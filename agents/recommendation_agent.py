import json
from agents.state import AgentState
from app.aws.bedrock_client import bedrock_client
from app.config import get_settings
from app.aws.xray_helpers import trace

@trace("recommendation_node")
def recommendation_node(state: AgentState) -> AgentState:
    outlet_data = state.get("outlet_data", {})
    if not outlet_data:
        # Fallback if no specific outlet selected
        ranked = state.get("ranked_outlets", [])
        if ranked:
            top = ranked[0]
            state["recommendation"] = {
                "action_type": "high_priority_visit",
                "outlet_name": top.get("name"),
                "detail": f"Conduct an immediate on-site visit to {top.get('name')}. Review QR standee placement and pitch Scan-to-Pay promotions.",
                "reasoning": f"Outlet has a top priority score of {top.get('score', 0):.1f}/100 and shows recent transaction deceleration."
            }
        else:
            state["recommendation"] = {
                "action_type": "territory_review",
                "detail": "Review assigned merchant accounts and schedule morning visits for top-scoring outlets.",
                "reasoning": "Standard morning optimization sequence."
            }
        return state
        
    settings = get_settings()
    profile = outlet_data.get("profile", {})
    name = profile.get("name", "Outlet")
    score = outlet_data.get("score", 0.0)

    try:
        system_prompt = 'Generate next-best-action based on outlet data. Return JSON {"action_type": "...", "detail": "...", "reasoning": "..."}'
        response = bedrock_client.invoke_model(
            model_id=settings.bedrock_model_id,
            system_prompt=system_prompt,
            user_message=json.dumps(outlet_data)
        )
        
        # Apply guardrail safely if configured
        if getattr(settings, "bedrock_guardrail_id", None):
            try:
                gr_res = bedrock_client.apply_guardrail(settings.bedrock_guardrail_id, response)
                response = gr_res.get("filtered_text", response)
            except Exception:
                pass

        try:
            parsed = json.loads(response)
            state["recommendation"] = parsed
        except json.JSONDecodeError:
            state["recommendation"] = {"action_type": "outlet_visit", "detail": response, "reasoning": f"Targeting {name} based on priority score {score}"}
    except Exception:
        # Domain-grounded fallback
        state["recommendation"] = {
            "action_type": "merchant_visit_and_activation",
            "outlet_name": name,
            "detail": f"Schedule an in-person coaching visit with the store manager at {name}. Inspect QR standee visibility, conduct a test P2M transaction, and verify Cash-In liquidity.",
            "reasoning": f"Priority score is {score:.1f}/100 with actionable opportunities to recover declining monthly volume."
        }
        
    return state

