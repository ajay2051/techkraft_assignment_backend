from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class ScoreCreate(BaseModel):
    category: str
    score: int
    notes: str

    @field_validator('score')
    def validate_score(cls, v):
        if v not in range(1, 6):
            raise ValueError('Score must be between 1 and 5')
        return v


class ScoreResponse(ScoreCreate):
    id: int
    reviewer_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateScoreResponseMessage(BaseModel):
    message: str = "Score Created Successfully...!👍👍"
    score: ScoreResponse
