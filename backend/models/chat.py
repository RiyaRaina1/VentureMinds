from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class ChatSession(Base):
    """
    SQLAlchemy model representing a chat conversation session.
    Can be optionally linked to a specific Startup project entity.
    """
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    startup_id = Column(Integer, ForeignKey("startups.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=True, default="New VentureMind Chat")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.id"
    )
    startup = relationship("Startup", backref="chat_sessions")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, title='{self.title}', startup_id={self.startup_id})>"


class ChatMessage(Base):
    """
    SQLAlchemy model representing individual messages in a chat session.
    Supported roles: 'system', 'user', 'assistant'.
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    model = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role='{self.role}')>"
