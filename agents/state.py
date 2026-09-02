from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    user_query: str
    user_id: str
    dsp_id: Optional[str]
    role: str
    area_id: Optional[str]
    intent: Optional[str]
    outlet_id: Optional[str]
    outlet_data: Optional[Dict[str, Any]]
    ranked_outlets: Optional[List[Dict[str, Any]]]
    recommendation: Optional[Dict[str, Any]]
    brief: Optional[str]
    response: Optional[str]
    conversation_history: List[Dict[str, str]]
    error: Optional[str]
    next_agent: Optional[str]
    metadata: Dict[str, Any]
