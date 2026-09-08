import json
from agents.state import AgentState
from app.aws.bedrock_client import bedrock_client
from app.config import get_settings
from app.aws.xray_helpers import trace

@trace("brief_node")
def brief_node(state: AgentState) -> AgentState:
    outlet_data = state.get("outlet_data", {})
    settings = get_settings()
    
    profile = outlet_data.get("profile", {}) if outlet_data else {}
    name = profile.get("name", "Target Store")
    merchant = profile.get("merchant", "Independent Merchant")
    owner = profile.get("owner", "Store Manager")
    kyc = profile.get("kyc_status", "verified").capitalize()
    risk = profile.get("risk_tier", "low").upper()
    city = profile.get("city", "Metro Manila")
    address = profile.get("address", "")
    score = outlet_data.get("score", 0.0) if outlet_data else 0.0
    factors = outlet_data.get("factors", [])
    factors_fmt = ", ".join([f.replace("_", " ").title() for f in factors]) if factors else "High volume potential"
    txns = outlet_data.get("recent_transactions", [])
    actions = outlet_data.get("pending_actions", [])

    try:
        system_prompt = (
            "You are Sales Coach AI. Generate an executive store briefing based on the outlet, merchant profile, and transaction history. "
            "Highlight merchant background, priority score, risk factors, and clear visit objectives."
        )
        response = bedrock_client.invoke_model(
            model_id=settings.bedrock_model_id,
            system_prompt=system_prompt,
            user_message=json.dumps(outlet_data or {"name": name, "city": city, "score": score})
        )
        if getattr(settings, "bedrock_guardrail_id", None):
            try:
                gr_res = bedrock_client.apply_guardrail(settings.bedrock_guardrail_id, response)
                response = gr_res.get("filtered_text", response)
            except Exception:
                pass
        if response and len(response.strip()) > 20:
            state["brief"] = response.strip()
            return state
    except Exception:
        pass

    # High-quality structured fallback
    lines = [
        f"### 🏪 Store Briefing: {name}",
        f"- **Merchant Network**: {merchant} *(Owner: {owner} | KYC: {kyc} | Risk Tier: {risk})*",
        f"- **Location**: {address or city}",
        f"- **Priority AI Score**: **{score:.1f} / 100**",
        f"- **Key Contributing Factors**: {factors_fmt}",
    ]

    if txns:
        tx_str = ", ".join([f"₱{t['amount']:,.2f} ({t['type']})" for t in txns[:2]])
        lines.append(f"- **Recent Transactions**: {tx_str}")

    if actions:
        act_str = "; ".join([f"{a['type']} ({a['detail']})" for a in actions[:2]])
        lines.append(f"- **Pending Recommended Actions**: {act_str}")

    lines.append(f"- **Field Objective**: Position Scan-to-Pay QR standees at primary checkout counters and ensure cashier familiarity with QR refunds.")

    state["brief"] = "\n".join(lines)
    return state


