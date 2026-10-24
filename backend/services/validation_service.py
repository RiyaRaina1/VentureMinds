"""
VentureMind AI — Phase 3A
Startup Validation Service: AI prompt construction, Groq call, output parsing,
score calculation, and MySQL persistence.

Design principles:
- All AI output is validated by Pydantic before storage or display.
- Score is calculated deterministically from parsed AI output — not from raw LLM text.
- Missing inputs reduce confidence explicitly — never silently fabricated.
- No external data sources are consulted; all limitations are disclosed.
- API key never appears in logs, reports, or error messages.
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from backend.models.validation import ValidationReport
from backend.models.startup import Startup
from backend.schemas.validation import (
    ValidationRequest,
    ValidationAnalysis,
    ScoreBreakdown,
    ScoringDimension,
    ValidationReportResponse,
    ValidationReportListItem,
    SynthesisRequest,
    SynthesisResponse,
    SynthesisFollowUpQuestion,
)
from backend.services.ai_service import (
    AIConfigError,
    AIAuthError,
    AIRateLimitError,
    AIConnectionError,
    AIAPIError,
    AIError,
    get_groq_api_key,
    get_default_model,
)

# ---------------------------------------------------------------------------
# SCORING METHODOLOGY (documented, deterministic)
# ---------------------------------------------------------------------------
# Five dimensions, each 0–20 raw score. Weighted contribution to final 0–100 score:
#
#   Dimension                  Weight   Max contribution
#   Problem Clarity             0.20    20 pts
#   Target Customer Definition  0.20    20 pts
#   Value Proposition           0.25    25 pts
#   Business Model Feasibility  0.20    20 pts
#   Execution Feasibility       0.15    15 pts
#                                        --------
#   Total maximum score                 100 pts
#
# Each raw dimension score (0–20) is assigned by the AI based on quality
# and specificity of the founder's inputs. The AI is instructed to:
# - Score 0 if the input is missing entirely for that dimension.
# - Score 1–5 for vague or placeholder inputs.
# - Score 6–10 for partial but incomplete inputs.
# - Score 11–16 for solid, specific, defensible inputs.
# - Score 17–20 for exceptionally clear, validated, well-reasoned inputs.
#
# The weighted_score = raw_score × weight × 100 / 20
# Final score = sum of all weighted_scores (max 100)
#
# Score labels:
#   0–30   : Critical Gaps — Needs significant rework
#   31–50  : Early Stage — Key assumptions unvalidated
#   51–65  : Developing — Promising but incomplete
#   66–80  : Promising — Strong foundation with gaps
#   81–90  : Strong — Well-reasoned concept
#   91–100 : Exceptional — Highly refined concept

SCORING_DIMENSIONS = [
    {"key": "problem_clarity",       "name": "Problem Clarity",              "weight": 0.20},
    {"key": "target_customer",       "name": "Target Customer Definition",   "weight": 0.20},
    {"key": "value_proposition",     "name": "Value Proposition Strength",   "weight": 0.25},
    {"key": "business_model",        "name": "Business Model Feasibility",   "weight": 0.20},
    {"key": "execution_feasibility", "name": "Execution Feasibility",        "weight": 0.15},
]

SCORE_LABELS = [
    (91, "Exceptional"),
    (81, "Strong"),
    (66, "Promising"),
    (51, "Developing"),
    (31, "Early Stage"),
    (0,  "Critical Gaps"),
]


def _score_label(score: float) -> str:
    for threshold, label in SCORE_LABELS:
        if score >= threshold:
            return label
    return "Critical Gaps"


# ---------------------------------------------------------------------------
# PROMPT CONSTRUCTION
# ---------------------------------------------------------------------------

VALIDATION_SYSTEM_PROMPT = """You are VentureMind AI's Startup Validation Engine.

Your task: Analyze the startup information provided and return a STRICT JSON object following
the exact schema below. Do NOT include any text before or after the JSON object.

CRITICAL RULES:
1. Return ONLY valid JSON — no markdown, no code fences, no explanatory text outside the JSON.
2. All string values must be non-empty. Use "Not enough information provided." for fields
   where the founder gave no relevant input — never invent specifics.
