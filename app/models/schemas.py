from pydantic import BaseModel, EmailStr, Field
from typing import List, Literal


class BriefingRequest(BaseModel):
    recipientEmail: EmailStr
    timeframe: Literal["1", "7", "30"] = "7"
    region: Literal["domestic", "international", "both"] = "both"
    categories: List[str] = Field(default_factory=lambda: ["film", "tv", "new_media", "investment"])


class BriefingItem(BaseModel):
    title: str
    source: str
    url: str
    published: str
    summary: str
    investorWhy: str
    section: str


class BriefingResponse(BaseModel):
    generatedAt: str
    timeframe: str
    region: str
    executiveSummary: List[str]
    items: List[BriefingItem]
    html: str
    text: str
    subject: str
