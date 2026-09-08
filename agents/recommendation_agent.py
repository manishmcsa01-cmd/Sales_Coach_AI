import json
from agents.state import AgentState
from app.aws.bedrock_client import bedrock_client
from app.config import get_settings
from app.aws.xray_helpers import trace

@trace("recommendation_node")
def recommendation_node(state: AgentState) -> AgentState:
    outlet_data = state.get("outlet_data", {})
    user_query = state.get("user_query", "").lower()
    settings = get_settings()

    profile = outlet_data.get("profile", {}) if outlet_data else {}
    name = profile.get("name") if profile else None
    score = outlet_data.get("score", 0.0) if outlet_data else 0.0
    db_actions = outlet_data.get("pending_actions", []) if outlet_data else []

    # If no specific outlet was resolved, check ranked outlets
    if not name:
        ranked = state.get("ranked_outlets", [])
        if ranked:
            top = ranked[0]
            name = top.get("name")
            score = top.get("score", 85.0)

    # 1. Check if user is asking for merchandising audit / coaching
    if any(w in user_query for w in ["audit", "merchandis", "standee", "sticker", "coaching"]):
        state["recommendation"] = {
            "action_type": "Merchandising Audit & Collateral Refresh",
            "outlet_name": name or "Assigned Retail Outlets",
            "detail": "Inspect cashier counter visibility. Replace bent or faded QR tent cards with high-durability acrylic standees, and stick the 'Scan to Pay Here' decal at eye level.",
            "reasoning": "Visible point-of-sale branding increases consumer QR payment adoption by up to 35%."
        }
        return state

    # 2. Check if user is asking for pitch strategy / adoption improvement
    if any(w in user_query for w in ["pitch", "adoption", "how to improve", "strategy", "recover"]):
        state["recommendation"] = {
            "action_type": "Merchant Value Pitch & Cash-In Activation",
            "outlet_name": name or "Top Priority Stores",
            "detail": f"Pitch store owner on zero merchant fees for the first ₱50k monthly volume, and enable Cash-In services to generate secondary customer foot traffic to {name or 'the store'}.",
            "reasoning": "Merchants are 3x more engaged when shown that GCash Cash-In brings new customers into their grocery/convenience aisles."
        }
        return state

    # 3. Attempt Bedrock if query is custom
    try:
        system_prompt = (
            'Generate next-best-action based on outlet data and rep question. '
            'Return JSON {"action_type": "...", "detail": "...", "reasoning": "..."}'
        )
        response = bedrock_client.invoke_model(
            model_id=settings.bedrock_model_id,
            system_prompt=system_prompt,
            user_message=f"Query: {user_query}\nData: {json.dumps(outlet_data)}"
        )
        if getattr(settings, "bedrock_guardrail_id", None):
            try:
                gr_res = bedrock_client.apply_guardrail(settings.bedrock_guardrail_id, response)
                response = gr_res.get("filtered_text", response)
            except Exception:
                pass

        parsed = json.loads(response)
        state["recommendation"] = parsed
        return state
    except Exception:
        pass

    # 4. Use Live DB Action if available, or domain fallback
    if db_actions:
        top_act = db_actions[0]
        state["recommendation"] = {
            "action_type": top_act.get("type", "Merchant Action"),
            "outlet_name": name or "Target Outlet",
            "detail": top_act.get("detail", "Conduct on-site audit"),
            "reasoning": f"Prioritized as {top_act.get('priority', 'HIGH')} in territory action database based on score {score:.1f}/100."
        }
    else:
        state["recommendation"] = {
            "action_type": "High Priority Merchant Visit",
            "outlet_name": name or "Target Outlet",
            "detail": f"Conduct an immediate on-site coaching visit to {name or 'the outlet'}. Verify QR standee placement, check cashier transaction app, and review weekly volume.",
            "reasoning": f"Priority AI score is {score:.1f}/100 with actionable opportunities to recover declining monthly volume."
        }
        
    return state


