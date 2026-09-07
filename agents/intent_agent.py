import json
import re
from agents.state import AgentState
from app.config import get_settings
from app.aws.xray_helpers import trace

@trace("intent_node")
def intent_node(state: AgentState) -> AgentState:
    query = state.get("user_query", "")
    q_lower = query.lower()
    
    # 1. High-accuracy semantic heuristic classification
    classified_intent = None
    if any(w in q_lower for w in ["visit", "priority", "first", "rank", "where to go", "route", "schedule"]):
        classified_intent = "get_priority_list"
    elif any(w in q_lower for w in ["brief", "profile", "overview of outlet", "store details"]):
        classified_intent = "get_brief"
    elif any(w in q_lower for w in ["recommendation", "action", "next best", "what to do"]):
        classified_intent = "get_recommendation"
    elif any(w in q_lower for w in ["transaction", "sales", "churn", "volume", "history", "risk", "summary"]):
        classified_intent = "ask_question"

    # 2. Attempt Amazon Bedrock if available and not yet confident
    if not classified_intent:
        try:
            from app.aws.bedrock_client import bedrock_client
            settings = get_settings()
            system_prompt = 'Classify intent into: get_priority_list, get_brief, get_recommendation, ask_question, unclear. Return JSON {"intent": "..."}'
            
            response = bedrock_client.invoke_model(
                model_id=settings.bedrock_model_id,
                system_prompt=system_prompt,
                user_message=query,
                max_tokens=100
            )
            # Clean possible markdown
            clean_res = re.sub(r'```(?:json)?|```', '', response).strip()
            parsed = json.loads(clean_res)
            classified_intent = parsed.get("intent")
            if "outlet_id" in parsed:
                state["outlet_id"] = parsed["outlet_id"]
        except Exception:
            pass

    state["intent"] = classified_intent or "ask_question"
    return state

