from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from backend.models.chat import ChatSession, ChatMessage
from backend.models.startup import Startup
from backend.schemas.chat import ChatSessionCreate


def create_chat_session(db: Session, data: ChatSessionCreate) -> ChatSession:
    """Create a new chat session in the database."""
    session_title = data.title if data.title else "New VentureMind Chat"
    session = ChatSession(
        title=session_title,
        startup_id=data.startup_id
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_chat_sessions(db: Session, skip: int = 0, limit: int = 100) -> List[ChatSession]:
    """Retrieve chat sessions ordered by most recently updated."""
    return (
        db.query(ChatSession)
        .order_by(ChatSession.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_chat_session(db: Session, session_id: int) -> Optional[ChatSession]:
    """Retrieve a single chat session by ID."""
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def update_chat_session_title(db: Session, session_id: int, title: str) -> Optional[ChatSession]:
    """Update title for a chat session."""
    session = get_chat_session(db, session_id)
    if not session:
        return None

    session.title = title.strip()
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session


def touch_chat_session(db: Session, session_id: int):
    """Update the updated_at timestamp on a session."""
    session = get_chat_session(db, session_id)
    if session:
        session.updated_at = datetime.utcnow()
        db.commit()


def delete_chat_session(db: Session, session_id: int) -> bool:
    """Delete a chat session and cascade delete all its messages."""
    session = get_chat_session(db, session_id)
    if not session:
        return False

    db.delete(session)
    db.commit()
    return True


def create_chat_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
    model: Optional[str] = None
) -> ChatMessage:
    """Persist a single chat message (user, assistant, or system) into MySQL."""
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        model=model
    )
    db.add(message)

    # Touch the session updated_at
    session = get_chat_session(db, session_id)
    if session:
        session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(message)
    return message


def get_chat_messages(db: Session, session_id: int, limit: int = 200) -> List[ChatMessage]:
    """Retrieve messages for a chat session in chronological order."""
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .limit(limit)
        .all()
    )


def get_recent_history_dicts(db: Session, session_id: int, limit: int = 20) -> List[Dict[str, str]]:
    """Retrieve the recent message history formatted as dictionaries for LLM context."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.desc())
        .limit(limit)
        .all()
    )
    # Reverse to get chronological order
    messages.reverse()
    return [{"role": msg.role, "content": msg.content} for msg in messages]


def get_attached_startup(db: Session, startup_id: Optional[int]) -> Optional[Startup]:
    """Retrieve startup entity if startup_id is provided."""
    if not startup_id:
        return None
    return db.query(Startup).filter(Startup.id == startup_id).first()
