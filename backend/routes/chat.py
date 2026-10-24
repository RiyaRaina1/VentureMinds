import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.database.connection import get_db, SessionLocal
from backend.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageResponse,
    ChatRequest,
)
from backend.services.chat_service import (
    create_chat_session,
    get_chat_sessions,
    get_chat_session,
    delete_chat_session,
    create_chat_message,
    get_chat_messages,
    get_recent_history_dicts,
    get_attached_startup,
    update_chat_session_title,
)
from backend.services.ai_service import (
    build_system_prompt,
    format_conversation_messages,
    stream_groq_chat,
    sanitize_model,
    AIError,
)

router = APIRouter(prefix="/api/chat", tags=["AI Chat Studio"])


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new AI chat session",
    description="Initializes a new persistent chat session with optional startup project context."
)
def create_session(payload: ChatSessionCreate, db: Session = Depends(get_db)):
    if payload.startup_id:
        startup = get_attached_startup(db, payload.startup_id)
        if not startup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Startup with ID {payload.startup_id} does not exist."
            )
    try:
        session = create_chat_session(db, payload)
        return session
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error creating chat session."
        )


@router.get(
    "/sessions",
    response_model=List[ChatSessionResponse],
    status_code=status.HTTP_200_OK,
    summary="List all chat sessions",
    description="Retrieves all chat sessions ordered by most recently active."
)
def list_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if skip < 0 or limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pagination parameters 'skip' must be >= 0 and 'limit' must be > 0."
        )
    try:
        return get_chat_sessions(db, skip=skip, limit=limit)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error listing chat sessions."
        )


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chat session details",
    description="Retrieves metadata for a specific chat session."
)
def get_session(session_id: int, db: Session = Depends(get_db)):
    if session_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID. Must be a positive integer."
        )
    session = get_chat_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session {session_id} not found."
        )
    return session


@router.get(
    "/sessions/{session_id}/messages",
    response_model=List[ChatMessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Get chat session messages",
    description="Retrieves chronological message history for a specific chat session."
)
def get_session_messages(session_id: int, limit: int = 200, db: Session = Depends(get_db)):
    if session_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID. Must be a positive integer."
        )
    session = get_chat_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session {session_id} not found."
        )
    return get_chat_messages(db, session_id, limit=limit)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete chat session",
    description="Deletes a chat session and all associated persisted messages."
)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    if session_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID. Must be a positive integer."
        )
    deleted = delete_chat_session(db, session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session {session_id} not found."
        )
    return {"status": "ok", "message": f"Chat session {session_id} deleted successfully", "id": session_id}


@router.post(
    "/sessions/{session_id}/messages/stream",
    summary="Stream AI chat response (SSE)",
    description="Streams real-time tokens from Groq using Server-Sent Events (SSE) and persists user and assistant messages into MySQL."
)
async def stream_chat_message(
    session_id: int,
    payload: ChatRequest,
    db: Session = Depends(get_db)
):
    if session_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID. Must be a positive integer."
        )

    session = get_chat_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session {session_id} not found."
        )

    # 1. Fetch prior history BEFORE appending current user message
    history = get_recent_history_dicts(db, session_id, limit=20)

    # 2. Persist user message to MySQL
    selected_model = sanitize_model(payload.model)
    user_msg = create_chat_message(
        db=db,
        session_id=session_id,
        role="user",
        content=payload.message,
        model=selected_model
    )

    # 3. Auto-generate conversational title if still default
    if not session.title or session.title == "New VentureMind Chat":
        short_title = payload.message.strip().replace("\n", " ")[:35]
        if len(payload.message.strip()) > 35:
            short_title += "..."
        update_chat_session_title(db, session_id, short_title)

    # 4. Load dynamic startup context if linked
    startup = get_attached_startup(db, session.startup_id)
    system_prompt = build_system_prompt(startup)

    # 5. Build structured message array
    formatted_messages = format_conversation_messages(
        system_prompt=system_prompt,
        history=history,
        user_message=payload.message
    )

    # 6. Generator for Server-Sent Events
    async def sse_event_generator():
        full_response_text = ""
        try:
            async for chunk in stream_groq_chat(
                messages=formatted_messages,
                model=selected_model
            ):
                full_response_text += chunk
                token_event = {
                    "content": chunk
                }
                yield f"event: token\ndata: {json.dumps(token_event)}\n\n"

            # Persist the final completed assistant response into MySQL
            save_db = SessionLocal()
            try:
                assistant_msg = create_chat_message(
                    db=save_db,
                    session_id=session_id,
                    role="assistant",
                    content=full_response_text,
                    model=selected_model
                )
                done_event = {
                    "message_id": assistant_msg.id,
                    "session_id": session_id,
                    "model": selected_model
                }
                yield f"event: done\ndata: {json.dumps(done_event)}\n\n"
            finally:
                save_db.close()

        except AIError as ai_err:
            error_event = {
                "error": True,
                "status_code": ai_err.status_code,
                "detail": ai_err.message
            }
            yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
        except Exception as exc:
            error_event = {
                "error": True,
                "status_code": 500,
                "detail": "Unexpected error while streaming response from AI engine."
            }
            yield f"event: error\ndata: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
