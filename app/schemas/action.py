from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ActionResponse(BaseModel):
    action_id: str
    outlet_id: str
    action_type: str
    action_detail: str
    status: str
    created_at: datetime

class ActionUpdateRequest(BaseModel):
    status: str
    completion_notes: Optional[str] = None