3. For lists, provide 3–8 items minimum. If information is insufficient, state so plainly.
4. Scores must be integers 0–20 reflecting ONLY the quality and specificity of PROVIDED inputs.
5. NEVER fabricate market research, statistics, customer counts, or competitor capabilities.
6. Clearly label all assessments as AI-generated estimates, not verified facts.
7. For confidence: use "HIGH" only when the founder gave rich specific inputs; "MEDIUM" for
   partial inputs; "LOW" for vague or missing inputs.

JSON SCHEMA TO FOLLOW EXACTLY:
{
  "executive_summary": "<2-3 paragraph summary>",
  "problem_clarity": "<assessment of problem statement clarity>",
  "target_customer_analysis": "<assessment of customer specificity>",
  "value_proposition_assessment": "<assessment of differentiation>",
  "business_model_feasibility": "<assessment of revenue model>",
  "market_assumptions": "<assessment of market assumptions — label as estimates>",
  "technical_operational_feasibility": "<assessment of execution realism>",
  "key_risks": ["<risk 1>", "<risk 2>", "..."],
  "strengths": ["<strength 1>", "<strength 2>", "..."],
  "weaknesses": ["<weakness 1>", "<weakness 2>", "..."],
  "recommended_next_steps": ["<step 1>", "<step 2>", "..."],
  "customer_discovery_questions": ["<question 1>", "<question 2>", "..."],
  "low_cost_validation_experiments": ["<experiment 1>", "<experiment 2>", "..."],
  "metrics_to_measure": ["<metric 1>", "<metric 2>", "..."],
  "missing_information": ["<missing input 1>", "..."],
  "uncertain_assumptions": ["<assumption 1>", "..."],
  "evidence_notes": "<explicit statement that only user-provided inputs were used>",
  "dimension_scores": {
    "problem_clarity": {"score": <0-20>, "rationale": "<why>", "confidence": "<HIGH|MEDIUM|LOW>", "missing_inputs": ["..."]},
    "target_customer": {"score": <0-20>, "rationale": "<why>", "confidence": "<HIGH|MEDIUM|LOW>", "missing_inputs": ["..."]},
    "value_proposition": {"score": <0-20>, "rationale": "<why>", "confidence": "<HIGH|MEDIUM|LOW>", "missing_inputs": ["..."]},
    "business_model": {"score": <0-20>, "rationale": "<why>", "confidence": "<HIGH|MEDIUM|LOW>", "missing_inputs": ["..."]},
    "execution_feasibility": {"score": <0-20>, "rationale": "<why>", "confidence": "<HIGH|MEDIUM|LOW>", "missing_inputs": ["..."]}
  }
}"""


SYNTHESIS_SYSTEM_PROMPT = """You are VentureMind AI's Co-Founder Synthesis Engine.

Your task: Given a founder's raw natural-language idea description, extract and structure the key business components and generate at most 2-3 high-impact clarifying follow-up questions.

Return ONLY a strict JSON object matching this schema:
{
  "startup_name": "<Suggest a crisp, professional startup name if not provided, or use the provided name>",
  "problem_statement": "<1-2 concise sentences summarizing the core customer problem>",
  "proposed_solution": "<1-2 concise sentences describing the solution>",
  "target_customers": "<Specific ideal customer profile (ICP)>",
  "unique_value_proposition": "<The primary differentiator and value driver>",
  "business_model": "<Suggested monetization/revenue model (e.g. B2B SaaS $49-$199/mo, Marketplace Take-Rate, Freemium, etc.)>",
  "geography_market": "<Inferred target market sector / geography>",
  "follow_up_questions": [
    {
      "question": "<High-impact clarifying question, e.g. regarding pricing, competitors, or target customer focus>",
      "field_key": "<business_model | known_competitors | startup_stage | target_customers>",
      "suggestion": "<Helpful AI suggestion or recommended default>",
      "options": ["<Option 1>", "<Option 2>", "<Option 3>"]
    }
  ]
}

