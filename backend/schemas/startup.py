from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class StartupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the startup project", example="VentureMind AI")
    description: Optional[str] = Field(None, max_length=5000, description="Detailed concept, problem, or value proposition", example="AI platform for startup valuation and simulation")


class StartupCreate(StartupBase):
    pass


class StartupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated startup name")
    description: Optional[str] = Field(None, max_length=5000, description="Updated description")


class StartupResponse(StartupBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
