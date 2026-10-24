from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.database.connection import Base


class Startup(Base):
    """
    SQLAlchemy model representing a startup project entity.
    Compatible with MySQL (active), SQLite (fallback), and PostgreSQL.
    """
    __tablename__ = "startups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Startup(id={self.id}, name='{self.name}')>"
