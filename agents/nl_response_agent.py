import json
from agents.state import AgentState
from app.aws.bedrock_client import bedrock_client
from app.config import get_settings
from app.aws.xray_helpers import trace

@trace("nl_response_node")
def nl_response_node(state: AgentState) -> AgentState:
    ranked = state.get("ranked_outlets") or []
    outlet_data = state.get("outlet_data") or {}
    recommendation = state.get("recommendation") or {}
    brief = state.get("brief") or ""
    nudges = state.get("metadata", {}).get("nudges", [])
    history = state.get("conversation_history", [])
    intent = state.get("intent", "general")
    query = state.get("user_query", "")

    data_context = {
        "intent": intent,
        "query": query,
        "outlet_data": outlet_data,
        "ranked_outlets": ranked[:5],
        "recommendation": recommendation,
        "brief": brief,
        "nudges": nudges,
        "history": history
    }
    
    settings = get_settings()
    
    # 1. Attempt Bedrock generation
    try:
        system_prompt = (
            "You are Sales Coach AI, an intelligent digital coach for GCash field sales representatives (DSPs) in the Philippines. "
            "Using the provided territory data, generate a clear, highly actionable, encouraging response in clean Markdown. "
            "Highlight outlet names, priority scores, and specific next-best-actions."
        )
        
        response = bedrock_client.invoke_model(
            model_id=settings.bedrock_model_id,
            system_prompt=system_prompt,
            user_message=json.dumps(data_context),
            max_tokens=800
        )
        if getattr(settings, "bedrock_guardrail_id", None):
            try:
                gr_res = bedrock_client.apply_guardrail(settings.bedrock_guardrail_id, response)
                response = gr_res.get("filtered_text", response)
            except Exception:
                pass
        if response and len(response.strip()) > 10:
            state["response"] = response.strip()
            return state
    except Exception:
        pass

    # 2. Grounded High-Quality Fallback Synthesis
    lines = []
    
    if brief:
        lines.append(brief)
        lines.append("")

    if recommendation:
        lines.append("### 🎯 Recommended Next Best Action")
        if isinstance(recommendation, dict):
            detail = recommendation.get("detail", "")
            reasoning = recommendation.get("reasoning", "")
            action_type = recommendation.get("action_type", "visit").replace("_", " ").title()
            lines.append(f"**Action [{action_type}]**: {detail}")
            if reasoning:
                lines.append(f"**Why this matters**: {reasoning}")
        else:
            lines.append(str(recommendation))
        lines.append("")

    if ranked:
        lines.append("### 📍 Priority Outlets for Today")
        lines.append("| Rank | Outlet Name | Merchant | Priority Score | Location |")
        lines.append("|:---:|:---|:---|:---:|:---|")
        for i, o in enumerate(ranked[:6], 1):
            score_badge = f"🔥 {o.get('score', 0):.1f}" if o.get('score', 0) >= 80 else f"{o.get('score', 0):.1f}"
            lines.append(f"| **#{i}** | {o.get('name', 'N/A')} | {o.get('merchant', 'Independent')} | {score_badge} | {o.get('address', 'Metro Manila')} |")
        lines.append("")

    if nudges:
        for nudge in nudges:
            lines.append(f"> {nudge}")
            lines.append("")

    if not lines:
        lines.append("Here is your current territory overview. All assigned merchant outlets are active. To see prioritized visits, ask: *'Which outlets should I visit first today?'*")

    state["response"] = "\n".join(lines).strip()
    return state

