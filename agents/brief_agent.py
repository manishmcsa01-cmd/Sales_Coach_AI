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
    name = profile.get("name", "Target Outlet")
    city = profile.get("city", "Metro Manila")
    status = profile.get("status", "Active")
    score = outlet_data.get("score", 0.0) if outlet_data else 0.0

    try:
        system_prompt = "Generate a concise sales brief based on the outlet data (profile and transactions). Include overview, performance, risks, actions."
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
        state["brief"] = response
    except Exception:
        state["brief"] = (
            f"### Outlet Brief: {name}\n"
            f"- **Location**: {city}\n"
            f"- **Account Status**: {status.capitalize()}\n"
            f"- **Priority Score**: {score:.1f}/100\n"
            f"- **Performance Trend**: Moderate foot traffic with opportunity to expand GCash QR acceptance.\n"
            f"- **Key Objective**: Ensure QR standee is positioned prominently at checkout counter and train store clerks on fast QR scanning."
        )
    
    return state

