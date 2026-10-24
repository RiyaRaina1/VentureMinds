from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ChatSessionCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Optional title for the chat session")
    startup_id: Optional[int] = Field(None, description="Optional startup project ID to provide context")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_stripped = v.strip()
            return v_stripped if v_stripped else None
        return None


class ChatSessionUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Updated session title")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("Session title cannot be empty.")
        return v_stripped


class ChatMessageBase(BaseModel):
    role: str = Field(..., description="Message author role ('system', 'user', 'assistant')")
    content: str = Field(..., min_length=1, description="Message text content")
    model: Optional[str] = Field(None, max_length=100, description="AI model used for generation")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = {"system", "user", "assistant"}
        if v not in valid_roles:
            raise ValueError(f"Role must be one of {valid_roles}")
        return v


class ChatMessageResponse(ChatMessageBase):
    id: int
    session_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionResponse(BaseModel):
    id: int
    startup_id: Optional[int] = None
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    session: ChatSessionResponse
    messages: List[ChatMessageResponse]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=20000, description="User prompt message")
    model: Optional[str] = Field(None, max_length=100, description="Optional AI model selection")

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("Message cannot be empty or whitespace only.")
        return v_stripped
