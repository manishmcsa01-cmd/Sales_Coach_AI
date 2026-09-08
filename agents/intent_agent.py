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
    
    # Category A: Proactive Coaching & Merchandising Audits
    if any(w in q_lower for w in ["audit", "merchandis", "coaching", "standee", "tent card", "counter check", "qr kit", "sticker", "pos health", "guidance"]):
        classified_intent = "coaching_and_audit"
    
    # Category B: Next-Best-Action & Merchant Strategy
    elif any(w in q_lower for w in ["recommendation", "next best", "next action", "pitch", "how can i improve", "how to improve", "adoption", "strategy", "what should i do", "what to do", "recover"]):
        classified_intent = "get_recommendation"
        
    # Category C: Store Briefing & Profile Deep Dive
    elif any(w in q_lower for w in ["brief", "tell me about", "profile", "overview of", "store details", "background", "branch info", "puregold quezon", "7-eleven eastwood", "puregold makati", "aling nena"]):
        classified_intent = "get_brief"

    # Category D: Risk, Volume & Performance Queries
    elif any(w in q_lower for w in ["churn", "risk", "dormant", "declining", "why does", "contributing factor", "factors", "transaction", "sales", "volume", "revenue", "payment"]):
        classified_intent = "risk_and_performance"

    # Category E: Priority Route Planning
    elif any(w in q_lower for w in ["visit", "priority", "first", "rank", "where to go", "route", "schedule", "morning"]):
        classified_intent = "get_priority_list"

    # 2. Attempt Amazon Bedrock if available and not yet confident
    if not classified_intent:
        try:
            from app.aws.bedrock_client import bedrock_client
            settings = get_settings()
            system_prompt = (
                'Classify query intent into exactly one of: '
                'get_priority_list, get_brief, get_recommendation, coaching_and_audit, risk_and_performance, ask_question, unclear. '
                'Return JSON {"intent": "..."}'
            )
            
            response = bedrock_client.invoke_model(
                model_id=settings.bedrock_model_id,
                system_prompt=system_prompt,
                user_message=query,
                max_tokens=100
            )
            clean_res = re.sub(r'```(?:json)?|```', '', response).strip()
            parsed = json.loads(clean_res)
            classified_intent = parsed.get("intent")
            if "outlet_id" in parsed:
                state["outlet_id"] = parsed["outlet_id"]
        except Exception:
            pass

    state["intent"] = classified_intent or "ask_question"
    return state


