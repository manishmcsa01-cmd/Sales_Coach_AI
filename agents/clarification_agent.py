from agents.state import AgentState
from app.aws.bedrock_client import bedrock_client
from app.config import get_settings
from app.aws.xray_helpers import trace

@trace("clarification_node")
def clarification_node(state: AgentState) -> AgentState:
    query = state.get("user_query", "")
    settings = get_settings()
    
    try:
        system_prompt = "You are Sales Coach AI for GCash DSPs. The user query is unclear. Ask a friendly, brief clarifying question offering helpful examples."
        response = bedrock_client.invoke_model(
            model_id=settings.bedrock_model_id,
            system_prompt=system_prompt,
            user_message=query
        )
        if getattr(settings, "bedrock_guardrail_id", None):
            try:
                gr_res = bedrock_client.apply_guardrail(settings.bedrock_guardrail_id, response)
                response = gr_res.get("filtered_text", response)
            except Exception:
                pass
        state["response"] = response
    except Exception:
        state["response"] = (
            "I'd love to help! Could you please clarify your request? For example, you can ask:\n\n"
            "- *'Which outlets should I visit first today?'*\n"
            "- *'What is the next best action for SM Makati?'*\n"
            "- *'Give me an outlet brief on Eastwood branch'*."
        )
    
    return state

