"""
VentureMind AI — Phase 3A
Pydantic schemas for Startup Validation Engine request and response.

All scoring is transparent and documented. AI-generated assessments are
clearly labelled as estimates. No market statistics are presented as facts.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ---------------------------------------------------------------------------
# REQUEST SCHEMA
# ---------------------------------------------------------------------------

class ValidationRequest(BaseModel):
    """
    Input payload for the Startup Validation Engine.
    All fields except startup_name are optional; missing inputs reduce
    confidence and are explicitly reported in the analysis response.
    """
    startup_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the startup or project",
        example="VentureMind AI"
    )
    problem_statement: Optional[str] = Field(
        None,
        max_length=3000,
        description="The specific problem the startup solves and why current solutions are inadequate",
        example="Early-stage founders lack structured AI tools for startup validation and financial modeling."
    )
    proposed_solution: Optional[str] = Field(
        None,
        max_length=3000,
        description="Description of the solution and how it addresses the problem",
        example="An autonomous AI co-founder platform with validation, simulation, and competitor analysis."
    )
    target_customers: Optional[str] = Field(
        None,
        max_length=2000,
        description="Description of ideal customer profile (ICP) and target market segment",
        example="Seed and early Series A founders, solo entrepreneurs, and early product teams."
    )
    unique_value_proposition: Optional[str] = Field(
        None,
        max_length=2000,
        description="What makes this startup distinctly better or different from alternatives",
        example="7 specialized AI agents working as your full-time co-founder squad at 1% of the cost."
    )
    business_model: Optional[str] = Field(
        None,
        max_length=2000,
        description="Revenue model, pricing strategy, and monetization approach",
        example="Subscription SaaS: Starter $49/mo, Growth $149/mo, Enterprise $299/mo."
    )
    budget_resources: Optional[str] = Field(
        None,
        max_length=1000,
        description="Available funding, team size, and key resources",
        example="Bootstrap: $50,000 savings, solo technical founder, 6-month runway."
    )
    geography_market: Optional[str] = Field(
        None,
        max_length=500,
        description="Target geography and intended market scope",
        example="Initially US and Canada, expanding to Western Europe in Year 2."
    )
    startup_stage: Optional[str] = Field(
        None,
        max_length=200,
        description="Current stage of the startup",
        example="Pre-product, idea validation phase."
    )
    known_competitors: Optional[str] = Field(
        None,
        max_length=2000,
        description="Known direct and indirect competitors, if any",
        example="Lean Canvas, Business Model Canvas, early-stage VC analysts."
    )
    additional_context: Optional[str] = Field(
        None,
        max_length=3000,
        description="Any other relevant context the founder wants to share",
        example="Planning to launch an MVP in 30 days via a closed beta waitlist."
    )
    # Optional: link to existing startup DB record
    startup_id: Optional[int] = Field(
        None,
        description="Optional ID of an existing startup record to associate this report with"
    )

    @field_validator("startup_name")
    @classmethod
    def validate_startup_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Startup name cannot be empty.")
        return v

    @field_validator(
        "problem_statement", "proposed_solution", "target_customers",
        "unique_value_proposition", "business_model", "budget_resources",
        "geography_market", "startup_stage", "known_competitors", "additional_context",
        mode="before"
    )
    @classmethod
    def strip_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


# ---------------------------------------------------------------------------
# STAGE 2 SYNTHESIS SCHEMAS (AI Co-Founder Extraction & Follow-ups)
# ---------------------------------------------------------------------------

class SynthesisRequest(BaseModel):
    """Input payload for Stage 2 AI synthesis from a raw idea description."""
    idea_description: str = Field(
        ...,
        min_length=5,
        max_length=5000,
        description="Natural language description of the startup concept",
        example="An AI-powered co-founder platform that helps solo founders model SaaS unit economics and validate startup ideas."
    )
    startup_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional startup name if provided by user",
        example="VentureMind AI"
    )

    @field_validator("idea_description")
    @classmethod
    def validate_idea(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Idea description must be at least 5 characters.")
        return v

    @field_validator("startup_name", mode="before")
    @classmethod
    def strip_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        return s if s else None


class SynthesisFollowUpQuestion(BaseModel):
    """A single high-impact follow-up question for Stage 2."""
    question: str = Field(..., description="The follow-up question text")
    field_key: str = Field(..., description="Target field: e.g. business_model, known_competitors, startup_stage")
    suggestion: Optional[str] = Field(None, description="Inferred or suggested answer")
    options: List[str] = Field(default_factory=list, description="Quick-select choice pills for the user")


class SynthesisResponse(BaseModel):
    """Extracted components and smart follow-up suggestions from Stage 2 AI synthesis."""
    startup_name: str = Field(..., description="Suggested or confirmed startup name")
    problem_statement: str = Field(..., description="Inferred core problem statement")
    proposed_solution: str = Field(..., description="Inferred proposed solution")
    target_customers: str = Field(..., description="Inferred ideal customer profile (ICP)")
    unique_value_proposition: str = Field(..., description="Inferred unique value proposition")
    business_model: str = Field(..., description="Inferred monetization / revenue model")
    geography_market: str = Field(..., description="Inferred primary market sector or geography")
    follow_up_questions: List[SynthesisFollowUpQuestion] = Field(
        default_factory=list,
        description="At most 2-3 high-impact clarifying questions"
    )



# ---------------------------------------------------------------------------
# RESPONSE SCHEMAS — Structured Analysis Components
# ---------------------------------------------------------------------------

class ScoringDimension(BaseModel):
    """A single scoring dimension with its score, weight, and rationale."""
    name: str = Field(..., description="Name of the scoring dimension")
    score: float = Field(..., ge=0, le=20, description="Raw score for this dimension (0–20)")
    weight: float = Field(..., description="Weight of this dimension in final score (sum to 1.0)")
    weighted_score: float = Field(..., description="score × weight × 100, contribution to final score")
    rationale: str = Field(..., description="Explanation of why this score was assigned")
    confidence: str = Field(..., description="Confidence level: HIGH, MEDIUM, or LOW")
    missing_inputs: List[str] = Field(default_factory=list, description="Inputs that would improve this score")


class ScoreBreakdown(BaseModel):
    """
    Transparent scoring breakdown. Final score is the sum of weighted_score
    across all five dimensions. Maximum possible = 100.

    Dimensions and weights:
    - Problem Clarity        (20%): How well-defined is the problem being solved?
    - Target Customer        (20%): How specific and reachable is the target customer?
    - Value Proposition      (25%): How differentiated and compelling is the solution?
    - Business Model         (20%): How viable and defensible is the revenue model?
    - Execution Feasibility  (15%): How realistic is the execution plan given resources?
    """
    dimensions: List[ScoringDimension]
    total_score: float = Field(..., ge=0, le=100, description="Aggregate validation score (0–100)")
    score_label: str = Field(..., description="Human-readable label: e.g. 'Promising', 'Needs Work'")
    scoring_disclaimer: str = Field(
        default=(
            "⚠️ This score is an AI-generated estimate based solely on the information "
            "provided. It does not constitute market research, financial advice, or a "
            "guarantee of startup success. Scores may improve as more information is supplied."
        ),
        description="Mandatory disclaimer about score limitations"
    )


class ValidationAnalysis(BaseModel):
    """Full structured validation analysis returned by the AI engine."""

    # Core identification
    startup_name: str
    analysis_timestamp: str  # ISO format

    # Executive overview
    executive_summary: str = Field(..., description="2–3 paragraph AI-generated summary of the startup concept and validation outlook")

    # Section analyses
    problem_clarity: str = Field(..., description="Assessment of how clearly the problem is defined and validated")
    target_customer_analysis: str = Field(..., description="Evaluation of customer specificity, reachability, and urgency")
    value_proposition_assessment: str = Field(..., description="Analysis of uniqueness, differentiation, and buyer motivation")
    business_model_feasibility: str = Field(..., description="Assessment of revenue model viability and unit economics assumptions")
    market_assumptions: str = Field(..., description="Evaluation of stated market size and demand assumptions — labelled as estimates")
    technical_operational_feasibility: str = Field(..., description="Assessment of execution realism given stated resources and timeline")

    # Risk and opportunity
    key_risks: List[str] = Field(..., description="Top 5–8 identified risks and dependencies")
    strengths: List[str] = Field(..., description="Notable strengths and competitive advantages observed")
    weaknesses: List[str] = Field(..., description="Notable weaknesses and gaps requiring attention")

    # Actionable outputs
    recommended_next_steps: List[str] = Field(..., description="Prioritized concrete actions the founder should take next")
    customer_discovery_questions: List[str] = Field(..., description="Questions to ask potential customers during discovery interviews")
    low_cost_validation_experiments: List[str] = Field(..., description="Specific low-cost experiments to test key assumptions")
    metrics_to_measure: List[str] = Field(..., description="Key metrics and signals to track during experiments")

    # Information quality
    missing_information: List[str] = Field(..., description="Important inputs that were not provided and would improve analysis quality")
    uncertain_assumptions: List[str] = Field(..., description="Assumptions the AI made due to missing context")

    # Transparency markers
    evidence_notes: str = Field(
        ...,
        description="Explicit statement of what data was used: user-provided inputs only. No external sources consulted."
    )
    ai_disclaimer: str = Field(
        default=(
            "This analysis was generated by VentureMind AI (Groq LPU) based solely on "
            "user-provided inputs. All assessments are AI-generated estimates and opinions. "
            "They do not represent verified market research, legal advice, or financial projections. "
            "Founders should conduct independent customer research and validate assumptions before committing resources."
        )
    )

    # Score
    score_breakdown: ScoreBreakdown


# ---------------------------------------------------------------------------
# DATABASE RESPONSE SCHEMA (returned after saving to MySQL)
# ---------------------------------------------------------------------------

class ValidationReportResponse(BaseModel):
    """API response schema for a persisted validation report."""
    id: int
    startup_id: Optional[int] = None
    report_type: str
    status: str
    score: Optional[float] = None
    input_summary: Optional[str] = None
    model_used: Optional[str] = None
    created_at: datetime
    analysis: Optional[ValidationAnalysis] = None

    model_config = ConfigDict(from_attributes=True)


class ValidationReportListItem(BaseModel):
    """Lightweight report listing (without full analysis data)."""
    id: int
    startup_id: Optional[int] = None
    report_type: str
    status: str
    score: Optional[float] = None
    input_summary: Optional[str] = None
    model_used: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