CRITICAL RULES:
1. Return ONLY valid JSON -- no markdown fences, no explanatory text.
2. Provide at most 3 targeted follow-up questions.
3. If an aspect cannot be reasonably inferred, provide a sensible default hypothesis and ask about it in follow_up_questions.
"""


def _build_user_message(req: ValidationRequest) -> str:
    """Format user inputs into a structured analysis request message."""
    lines = [f"STARTUP NAME: {req.startup_name}"]
    
    fields = [
        ("PROBLEM STATEMENT",       req.problem_statement),
        ("PROPOSED SOLUTION",       req.proposed_solution),
        ("TARGET CUSTOMERS / ICP",  req.target_customers),
        ("UNIQUE VALUE PROPOSITION", req.unique_value_proposition),
        ("BUSINESS MODEL & PRICING", req.business_model),
        ("BUDGET & RESOURCES",      req.budget_resources),
        ("GEOGRAPHY & MARKET",      req.geography_market),
        ("STARTUP STAGE",           req.startup_stage),
        ("KNOWN COMPETITORS",       req.known_competitors),
        ("ADDITIONAL CONTEXT",      req.additional_context),
    ]
    
    for label, value in fields:
        if value:
            lines.append(f"\n{label}:\n{value}")
        else:
            lines.append(f"\n{label}:\n[Not provided — mark as missing input in your analysis]")
    
    lines.append(
        "\n\nPlease analyze the above and return the strict JSON validation report. "
        "Remember: return ONLY the JSON object, no other text."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# GROQ API CALL (non-streaming, for structured JSON output)
# ---------------------------------------------------------------------------

async def _call_groq_json(
    system_prompt: str,
    user_message: str,
    model: str,
    timeout_seconds: float = 90.0,
) -> str:
    """
    Call Groq chat completions API (non-streaming) and return the raw response text.
    Uses a higher temperature=0.3 for more consistent JSON structure.
    Raises appropriate AIError subclasses on failure.
    """
    api_key = get_groq_api_key()
    if not api_key:
        raise AIConfigError(
            "Groq API key (GROQ_API_KEY) is not configured in backend/.env. "
            "Please set your GROQ_API_KEY to enable AI validation."
        )

    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "temperature": 0.3,
        "max_tokens": 6000,
    }

    timeout = httpx.Timeout(connect=15.0, read=timeout_seconds, write=15.0, pool=15.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(endpoint, headers=headers, json=payload)

            if response.status_code in (401, 403):
                raise AIAuthError("Invalid Groq API key. Check your GROQ_API_KEY configuration.")
            if response.status_code == 429:
                raise AIRateLimitError("Groq API rate limit exceeded. Please try again shortly.")
            if response.status_code >= 400:
                error_body = response.text[:300]
                raise AIAPIError(
                    f"Groq API returned status {response.status_code}.",
                    status_code=response.status_code
                )

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise AIAPIError("Groq returned an empty choices array.")
            
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                raise AIAPIError("Groq returned empty message content.")
            
            return content

    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as conn_err:
        raise AIConnectionError(f"Connection to Groq failed: {str(conn_err)}")
    except httpx.HTTPError as http_err:
        raise AIError(f"HTTP error communicating with Groq: {str(http_err)}")


# ---------------------------------------------------------------------------
# JSON EXTRACTION AND VALIDATION
# ---------------------------------------------------------------------------

def _extract_json_from_response(raw_text: str) -> dict:
    """
    Extract and parse JSON from the AI response.
    Handles cases where the model wraps JSON in markdown code fences.
    Raises ValueError if no valid JSON is found.
    """
    text = raw_text.strip()

    # Strip markdown fences if present (```json ... ``` or ``` ... ```)
    fence_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find the first { ... } block
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        candidate = text[brace_start:brace_end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError(
        "AI response did not contain parseable JSON. "
        "This may be a model or prompt issue. Please try again."
    )


def _validate_and_build_analysis(
    raw_dict: dict,
    req: ValidationRequest,
) -> ValidationAnalysis:
    """
    Validate the AI-parsed dictionary and build a fully validated
    ValidationAnalysis Pydantic model with a computed score breakdown.
    
    Raises ValueError if required fields are missing or malformed.
    """
    def _require(key: str, type_=str) -> object:
        val = raw_dict.get(key)
        if val is None:
            raise ValueError(f"AI response missing required field: '{key}'")
        if type_ == str and not isinstance(val, str):
            val = str(val)
        if type_ == list and not isinstance(val, list):
            raise ValueError(f"Expected list for field '{key}', got {type(val).__name__}")
        return val

    def _require_list(key: str) -> list:
        val = raw_dict.get(key)
        if not isinstance(val, list):
            if isinstance(val, str):
                return [val]
            return ["Not provided."]
        return [str(item) for item in val if item] or ["Not provided."]

    # --- Build score breakdown from AI-assigned dimension scores ---
    dim_scores_raw = raw_dict.get("dimension_scores", {})
    if not isinstance(dim_scores_raw, dict):
        dim_scores_raw = {}

    dimensions = []
    total_score = 0.0

    for dim_def in SCORING_DIMENSIONS:
        key = dim_def["key"]
        weight = dim_def["weight"]
        dim_data = dim_scores_raw.get(key, {})

        if not isinstance(dim_data, dict):
            dim_data = {}

        # Clamp score to valid range
        raw_score = float(dim_data.get("score", 0))
        raw_score = max(0.0, min(20.0, raw_score))

        weighted = round(raw_score * weight * (100.0 / 20.0), 2)
        total_score += weighted

        confidence = dim_data.get("confidence", "LOW")
        if confidence not in ("HIGH", "MEDIUM", "LOW"):
            confidence = "LOW"

        rationale = str(dim_data.get("rationale", "No rationale provided."))
        missing_inputs = dim_data.get("missing_inputs", [])
        if not isinstance(missing_inputs, list):
            missing_inputs = []

        dimensions.append(ScoringDimension(
            name=dim_def["name"],
            score=raw_score,
            weight=weight,
            weighted_score=weighted,
            rationale=rationale,
            confidence=confidence,
            missing_inputs=[str(m) for m in missing_inputs],
        ))

    total_score = round(total_score, 1)
    score_label = _score_label(total_score)

    score_breakdown = ScoreBreakdown(
        dimensions=dimensions,
        total_score=total_score,
        score_label=score_label,
    )

    # --- Build the full analysis object ---
    now_iso = datetime.now(timezone.utc).isoformat()

    analysis = ValidationAnalysis(
        startup_name=req.startup_name,
        analysis_timestamp=now_iso,
        executive_summary=_require("executive_summary"),
        problem_clarity=_require("problem_clarity"),
        target_customer_analysis=_require("target_customer_analysis"),
        value_proposition_assessment=_require("value_proposition_assessment"),
        business_model_feasibility=_require("business_model_feasibility"),
        market_assumptions=_require("market_assumptions"),
        technical_operational_feasibility=_require("technical_operational_feasibility"),
        key_risks=_require_list("key_risks"),
        strengths=_require_list("strengths"),
        weaknesses=_require_list("weaknesses"),
        recommended_next_steps=_require_list("recommended_next_steps"),
        customer_discovery_questions=_require_list("customer_discovery_questions"),
        low_cost_validation_experiments=_require_list("low_cost_validation_experiments"),
        metrics_to_measure=_require_list("metrics_to_measure"),
        missing_information=_require_list("missing_information"),
        uncertain_assumptions=_require_list("uncertain_assumptions"),
        evidence_notes=str(raw_dict.get(
            "evidence_notes",
            "Analysis based solely on user-provided inputs. No external data sources consulted."
        )),
        score_breakdown=score_breakdown,
    )
    return analysis


# ---------------------------------------------------------------------------
# MAIN SERVICE FUNCTION
# ---------------------------------------------------------------------------

async def run_validation_analysis(
    req: ValidationRequest,
    db: Session,
) -> Tuple[ValidationAnalysis, ValidationReport]:
    """
    Orchestrate the full startup validation pipeline:
    1. Build and send structured prompt to Groq.
    2. Parse and validate the AI response.
    3. Calculate score deterministically.
    4. Persist the report to MySQL.
    5. Return the validated analysis and the DB record.
    
    Raises AIError subclasses on AI provider failures.
    Raises ValueError on malformed AI output.
    """
    model = get_default_model()
    user_message = _build_user_message(req)

    # Step 1: Call Groq
    raw_response = await _call_groq_json(
        system_prompt=VALIDATION_SYSTEM_PROMPT,
        user_message=user_message,
        model=model,
    )

    # Step 2: Extract JSON
    raw_dict = _extract_json_from_response(raw_response)

    # Step 3: Validate and build analysis with computed score
    analysis = _validate_and_build_analysis(raw_dict, req)

    # Step 4: Build input summary for display (first 500 chars, no sensitive info)
    input_parts = [req.startup_name]
    if req.problem_statement:
        input_parts.append(req.problem_statement[:100])
    input_summary = " | ".join(input_parts)[:500]

    # Step 5: Persist to MySQL
    report_json = analysis.model_dump_json()
    db_report = ValidationReport(
        startup_id=req.startup_id,
        report_type="startup_validation",
        status="completed",
        score=analysis.score_breakdown.total_score,
        report_data=report_json,
        input_summary=input_summary,
        model_used=model,
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    return analysis, db_report


# ---------------------------------------------------------------------------
# RETRIEVAL SERVICE FUNCTIONS
# ---------------------------------------------------------------------------

def get_validation_report(db: Session, report_id: int) -> Optional[ValidationReport]:
    """Retrieve a single validation report by ID."""
    return db.query(ValidationReport).filter(ValidationReport.id == report_id).first()


def get_validation_reports(
    db: Session,
    startup_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
) -> list:
    """
    Retrieve validation reports with optional startup filter and pagination.
    Returns most recent reports first.
    """
    query = db.query(ValidationReport).order_by(ValidationReport.created_at.desc())
    if startup_id is not None:
        query = query.filter(ValidationReport.startup_id == startup_id)
    return query.offset(skip).limit(limit).all()


def delete_validation_report(db: Session, report_id: int) -> bool:
    """Delete a validation report by ID. Returns True if found and deleted."""
    report = get_validation_report(db, report_id)
    if not report:
        return False
    db.delete(report)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# STAGE 2 SYNTHESIS SERVICE FUNCTION
# ---------------------------------------------------------------------------

async def synthesize_startup_idea(req: SynthesisRequest) -> SynthesisResponse:
    """
    Fast Stage 2 AI synthesis:
    Extracts structured components (problem, solution, ICP, UVP, business model)
    from a natural language idea description and produces 2-3 high-impact follow-up questions.
    """
    model = get_default_model()
    user_prompt = f"FOUNDER IDEA DESCRIPTION:\n{req.idea_description}\n"
    if req.startup_name:
        user_prompt += f"\nFOUNDER SPECIFIED NAME:\n{req.startup_name}\n"

    raw_response = await _call_groq_json(
        system_prompt=SYNTHESIS_SYSTEM_PROMPT,
        user_message=user_prompt,
        model=model,
        timeout_seconds=45.0,
    )

    raw_dict = _extract_json_from_response(raw_response)

    name = req.startup_name or str(raw_dict.get("startup_name") or "My Startup Concept").strip()
    problem = str(raw_dict.get("problem_statement") or "Problem identified from idea description.").strip()
    solution = str(raw_dict.get("proposed_solution") or req.idea_description[:300]).strip()
    audience = str(raw_dict.get("target_customers") or "Target users and early adopters").strip()
    uvp = str(raw_dict.get("unique_value_proposition") or solution).strip()
    biz_model = str(raw_dict.get("business_model") or "Subscription SaaS ($29-$99/mo)").strip()
    market = str(raw_dict.get("geography_market") or "Global / Online").strip()

    questions_raw = raw_dict.get("follow_up_questions", [])
    questions = []
    if isinstance(questions_raw, list):
        for q in questions_raw[:3]:
            if isinstance(q, dict) and "question" in q and "field_key" in q:
                options = q.get("options", [])
                if not isinstance(options, list):
                    options = []
                questions.append(SynthesisFollowUpQuestion(
                    question=str(q["question"]),
                    field_key=str(q["field_key"]),
                    suggestion=str(q.get("suggestion") or "") if q.get("suggestion") else None,
                    options=[str(opt) for opt in options][:4],
                ))

    return SynthesisResponse(
        startup_name=name,
        problem_statement=problem,
        proposed_solution=solution,
        target_customers=audience,
        unique_value_proposition=uvp,
        business_model=biz_model,
        geography_market=market,
        follow_up_questions=questions,
    )

