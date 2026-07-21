from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime

class ScrapedPageRecord(BaseModel):
    """The strict data contract for our structured output."""
    url: HttpUrl
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=10)
    author: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)