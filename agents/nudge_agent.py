import json
from agents.state import AgentState
from app.aws.bedrock_client import bedrock_client
from app.config import get_settings
from app.aws.xray_helpers import trace

@trace("nudge_node")
def nudge_node(state: AgentState) -> AgentState:
    ranked = state.get("ranked_outlets", [])
    settings = get_settings()
    if "metadata" not in state:
        state["metadata"] = {}
        
    top_name = ranked[0].get("name") if ranked else "high-priority outlets"

    try:
        system_prompt = "Generate a short 1-sentence sales coaching nudge/reminder based on the provided ranked outlets data."
        response = bedrock_client.invoke_model(
            model_id=settings.bedrock_model_id,
            system_prompt=system_prompt,
            user_message=json.dumps(ranked[:3])
        )
        state["metadata"]["nudges"] = [response.strip()]
    except Exception:
        state["metadata"]["nudges"] = [f"💡 Tip: Plan an early morning visit to {top_name} to secure merchant commitment before peak hours!"]
        
    return state

