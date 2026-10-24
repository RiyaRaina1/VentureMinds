"""
VentureMind AI - Comprehensive Backend & Database Test Suite (Phase 1 & Phase 2)
Tests:
1. Health API
2. OpenAPI & Swagger Docs endpoints
3. Startup Project CRUD (Create, Read, Update, Delete)
4. Deterministic Financial Simulation API
5. Chat Session Creation & Retrieval
6. Chat Session with Startup Context
7. Chat Message History Retrieval
8. Streaming AI Endpoint & MySQL Persistence
9. Missing API Key & Error Handling in Stream
10. Chat Session Deletion & Cascade
11. Invalid Session & Validation Error Handling
12. Direct MySQL Chat Persistence Verification
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

# Add backend and root to sys.path
backend_dir = Path(__file__).resolve().parent
parent_dir = backend_dir.parent
for p in [str(backend_dir), str(parent_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import init_db, SessionLocal, engine
from backend.models.startup import Startup
from backend.models.chat import ChatSession, ChatMessage
from backend.services.ai_service import AIConfigError, AIAuthError

client = TestClient(app)


def run_tests():
    print("============================================================")
    print("STARTING VENTUREMIND AI PHASE 1 + PHASE 2 BACKEND TEST SUITE")
    print("============================================================\n")

    # 0. Initialize DB
    init_db()

    # 1. Test Health API
    print("1. Testing GET /api/health...")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    health_data = res.json()
    assert health_data.get("status") == "ok", "Expected status 'ok'"
    assert health_data.get("service") == "VentureMind API", "Expected service 'VentureMind API'"
    print("   [PASS] Health API returned expected status and version:", health_data)

    # 2. Test OpenAPI & Docs
    print("\n2. Testing Documentation endpoints (/docs and /openapi.json)...")
    res_docs = client.get("/docs")
    assert res_docs.status_code == 200, "GET /docs failed"
    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200, "GET /openapi.json failed"
    schema = res_openapi.json()
    assert "/api/health" in schema["paths"]
    assert "/api/startups" in schema["paths"]
    assert "/api/startups/{startup_id}" in schema["paths"]
    assert "/api/simulation/run" in schema["paths"]
    assert "/api/chat/sessions" in schema["paths"]
    assert "/api/chat/sessions/{session_id}" in schema["paths"]
    assert "/api/chat/sessions/{session_id}/messages" in schema["paths"]
    assert "/api/chat/sessions/{session_id}/messages/stream" in schema["paths"]
    print("   [PASS] OpenAPI schema includes all Phase 1 & Phase 2 routes.")

    # 3. Test Startup Project CRUD
    print("\n3. Testing Startup Project CRUD (/api/startups)...")
    new_startup_payload = {
        "name": "NeuralFlow AI",
        "description": "Next-gen autonomous enterprise automation workflows."
    }
    res_create = client.post("/api/startups", json=new_startup_payload)
    assert res_create.status_code == 201, f"Create failed: {res_create.status_code} - {res_create.text}"
    created_startup = res_create.json()
    startup_id = created_startup["id"]
    assert created_startup["name"] == new_startup_payload["name"]
    print(f"   [PASS] POST /api/startups created Startup #{startup_id}: {created_startup['name']}")

    # Read List
    res_list = client.get("/api/startups")
    assert res_list.status_code == 200
    assert any(s["id"] == startup_id for s in res_list.json())
    print(f"   [PASS] GET /api/startups successfully retrieved list.")

    # Read By ID
    res_get = client.get(f"/api/startups/{startup_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == startup_id
    print(f"   [PASS] GET /api/startups/{startup_id} successfully fetched record.")

    # Update
    update_payload = {
        "name": "NeuralFlow Enterprise AI",
        "description": "Updated platform description with Series A validation."
    }
    res_update = client.put(f"/api/startups/{startup_id}", json=update_payload)
    assert res_update.status_code == 200
    assert res_update.json()["name"] == update_payload["name"]
    print(f"   [PASS] PUT /api/startups/{startup_id} updated record.")

    # 4. Test Deterministic Simulation API
    print("\n4. Testing POST /api/simulation/run...")
    sim_exact_payload = {
        "price": 100.0,
        "customers": 100,
        "monthly_growth": 12.0,
        "churn": 3.0,
        "marketing_spend": 2000.0,
        "salaries": 2500.0,
        "infrastructure_cost": 500.0,
        "other_expenses": 0.0,
        "cash_balance": 50000.0
    }
    res_sim = client.post("/api/simulation/run", json=sim_exact_payload)
    assert res_sim.status_code == 200, f"Simulation failed: {res_sim.text}"
    sim_res = res_sim.json()
    assert sim_res["mrr"] == 10000.0
    assert sim_res["arr"] == 120000.0
    assert sim_res["monthly_burn"] == 5000.0
    assert sim_res["runway_months"] == 10.0
    print(f"   [PASS] POST /api/simulation/run matched benchmark (MRR: ${sim_res['mrr']}, Burn: ${sim_res['monthly_burn']}).")

    # 5. Test Chat Session Creation
    print("\n5. Testing Chat Session Creation (POST /api/chat/sessions)...")
    session_payload = {
        "title": "GTM Strategy Session",
        "startup_id": startup_id
    }
    res_sess = client.post("/api/chat/sessions", json=session_payload)
    assert res_sess.status_code == 201, f"Session create failed: {res_sess.text}"
    sess_data = res_sess.json()
    chat_session_id = sess_data["id"]
    assert sess_data["title"] == "GTM Strategy Session"
    assert sess_data["startup_id"] == startup_id
    assert "created_at" in sess_data
    print(f"   [PASS] Created ChatSession #{chat_session_id} linked to Startup #{startup_id}.")

    # 6. Test Chat Session Retrieval
    print("\n6. Testing Chat Session Retrieval (GET /api/chat/sessions and /api/chat/sessions/{id})...")
    res_all_sess = client.get("/api/chat/sessions")
    assert res_all_sess.status_code == 200
    assert any(s["id"] == chat_session_id for s in res_all_sess.json())
    
    res_single_sess = client.get(f"/api/chat/sessions/{chat_session_id}")
    assert res_single_sess.status_code == 200
    assert res_single_sess.json()["id"] == chat_session_id
    print(f"   [PASS] Retrieved ChatSession #{chat_session_id} successfully.")

    # 7. Test Streaming Chat Endpoint & MySQL Message Persistence
    print("\n7. Testing POST /api/chat/sessions/{id}/messages/stream (SSE Streaming & Persistence)...")
    
    async def mock_stream_chunks(*args, **kwargs):
        chunks = ["Here is ", "your GTM ", "strategy: ", "1. Focus on ICP ", "2. Cold outreach."]
        for chunk in chunks:
            yield chunk

    with patch("backend.routes.chat.stream_groq_chat", side_effect=mock_stream_chunks):
        stream_payload = {
            "message": "What is the best GTM motion for B2B SaaS?",
            "model": "openai/gpt-oss-120b"
        }
        res_stream = client.post(
            f"/api/chat/sessions/{chat_session_id}/messages/stream",
            json=stream_payload
        )
        assert res_stream.status_code == 200, f"Stream failed: {res_stream.text}"
        stream_text = res_stream.text
        assert "event: token" in stream_text
        assert "event: done" in stream_text
        assert "Focus on ICP" in stream_text
        print(f"   [PASS] SSE stream executed successfully and emitted token and done events.")

    # 8. Test Message History & Assistant Persistence
    print("\n8. Testing Chat History & Assistant Persistence (GET /api/chat/sessions/{id}/messages)...")
    res_msgs = client.get(f"/api/chat/sessions/{chat_session_id}/messages")
    assert res_msgs.status_code == 200
    msgs = res_msgs.json()
    assert len(msgs) >= 2, f"Expected at least 2 messages (user + assistant), got {len(msgs)}"
    user_msgs = [m for m in msgs if m["role"] == "user"]
    assistant_msgs = [m for m in msgs if m["role"] == "assistant"]
    assert len(user_msgs) >= 1
    assert len(assistant_msgs) >= 1
    assert "What is the best GTM motion" in user_msgs[0]["content"]
    assert "Focus on ICP" in assistant_msgs[0]["content"]
    print(f"   [PASS] Verified persistent user message and assistant message in MySQL database.")

    # 9. Test Direct MySQL Model Persistence for Chat
    print("\n9. Testing Direct MySQL Database Queries for Chat...")
    db_session = SessionLocal()
    db_chat_session = db_session.query(ChatSession).filter(ChatSession.id == chat_session_id).first()
    assert db_chat_session is not None
    assert len(db_chat_session.messages) >= 2
    assert db_chat_session.startup_id == startup_id
    db_session.close()
    print("   [PASS] Direct MySQL query confirmed ChatSession and ChatMessages persisted with ForeignKeys.")

    # 10. Test AI Error Handling in Stream (e.g. Missing Key / Rate Limit)
    print("\n10. Testing AI Error Handling in Stream...")
    async def mock_stream_error(*args, **kwargs):
        raise AIConfigError("Groq API key is not configured in backend/.env.")
        yield ""

    with patch("backend.routes.chat.stream_groq_chat", side_effect=mock_stream_error):
        res_err_stream = client.post(
            f"/api/chat/sessions/{chat_session_id}/messages/stream",
            json={"message": "Trigger test error", "model": "openai/gpt-oss-120b"}
        )
        assert res_err_stream.status_code == 200
        assert "event: error" in res_err_stream.text
        assert "Groq API key is not configured" in res_err_stream.text
        print("   [PASS] Clean SSE error event dispatched on AIConfigError.")

    # 11. Test Invalid Session & Validation Errors
    print("\n11. Testing Invalid Session and Schema Validations...")
    res_invalid_sess = client.get("/api/chat/sessions/999999")
    assert res_invalid_sess.status_code == 404
    
    res_empty_msg = client.post(
        f"/api/chat/sessions/{chat_session_id}/messages/stream",
        json={"message": "   "}
    )
    assert res_empty_msg.status_code in (400, 422)
    print("   [PASS] Correct 404 and 422 validations returned.")

    # 12. Test Chat Session Deletion & Cascade
    print("\n12. Testing DELETE /api/chat/sessions/{session_id}...")
    res_del_sess = client.delete(f"/api/chat/sessions/{chat_session_id}")
    assert res_del_sess.status_code == 200
    
    res_after_del = client.get(f"/api/chat/sessions/{chat_session_id}")
    assert res_after_del.status_code == 404
    
    db_verify = SessionLocal()
    orphaned_msgs = db_verify.query(ChatMessage).filter(ChatMessage.session_id == chat_session_id).all()
    assert len(orphaned_msgs) == 0, "Cascade delete failed: Orphaned chat messages found"
    db_verify.close()
    print("   [PASS] Chat session deleted and cascade deleted all associated messages.")

    # Cleanup test startup
    res_del_startup = client.delete(f"/api/startups/{startup_id}")
    assert res_del_startup.status_code == 200
    print(f"   [PASS] Test startup #{startup_id} cleaned up.")

    print("\n============================================================")
    print("ALL PHASE 1 + PHASE 2 TESTS PASSED SUCCESSFULLY! (100%)")
    print("============================================================\n")


if __name__ == "__main__":
    run_tests()
