"""
VentureMind AI - Database Persistence Test (Phase 1 & Phase 2)
1. Create a startup project and a linked AI Chat Session with messages in MySQL.
2. Confirm records exist.
3. Simulate backend shutdown (engine.dispose(), close all sessions).
4. Simulate backend restart (fresh engine connection and session).
5. Retrieve startup, chat session, and messages from MySQL.
6. Verify all data persisted completely intact.
7. Clean up test records.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
parent_dir = backend_dir.parent
for p in [str(backend_dir), str(parent_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.database.connection import init_db, SessionLocal, engine
from backend.models.startup import Startup
from backend.models.chat import ChatSession, ChatMessage
from backend.services.startup_service import create_startup, get_startup
from backend.services.chat_service import create_chat_session, create_chat_message, get_chat_session
from backend.schemas.startup import StartupCreate
from backend.schemas.chat import ChatSessionCreate


def test_persistence_flow():
    print("============================================================")
    print("TESTING FULL MYSQL PERSISTENCE ACROSS RESTART (PHASE 1 + 2)")
    print("============================================================\n")

    # Step 1: Initialize DB and create records
    init_db()
    session_1 = SessionLocal()
    
    # 1a. Create Startup
    startup_input = StartupCreate(
        name="AeroDynamics Autonomous",
        description="Autonomous aerospace telemetry models."
    )
    created_startup = create_startup(session_1, startup_input)
    startup_id = created_startup.id
    
    # 1b. Create ChatSession linked to Startup
    chat_sess_input = ChatSessionCreate(
        title="Aerospace Valuation Strategy",
        startup_id=startup_id
    )
    created_chat_sess = create_chat_session(session_1, chat_sess_input)
    chat_sess_id = created_chat_sess.id
    
    # 1c. Create User and Assistant Chat Messages
    msg_user = create_chat_message(
        session_1,
        session_id=chat_sess_id,
        role="user",
        content="What is the TAM for autonomous aerospace telematics?",
        model="openai/gpt-oss-120b"
    )
    msg_assistant = create_chat_message(
        session_1,
        session_id=chat_sess_id,
        role="assistant",
        content="The commercial autonomous aerospace telematics TAM is projected at $14.2B by 2030.",
        model="openai/gpt-oss-120b"
    )
    
    session_1.close()
    print(f"1. Created Startup #{startup_id} and ChatSession #{chat_sess_id} with 2 messages in Session 1.")

    # Step 2: Confirm records exist in database
    session_check = SessionLocal()
    check_startup = get_startup(session_check, startup_id)
    check_chat = get_chat_session(session_check, chat_sess_id)
    assert check_startup is not None
    assert check_chat is not None
    assert len(check_chat.messages) == 2
    session_check.close()
    print("2. Confirmed records exist in MySQL database.")

    # Step 3: Stop backend / dispose all engine connections
    engine.dispose()
    print("3. Simulated backend stop: Engine connection pool disposed.")

    # Step 4: Restart backend / re-open fresh engine connection from MySQL database
    new_session = SessionLocal()
    print("4. Simulated backend restart: New independent MySQL session initialized.")

    # Step 5 & 6: Retrieve and confirm persistence
    persisted_startup = get_startup(new_session, startup_id)
    persisted_chat = get_chat_session(new_session, chat_sess_id)

    assert persisted_startup is not None, "Failed: Startup record lost after restart!"
    assert persisted_startup.name == "AeroDynamics Autonomous"
    
    assert persisted_chat is not None, "Failed: Chat session lost after restart!"
    assert persisted_chat.title == "Aerospace Valuation Strategy"
    assert persisted_chat.startup_id == startup_id
    assert len(persisted_chat.messages) == 2
    assert persisted_chat.messages[0].role == "user"
    assert "TAM for autonomous" in persisted_chat.messages[0].content
    assert persisted_chat.messages[1].role == "assistant"
    assert "$14.2B" in persisted_chat.messages[1].content
    
    print(f"5. Successfully retrieved Startup #{persisted_startup.id} and ChatSession #{persisted_chat.id} from MySQL.")
    print(f"6. Message data verified completely intact ({len(persisted_chat.messages)} messages).")

    # Cleanup
    new_session.delete(persisted_chat)  # Cascade deletes messages
    new_session.delete(persisted_startup)
    new_session.commit()
    new_session.close()
    print("7. Persistence test passed 100% and test records cleaned up.\n")


if __name__ == "__main__":
    test_persistence_flow()
