from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OutletResponse(BaseModel):
    outlet_id: str
    outlet_name: str
    merchant_name: str
    outlet_type: str
    status: str
    priority_score: float
    contributing_factors: List[str]
    address: str
    city: str

class OutletListResponse(BaseModel):
    outlets: List[OutletResponse]
    total: int
    date: datetime
