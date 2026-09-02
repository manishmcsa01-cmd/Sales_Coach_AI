from agents.state import AgentState
from app.aws.bedrock_client import bedrock_client
from app.config import get_settings
from app.aws.xray_helpers import trace

@trace("clarification_node")
def clarification_node(state: AgentState) -> AgentState:
    query = state.get("user_query", "")
    settings = get_settings()
    
    system_prompt = "The user query is unclear. Ask a clarifying question."
    
    response = bedrock_client.invoke_model(
        model_id=settings.bedrock_model_id,
        system_prompt=system_prompt,
        user_message=query
    )
    
    safe_response = bedrock_client.apply_guardrail(response) if hasattr(bedrock_client, 'apply_guardrail') else response
    state["response"] = safe_response
    
    return state
