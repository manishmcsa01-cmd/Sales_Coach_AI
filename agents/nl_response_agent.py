import json
from agents.state import AgentState
from app.aws.bedrock_client import bedrock_client
from app.config import get_settings
from app.aws.xray_helpers import trace

@trace("nl_response_node")
def nl_response_node(state: AgentState) -> AgentState:
    data_context = {
        "intent": state.get("intent"),
        "outlet_data": state.get("outlet_data"),
        "ranked_outlets": state.get("ranked_outlets"),
        "recommendation": state.get("recommendation"),
        "brief": state.get("brief"),
        "nudges": state.get("metadata", {}).get("nudges", []),
        "history": state.get("conversation_history", [])
    }
    
    settings = get_settings()
    system_prompt = "Format the provided data and conversation history into a natural language response appropriate for the user role."
    
    response = bedrock_client.invoke_model(
        model_id=settings.bedrock_model_id,
        system_prompt=system_prompt,
        user_message=json.dumps(data_context)
    )
    
    safe_response = bedrock_client.apply_guardrail(response) if hasattr(bedrock_client, 'apply_guardrail') else response
    state["response"] = safe_response
    
    return state
