from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class BriefResponse(BaseModel):
    outlet_id: str
    outlet_name: str
    brief_text: str
    generated_at: datetime
    is_cached: bool

class AreaSummaryResponse(BaseModel):
    area_name: str
    total_outlets: int
    active_count: int
    at_risk_count: int
    avg_score: float
    top_issues: List[str]
