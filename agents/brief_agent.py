import json
from agents.state import AgentState
from app.aws.bedrock_client import bedrock_client
from app.config import get_settings
from app.aws.xray_helpers import trace

@trace("brief_node")
def brief_node(state: AgentState) -> AgentState:
    outlet_data = state.get("outlet_data", {})
    
    if not outlet_data:
        state["error"] = "Missing data for brief generation."
        return state
        
    settings = get_settings()
    system_prompt = "Generate a concise sales brief based on the outlet data (profile and transactions). Include overview, performance, risks, actions."
    
    response = bedrock_client.invoke_model(
        model_id=settings.bedrock_model_id,
        system_prompt=system_prompt,
        user_message=json.dumps(outlet_data)
    )
    
    safe_response = bedrock_client.apply_guardrail(response) if hasattr(bedrock_client, 'apply_guardrail') else response
    state["brief"] = safe_response
    
    return state
