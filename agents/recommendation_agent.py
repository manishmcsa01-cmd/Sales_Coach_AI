import json
from agents.state import AgentState
from app.aws.bedrock_client import bedrock_client
from app.config import get_settings
from app.aws.xray_helpers import trace

@trace("recommendation_node")
def recommendation_node(state: AgentState) -> AgentState:
    outlet_data = state.get("outlet_data", {})
    if not outlet_data:
        state["error"] = "No outlet data for recommendation."
        return state
        
    settings = get_settings()
    system_prompt = 'Generate next-best-action based on outlet data. Return JSON {"action_type": "...", "detail": "...", "reasoning": "..."}'
    
    response = bedrock_client.invoke_model(
        model_id=settings.bedrock_model_id,
        system_prompt=system_prompt,
        user_message=json.dumps(outlet_data)
    )
    
    safe_response = bedrock_client.apply_guardrail(response) if hasattr(bedrock_client, 'apply_guardrail') else response
    
    try:
        parsed = json.loads(safe_response)
        state["recommendation"] = parsed
    except json.JSONDecodeError:
        state["recommendation"] = {"action_type": "unknown", "detail": safe_response, "reasoning": "Could not parse JSON"}
        
    return state
