from pydantic import BaseModel, Field
from typing import Literal

class ClassificationResult(BaseModel):
    category: Literal["bug", "question", "feedback"] = Field(description="The classification category of the message.")
    summary: str = Field(description="A 1-sentence summary of the user's input.")
    urgency: Literal["high", "medium", "low"] = Field(description="Urgency assessment based on tone and text content.")