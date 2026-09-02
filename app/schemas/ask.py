from pydantic import BaseModel
from typing import List, Optional

class AskRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None

class AskResponse(BaseModel):
    answer: str
    conversation_id: str
    sources: List[str]
    is_clarification: bool
