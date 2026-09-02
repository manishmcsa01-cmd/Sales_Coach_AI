import json
from agents.state import AgentState
from app.aws.bedrock_client import bedrock_client
from app.config import get_settings
from app.aws.xray_helpers import trace

@trace("intent_node")
def intent_node(state: AgentState) -> AgentState:
    query = state.get("user_query", "")
    settings = get_settings()
    
    system_prompt = 'Classify intent into: get_priority_list, get_brief, get_recommendation, ask_question, unclear. Return JSON {"intent": "..."}'
    
    response = bedrock_client.invoke_model(
        model_id=settings.bedrock_model_id,
        system_prompt=system_prompt,
        user_message=query
    )
    
    try:
        parsed = json.loads(response)
        state["intent"] = parsed.get("intent", "unclear")
        if "outlet_id" in parsed:
            state["outlet_id"] = parsed["outlet_id"]
    except json.JSONDecodeError:
        state["intent"] = "unclear"
        
    return state
