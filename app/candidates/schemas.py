from typing import Optional, List

from pydantic import BaseModel


class PaginationResult(BaseModel):
    count: int
    next_page: Optional[str] = None
    previous_page: Optional[str] = None
    current_page: int
    total_pages: int
    items: List
