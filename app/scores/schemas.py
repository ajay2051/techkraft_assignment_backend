from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ScoreResponse(BaseModel):
    id: int
    category: str
    score: int
    notes: Optional[str]
    reviewer_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
