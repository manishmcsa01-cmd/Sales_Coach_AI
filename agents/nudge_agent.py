import json
from agents.state import AgentState
from app.aws.bedrock_client import bedrock_client
from app.config import get_settings
from app.aws.xray_helpers import trace

@trace("nudge_node")
def nudge_node(state: AgentState) -> AgentState:
    ranked = state.get("ranked_outlets", [])
    settings = get_settings()
    
    system_prompt = "Generate a nudge/reminder based on the provided ranked outlets data."
    
    response = bedrock_client.invoke_model(
        model_id=settings.bedrock_model_id,
        system_prompt=system_prompt,
        user_message=json.dumps(ranked)
    )
    
    if "metadata" not in state:
        state["metadata"] = {}
    
    state["metadata"]["nudges"] = [response]
        
    return state
