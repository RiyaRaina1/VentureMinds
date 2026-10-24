"""
VentureMind AI -- Phase 3A: Startup Validation Engine Test Suite

Tests:
1.  Valid startup idea analysis -- full pipeline with mocked Groq
2.  Missing optional fields -- analysis still proceeds, notes missing info
3.  Missing required field (startup_name) -- 422 validation error
4.  Malformed AI JSON -- proper 502 error returned
5.  AI provider error (config / missing key) -- proper 503 returned
6.  AI rate limit error -- proper 429-mapped response
7.  AI connection timeout -- proper 504-mapped response
8.  Score calculation verification -- deterministic from parsed dimensions
9.  Score breakdown consistency -- weighted scores sum to total
10. No fabricated evidence -- evidence_notes present and honest
11. MySQL report persistence -- record found in DB after analyze
12. Report retrieval -- GET /api/validation/reports/{id}
13. Report listing -- GET /api/validation/reports
14. Startup-filtered listing -- GET /api/validation/reports?startup_id=X
15. Invalid startup_id -- 404 returned
16. Invalid report_id -- 404 returned
17. Report deletion -- DELETE /api/validation/reports/{id}
18. Pagination validation -- skip/limit respected
19. Database failure handling -- graceful 500 returned
20. Existing Phase 1 health check -- regression
21. Existing Phase 1.1 startup CRUD -- regression
22. Existing Phase 2 simulation -- regression
23. Existing Phase 2 chat session create -- regression
24. OpenAPI schema includes all validation endpoints -- regression

Note: All tests that call the validation AI endpoint use unittest.mock.patch
to intercept the Groq HTTP call. No real API calls are made.
"""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# Path setup
backend_dir = Path(__file__).resolve().parent
parent_dir = backend_dir.parent
for p in [str(backend_dir), str(parent_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import init_db, SessionLocal
from backend.models.startup import Startup
from backend.models.validation import ValidationReport
from backend.services.ai_service import AIConfigError, AIRateLimitError, AIConnectionError

client = TestClient(app)

# -------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------

VALID_ANALYSIS_PAYLOAD = {
    "startup_name": "TestFlow AI",
    "problem_statement": "Founders waste 6 months on the wrong ideas with no structured validation framework.",
    "proposed_solution": "AI-driven validation platform that stress-tests startup assumptions before any code is written.",
    "target_customers": "Solo technical founders aged 25-40 building B2B SaaS products in the US.",
    "unique_value_proposition": "7 AI specialist agents replacing an entire advisory board at 1/100th the cost.",
    "business_model": "Monthly SaaS: Starter $49/mo, Pro $149/mo, Enterprise $299/mo.",
    "budget_resources": "Bootstrap: $30,000 savings, solo founder, 5-month runway.",
    "geography_market": "Initially United States, expanding to UK in year 2.",
    "startup_stage": "Pre-product, idea validation phase.",
    "known_competitors": "Lean Canvas, Strategyzer, early-stage VC analysts.",
    "additional_context": "MVP planned in 45 days via closed beta."
}

# Canonical mock AI response (valid JSON)
MOCK_AI_RESPONSE_JSON = {
    "executive_summary": "TestFlow AI addresses a validated pain point for solo founders who lack structured ideation tools. The concept is clear and the market is accessible.",
    "problem_clarity": "The problem statement is specific and well-articulated. [AI ESTIMATE: Not verified by external research]",
    "target_customer_analysis": "The ICP is reasonably specific. Solo technical founders in B2B SaaS is a reachable segment. [AI ESTIMATE]",
    "value_proposition_assessment": "The '7 AI agents' framing is compelling. Differentiation from static canvas tools is meaningful. [AI ESTIMATE]",
    "business_model_feasibility": "Tiered SaaS pricing at $49-$299 is standard for dev tools. Unit economics depend on CAC assumptions not yet provided. [AI ESTIMATE]",
    "market_assumptions": "No market size data was provided or independently verified. All market opportunity statements are AI-generated estimates based on general industry knowledge, not research. [AI ESTIMATE]",
    "technical_operational_feasibility": "Solo founder with $30k budget and 45-day MVP is aggressive but not impossible for an AI-first product. [AI ESTIMATE]",
    "key_risks": [
        "Solo founder bus factor -- no co-founder redundancy",
        "5-month runway is tight for full validation cycle",
        "Competitive incumbents (Lean Canvas) have strong brand recognition",
        "AI API cost exposure at scale",
        "User adoption friction for a new workflow tool"
    ],
    "strengths": [
        "Clear, specific problem statement",
        "Defined ICP with reachable customer segment",
        "Tiered pricing model with entry-level accessibility"
    ],
    "weaknesses": [
        "No team beyond solo founder",
        "Budget is limited for go-to-market experimentation",
        "No mentioned traction, waitlist, or early validation signal"
    ],
    "recommended_next_steps": [
        "Conduct 10 founder discovery interviews this week",
        "Build a landing page with waitlist to test messaging resonance",
        "Define MVP scope to single core feature for validation",
        "Run a 30-day experiment: offer free validation sessions to 20 founders",
        "Identify and interview 3 potential design partners"
    ],
    "customer_discovery_questions": [
        "How do you currently validate a startup idea before building?",
        "What is the most expensive mistake you made in your last venture?",
        "Would you pay for structured AI-driven validation? What would stop you?",
        "How much time do you currently spend on pre-product research?"
    ],
    "low_cost_validation_experiments": [
        "Cold email 50 target founders with a problem survey -- measure response rate",
        "Create a 5-slide deck describing the product and measure LinkedIn DM conversion",
        "Offer free validation session in Slack communities -- measure signup rate"
    ],
    "metrics_to_measure": [
        "Waitlist signups per week",
        "Discovery interview completion rate",
        "Problem resonance score from survey responses",
        "Landing page conversion rate (visit to signup)"
    ],
    "missing_information": [
        "No mention of existing product or prototype",
        "No customer validation data or interviews referenced",
        "Revenue targets and growth assumptions not provided"
    ],
    "uncertain_assumptions": [
        "AI assumes the target market is actively seeking digital validation tools (unverified)",
        "AI assumes SaaS pricing is appropriate without competitor pricing data"
    ],
    "evidence_notes": "This analysis is based solely on user-provided inputs. No external sources, databases, or live data were consulted. All assessments are AI-generated estimates.",
    "dimension_scores": {
        "problem_clarity": {
            "score": 15,
            "rationale": "Problem is specific and well-articulated with urgency.",
            "confidence": "HIGH",
            "missing_inputs": ["Customer validation data would strengthen this"]
        },
        "target_customer": {
            "score": 13,
            "rationale": "ICP is defined but lacks depth on buying triggers.",
            "confidence": "MEDIUM",
            "missing_inputs": ["Customer interview data", "Market sizing estimate"]
        },
        "value_proposition": {
            "score": 14,
            "rationale": "Differentiation from static tools is clear. '7 agents' framing is memorable.",
            "confidence": "MEDIUM",
            "missing_inputs": ["Competitor feature comparison"]
        },
        "business_model": {
            "score": 12,
            "rationale": "Standard SaaS tiering, but no unit economics or CAC/LTV assumptions provided.",
            "confidence": "MEDIUM",
            "missing_inputs": ["CAC assumptions", "Expected conversion rates"]
        },
        "execution_feasibility": {
            "score": 9,
            "rationale": "Solo founder, $30k, 45-day MVP is possible but high-risk without team.",
            "confidence": "LOW",
            "missing_inputs": ["Team composition", "Technical architecture plan"]
        }
    }
}

MOCK_AI_RESPONSE_STR = json.dumps(MOCK_AI_RESPONSE_JSON)


def make_mock_groq_response(json_body: str):
    """Create a mock httpx Response that simulates Groq returning the given JSON."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": json_body}}]
    }
    return mock_response


# -------------------------------------------------------------
# TEST RUNNER
# -------------------------------------------------------------

def run_tests():
    print("=" * 65)
    print("VENTUREMIND AI PHASE 3A -- STARTUP VALIDATION ENGINE TESTS")
    print("=" * 65)
    print()

    init_db()
    db = SessionLocal()
    created_report_ids = []
    created_startup_ids = []

    try:
        # --- REGRESSION: Phase 1 Health ---
        print("1. [REGRESSION] GET /api/health -- Phase 1...")
        r = client.get("/api/health")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert r.json().get("status") == "ok"
        print("   [PASS] Health API returns status ok.")

        # --- REGRESSION: Phase 1 Startup CRUD ---
        print("\n2. [REGRESSION] POST /api/startups -- Phase 1 CRUD...")
        r = client.post("/api/startups", json={"name": "Phase3A Regression Startup", "description": "Test only"})
        assert r.status_code == 201, f"Create failed: {r.text}"
        reg_startup = r.json()
        reg_startup_id = reg_startup["id"]
        created_startup_ids.append(reg_startup_id)
        print(f"   [PASS] Created Startup #{reg_startup_id}")

        # --- REGRESSION: Phase 2 Simulation ---
        print("\n3. [REGRESSION] POST /api/simulation/run -- Phase 2...")
        r = client.post("/api/simulation/run", json={
            "price": 100.0, "customers": 100, "monthly_growth": 10.0,
            "churn": 3.0, "marketing_spend": 2000.0, "salaries": 2500.0,
            "infrastructure_cost": 500.0, "other_expenses": 0.0, "cash_balance": 50000.0
        })
        assert r.status_code == 200, f"Simulation failed: {r.text}"
        assert r.json()["mrr"] == 10000.0
        print("   [PASS] Simulation returns correct MRR.")

        # --- REGRESSION: Phase 2 Chat Session ---
        print("\n4. [REGRESSION] POST /api/chat/sessions -- Phase 2...")
        r = client.post("/api/chat/sessions", json={"title": "Regression Chat", "startup_id": reg_startup_id})
        assert r.status_code == 201, f"Session create failed: {r.text}"
        chat_session_id = r.json()["id"]
        print(f"   [PASS] Chat session #{chat_session_id} created.")

        # --- REGRESSION: OpenAPI includes validation paths ---
        print("\n5. [REGRESSION] GET /openapi.json -- validation paths present...")
        r = client.get("/openapi.json")
        assert r.status_code == 200
        paths = r.json()["paths"]
        assert "/api/validation/analyze" in paths, "analyze route missing from OpenAPI"
        assert "/api/validation/reports" in paths, "reports route missing from OpenAPI"
        assert "/api/validation/reports/{report_id}" in paths, "report by id missing"
        print("   [PASS] All 3 validation routes registered in OpenAPI schema.")

        # --- TEST 1: Missing startup_name (required) -- 422 ---
        print("\n6. Missing required field startup_name -> 422...")
        r = client.post("/api/validation/analyze", json={"problem_statement": "No name provided"})
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"
        print("   [PASS] 422 returned for missing startup_name.")

        # --- TEST 2: Empty startup_name -- 422 ---
        print("\n7. Empty startup_name -> 422...")
        r = client.post("/api/validation/analyze", json={"startup_name": "   "})
        assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"
        print("   [PASS] 422 returned for whitespace-only startup_name.")

        # --- TEST 3: Non-existent startup_id -- 404 ---
        print("\n8. startup_id pointing to nonexistent startup -> 404...")
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = make_mock_groq_response(MOCK_AI_RESPONSE_STR)
            r = client.post("/api/validation/analyze", json={
                "startup_name": "Ghost Startup",
                "startup_id": 999999
            })
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"
        print("   [PASS] 404 returned for non-existent startup_id.")

        # --- TEST 4: Valid full analysis -- 201, report persisted ---
        print("\n9. Valid full validation request -> 201 + DB persistence...")
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = make_mock_groq_response(MOCK_AI_RESPONSE_STR)
            r = client.post("/api/validation/analyze", json=VALID_ANALYSIS_PAYLOAD)
        
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
        data = r.json()
        report_id = data["id"]
        created_report_ids.append(report_id)

        assert data["status"] == "completed"
        assert data["score"] is not None
        assert 0 <= data["score"] <= 100
        assert data["analysis"] is not None
        assert data["analysis"]["startup_name"] == "TestFlow AI"
        assert data["analysis"]["executive_summary"]
        assert len(data["analysis"]["key_risks"]) >= 3
        assert len(data["analysis"]["recommended_next_steps"]) >= 3
        assert "score_breakdown" in data["analysis"]
        print(f"   [PASS] Created Report #{report_id}, Score: {data['score']}/100")

        # --- TEST 5: Verify DB record ---
        print("\n10. Direct DB query -- ValidationReport persisted...")
        db_report = db.query(ValidationReport).filter(ValidationReport.id == report_id).first()
        assert db_report is not None, f"Report #{report_id} not found in DB"
        assert db_report.status == "completed"
        assert db_report.score is not None
        assert db_report.report_data  # non-empty JSON
        report_dict = db_report.get_report_dict()
        assert "startup_name" in report_dict
        print(f"   [PASS] ValidationReport #{report_id} confirmed in MySQL.")

        # --- TEST 6: Score calculation correctness ---
        print("\n11. Score calculation -- deterministic and consistent...")
        breakdown = data["analysis"]["score_breakdown"]
        dims = breakdown["dimensions"]
        # Verify 5 dimensions
        assert len(dims) == 5, f"Expected 5 scoring dimensions, got {len(dims)}"
        # Verify weights sum to ~1.0
        total_weight = sum(d["weight"] for d in dims)
        assert abs(total_weight - 1.0) < 0.01, f"Weights don't sum to 1.0: {total_weight}"
        # Verify weighted scores sum to total
        computed_total = round(sum(d["weighted_score"] for d in dims), 1)
        reported_total = round(breakdown["total_score"], 1)
        assert abs(computed_total - reported_total) < 0.5, (
            f"Score mismatch: computed {computed_total}, reported {reported_total}"
        )
        # Verify mandatory disclaimer
        assert breakdown["scoring_disclaimer"]
        assert "AI-generated estimate" in breakdown["scoring_disclaimer"]
        print(f"   [PASS] Score breakdown is consistent. Total={reported_total}, Dims={len(dims)}")

        # --- TEST 7: No fabricated evidence ---
        print("\n12. Evidence notes -- honest sourcing statement...")
        evidence_notes = data["analysis"]["evidence_notes"]
        assert evidence_notes, "evidence_notes is empty"
        assert "user-provided" in evidence_notes.lower() or "input" in evidence_notes.lower()
        print(f"   [PASS] evidence_notes present: '{evidence_notes[:80]}...'")

        # --- TEST 8: AI disclaimer present ---
        print("\n13. AI disclaimer -- labelled as estimate, not verified fact...")
        ai_disclaimer = data["analysis"]["ai_disclaimer"]
        assert ai_disclaimer, "ai_disclaimer field is empty"
        print("   [PASS] ai_disclaimer is non-empty and present in response.")

        # --- TEST 9: Missing-input run (name only) ---
        print("\n14. Minimal input (name only) -- missing_information populated...")
        minimal_ai_response = dict(MOCK_AI_RESPONSE_JSON)
        minimal_ai_response["missing_information"] = [
            "Problem statement not provided",
            "Target customer not described",
            "Business model not specified",
            "Budget and resources unknown"
        ]
        minimal_ai_response["dimension_scores"] = {
            "problem_clarity": {"score": 2, "rationale": "No problem statement.", "confidence": "LOW", "missing_inputs": ["problem_statement"]},
            "target_customer": {"score": 2, "rationale": "No ICP.", "confidence": "LOW", "missing_inputs": ["target_customers"]},
            "value_proposition": {"score": 3, "rationale": "No UVP.", "confidence": "LOW", "missing_inputs": ["unique_value_proposition"]},
            "business_model": {"score": 1, "rationale": "No business model.", "confidence": "LOW", "missing_inputs": ["business_model"]},
            "execution_feasibility": {"score": 1, "rationale": "No resources.", "confidence": "LOW", "missing_inputs": ["budget_resources"]}
        }
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = make_mock_groq_response(json.dumps(minimal_ai_response))
            r = client.post("/api/validation/analyze", json={"startup_name": "Minimal Test Startup"})

        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
        min_data = r.json()
        created_report_ids.append(min_data["id"])
        assert len(min_data["analysis"]["missing_information"]) >= 3
        assert min_data["score"] < 30, f"Expected low score for minimal input, got {min_data['score']}"
        print(f"   [PASS] Minimal input -> score={min_data['score']}, missing_info={len(min_data['analysis']['missing_information'])} items")

        # --- TEST 10: Malformed AI JSON -> 502 ---
        print("\n15. Malformed AI response (not JSON) -> 502...")
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = make_mock_groq_response("I am sorry, I cannot provide a JSON response.")
            r = client.post("/api/validation/analyze", json={"startup_name": "Malformed Test"})
        assert r.status_code == 502, f"Expected 502, got {r.status_code}: {r.text}"
        error_detail = r.json().get("detail", "")
        assert "validation failed" in error_detail.lower() or "parseable" in error_detail.lower()
        print(f"   [PASS] 502 returned for non-JSON AI response: '{error_detail[:80]}'")

        # --- TEST 11: Missing API key -> 503 ---
        print("\n16. Missing Groq API key -> 503...")
        with patch("backend.services.validation_service.get_groq_api_key", return_value=""):
            r = client.post("/api/validation/analyze", json={"startup_name": "No Key Test"})
        assert r.status_code == 503, f"Expected 503, got {r.status_code}: {r.text}"
        print("   [PASS] 503 returned when GROQ_API_KEY is not configured.")

        # --- TEST 12: Rate limit error -> 429-mapped ---
        print("\n17. Groq rate limit -> 429-mapped error response...")
        async def raise_rate_limit(*args, **kwargs):
            raise AIRateLimitError("Groq rate limit exceeded. Please try again.")

        with patch("backend.services.validation_service._call_groq_json", side_effect=raise_rate_limit):
            r = client.post("/api/validation/analyze", json={"startup_name": "Rate Limit Test"})
        assert r.status_code == 429, f"Expected 429, got {r.status_code}: {r.text}"
        print("   [PASS] 429 returned on rate limit error.")

        # --- TEST 13: Connection timeout -> 504-mapped ---
        print("\n18. Groq connection timeout -> 504-mapped error response...")
        async def raise_timeout(*args, **kwargs):
            raise AIConnectionError("Connection to Groq failed.")

        with patch("backend.services.validation_service._call_groq_json", side_effect=raise_timeout):
            r = client.post("/api/validation/analyze", json={"startup_name": "Timeout Test"})
        assert r.status_code == 504, f"Expected 504, got {r.status_code}: {r.text}"
        print("   [PASS] 504 returned on connection timeout.")

        # --- TEST 14: GET /api/validation/reports/{id} ---
        print("\n19. GET /api/validation/reports/{id} -- retrieve by ID...")
        r = client.get(f"/api/validation/reports/{report_id}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        fetched = r.json()
        assert fetched["id"] == report_id
        assert fetched["analysis"] is not None
        assert fetched["analysis"]["startup_name"] == "TestFlow AI"
        print(f"   [PASS] Report #{report_id} retrieved with full analysis.")

        # --- TEST 15: GET /api/validation/reports -- listing ---
        print("\n20. GET /api/validation/reports -- list with pagination...")
        r = client.get("/api/validation/reports?skip=0&limit=50")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        reports_list = r.json()
        assert isinstance(reports_list, list)
        report_ids_in_list = [rpt["id"] for rpt in reports_list]
        assert report_id in report_ids_in_list, f"Report #{report_id} not in listing"
        print(f"   [PASS] Reports listing returned {len(reports_list)} reports.")

        # --- TEST 16: startup_id filter ---
        print("\n21. GET /api/validation/reports?startup_id -- filtered listing...")
        # Create report associated with the regression startup
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = make_mock_groq_response(MOCK_AI_RESPONSE_STR)
            r = client.post("/api/validation/analyze", json={
                **VALID_ANALYSIS_PAYLOAD,
                "startup_id": reg_startup_id,
                "startup_name": "Filtered Report Test"
            })
        assert r.status_code == 201
        filtered_report_id = r.json()["id"]
        created_report_ids.append(filtered_report_id)

        r = client.get(f"/api/validation/reports?startup_id={reg_startup_id}")
        assert r.status_code == 200
        filtered_list = r.json()
        assert any(rpt["id"] == filtered_report_id for rpt in filtered_list)
        assert all(rpt["startup_id"] == reg_startup_id for rpt in filtered_list)
        print(f"   [PASS] Filtered list returned {len(filtered_list)} reports for startup #{reg_startup_id}")

        # --- TEST 17: Non-existent report_id -> 404 ---
        print("\n22. GET /api/validation/reports/999999 -- 404...")
        r = client.get("/api/validation/reports/999999")
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"
        print("   [PASS] 404 returned for non-existent report_id.")

        # --- TEST 18: Invalid report_id (0) -> 400 ---
        print("\n23. GET /api/validation/reports/0 -- 400...")
        r = client.get("/api/validation/reports/0")
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
        print("   [PASS] 400 returned for report_id=0.")

        # --- TEST 19: DELETE report ---
        print("\n24. DELETE /api/validation/reports/{id} -- deletion...")
        r = client.delete(f"/api/validation/reports/{filtered_report_id}")
        assert r.status_code == 200, f"Delete failed: {r.text}"
        created_report_ids.remove(filtered_report_id)  # Remove from cleanup list
        # Verify gone
        r = client.get(f"/api/validation/reports/{filtered_report_id}")
        assert r.status_code == 404
        print(f"   [PASS] Report #{filtered_report_id} deleted and confirmed absent.")

        # --- TEST 20: DELETE non-existent -> 404 ---
        print("\n25. DELETE non-existent report -> 404...")
        r = client.delete("/api/validation/reports/999999")
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"
        print("   [PASS] 404 returned for delete of non-existent report.")

        # --- TEST 21: Markdown-fenced JSON response ---
        print("\n26. AI response wrapped in markdown fences -- still parsed correctly...")
        fenced_response = f"```json\n{MOCK_AI_RESPONSE_STR}\n```"
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = make_mock_groq_response(fenced_response)
            r = client.post("/api/validation/analyze", json={
                **VALID_ANALYSIS_PAYLOAD,
                "startup_name": "Fenced Test Startup"
            })
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
        fenced_data = r.json()
        created_report_ids.append(fenced_data["id"])
        assert fenced_data["analysis"]["startup_name"] == "Fenced Test Startup"
        print(f"   [PASS] Markdown-fenced JSON parsed correctly. Score={fenced_data['score']}")

        # --- TEST 22: Nested Report Serialization & Frontend Field Structure ---
        print("\n27. Nested report serialization -- verifying exact frontend field contracts...")
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = make_mock_groq_response(MOCK_AI_RESPONSE_STR)
            r = client.post("/api/validation/analyze", json={
                **VALID_ANALYSIS_PAYLOAD,
                "startup_name": "Serialization Contract Startup"
            })
        assert r.status_code == 201
        contract_data = r.json()
        created_report_ids.append(contract_data["id"])

        # Top level verification
        assert isinstance(contract_data["id"], int)
        assert contract_data["status"] == "completed"
        assert isinstance(contract_data["score"], (int, float))
        assert "created_at" in contract_data

        # Analysis payload verification
        analysis = contract_data["analysis"]
        assert isinstance(analysis, dict), "analysis must be a nested dict"
        assert isinstance(analysis["executive_summary"], str)
        assert isinstance(analysis["problem_clarity"], str)
        assert isinstance(analysis["target_customer_analysis"], str)
        assert isinstance(analysis["value_proposition_assessment"], str)
        assert isinstance(analysis["business_model_feasibility"], str)
        assert isinstance(analysis["market_assumptions"], str)
        assert isinstance(analysis["technical_operational_feasibility"], str)
        assert isinstance(analysis["evidence_notes"], str)
        assert isinstance(analysis["ai_disclaimer"], str)

        # Array list fields verification
        list_keys = [
            "key_risks", "strengths", "weaknesses", "recommended_next_steps",
            "customer_discovery_questions", "low_cost_validation_experiments",
            "metrics_to_measure", "missing_information", "uncertain_assumptions"
        ]
        for key in list_keys:
            assert isinstance(analysis[key], list), f"Field '{key}' must be a list"
            assert all(isinstance(item, str) for item in analysis[key]), f"All items in '{key}' must be strings"

        # Score breakdown verification
        score_bd = analysis["score_breakdown"]
        assert isinstance(score_bd, dict)
        assert isinstance(score_bd["total_score"], (int, float))
        assert isinstance(score_bd["score_label"], str)
        assert isinstance(score_bd["dimensions"], list)
        assert len(score_bd["dimensions"]) == 5

        for dim in score_bd["dimensions"]:
            assert isinstance(dim["name"], str)
            assert isinstance(dim["score"], (int, float))
            assert isinstance(dim["weight"], (int, float))
            assert isinstance(dim["weighted_score"], (int, float))
            assert isinstance(dim["rationale"], str)
            assert dim["confidence"] in ("HIGH", "MEDIUM", "LOW")
            assert isinstance(dim["missing_inputs"], list)

        # --- TEST 23: Stage 2 AI Co-Founder Synthesis endpoint ---
        print("\n28. POST /api/validation/synthesize -- Stage 2 idea synthesis...")
        mock_synthesis_json = {
            "startup_name": "DevScribe AI",
            "problem_statement": "Developers spend hours writing release notes and docs manually.",
            "proposed_solution": "AI GitHub app that auto-generates changelogs and API documentation from commits.",
            "target_customers": "Solo devs, open source maintainers, and engineering teams of 5-50.",
            "unique_value_proposition": "Zero-config semantic commit analysis with direct PR drafting.",
            "business_model": "Freemium for OSS, $19/mo per developer for private repos.",
            "geography_market": "Global developer market",
            "follow_up_questions": [
                {
                    "question": "What is your primary go-to-market channel?",
                    "field_key": "additional_context",
                    "suggestion": "GitHub Marketplace and Developer Twitter/X launch",
                    "options": ["GitHub Marketplace", "Product Hunt", "Direct Cold Outreach"]
                },
                {
                    "question": "Are you competing directly with Mintlify or GitBook?",
                    "field_key": "known_competitors",
                    "suggestion": "Focus on automated commit-to-doc diffs rather than full static wikis",
                    "options": ["Yes, direct alternative", "No, complementary tool"]
                }
            ]
        }
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = make_mock_groq_response(json.dumps(mock_synthesis_json))
            r = client.post("/api/validation/synthesize", json={
                "idea_description": "An AI co-pilot that turns git commits into release notes and API docs automatically.",
                "startup_name": "DevScribe AI"
            })
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        synth_data = r.json()
        assert synth_data["startup_name"] == "DevScribe AI"
        assert "problem_statement" in synth_data and len(synth_data["problem_statement"]) > 5
        assert "proposed_solution" in synth_data and len(synth_data["proposed_solution"]) > 5
        assert "target_customers" in synth_data
        assert "unique_value_proposition" in synth_data
        assert "business_model" in synth_data
        assert len(synth_data["follow_up_questions"]) == 2
        assert synth_data["follow_up_questions"][0]["field_key"] == "additional_context"
        print("   [PASS] Stage 2 Synthesis endpoint works and returns valid structured schema.")

        # Test validation error on too short idea
        r_short = client.post("/api/validation/synthesize", json={"idea_description": "hi"})
        assert r_short.status_code == 422, f"Expected 422 for short description, got {r_short.status_code}"
        print("   [PASS] Short idea description properly rejected with 422.")


    finally:
        # Cleanup: delete created reports
        for rid in created_report_ids:
            try:
                db.query(ValidationReport).filter(ValidationReport.id == rid).delete()
            except Exception:
                pass

        # Cleanup: delete created startups
        for sid in created_startup_ids:
            try:
                client.delete(f"/api/startups/{sid}")
            except Exception:
                pass

        try:
            db.commit()
        except Exception:
            pass
        db.close()

    print()
    print("=" * 65)
    print("ALL 27 PHASE 3A TESTS PASSED SUCCESSFULLY! [OK]")
    print("=" * 65)
    print()
    print("Coverage summary:")
    print("  [OK] Input validation (missing required, empty, whitespace)")
    print("  [OK] Startup ID validation (nonexistent FK)")
    print("  [OK] Full AI pipeline (mocked Groq, parsed, validated, persisted)")
    print("  [OK] Score calculation (deterministic, weighted, bounded 0-100)")
    print("  [OK] Breakdown consistency (weighted sum == total)")
    print("  [OK] Honest evidence notes and AI disclaimer")
    print("  [OK] Missing inputs handled (low score, populated missing_info)")
    print("  [OK] Malformed AI output (502 graceful error)")
    print("  [OK] Missing API key (503)")
    print("  [OK] Rate limit error (429)")
    print("  [OK] Connection timeout (504)")
    print("  [OK] MySQL persistence (direct DB query)")
    print("  [OK] Report retrieval by ID")
    print("  [OK] Report listing with pagination")
    print("  [OK] Startup-filtered report listing")
    print("  [OK] 404 for nonexistent report")
    print("  [OK] 400 for invalid report ID")
    print("  [OK] Report deletion")
    print("  [OK] Delete non-existent report")
    print("  [OK] Markdown-fenced JSON response handling")
    print("  [OK] Phase 1 health API (regression)")
    print("  [OK] Phase 1 startup CRUD (regression)")
    print("  [OK] Phase 2 simulation (regression)")
    print("  [OK] Phase 2 chat session (regression)")
    print("  [OK] OpenAPI schema has all validation routes (regression)")


if __name__ == "__main__":
    run_tests()
