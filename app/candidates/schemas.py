from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, field_validator

from app.scores.schemas import ScoreResponse


class PaginationResult(BaseModel):
    count: int
    next_page: Optional[str] = None
    previous_page: Optional[str] = None
    current_page: int
    total_pages: int
    items: List


class CandidateCreate(BaseModel):
    name: str
    email: str
    role_applied: str
    skills: List[str]
    keywords: str

    @field_validator('name')
    def validate__name(cls, v):
        name_str = str(v)
        if len(name_str) < 3 or len(name_str) > 15:
            raise ValueError('Name must be between 3 and 10 characters')
        if any(char in r'!@#$%^&*(),.?":{}|<>' for char in v):
            raise ValueError("Name should not contain any special characters")
        return v


class CandidateResponse(CandidateCreate):
    id: int
    status: str
    scores: List[ScoreResponse] = []
    internal_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateCandidateResponseMessage(BaseModel):
    message: str = "Candidate Created Successfully...!👍👍"
    candidate: CandidateResponse
