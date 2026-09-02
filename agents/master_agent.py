from agents.state import AgentState
from app.aws.xray_helpers import trace

@trace("master_node")
def master_node(state: AgentState) -> AgentState:
    intent = state.get("intent")
    
    if not intent:
        state["next_agent"] = "intent"
    elif intent == "get_priority_list":
        if not state.get("ranked_outlets"):
            state["next_agent"] = "ranking"
        else:
            state["next_agent"] = "nl_response"
    elif intent == "get_brief":
        if not state.get("outlet_data"):
            state["next_agent"] = "profile"
        elif not state.get("brief"):
            state["next_agent"] = "brief"
        else:
            state["next_agent"] = "nl_response"
    elif intent == "get_recommendation":
        if not state.get("outlet_data"):
            state["next_agent"] = "profile"
        elif not state.get("recommendation"):
            state["next_agent"] = "recommendation"
        else:
            state["next_agent"] = "nl_response"
    elif intent == "ask_question":
        state["next_agent"] = "nl_response"
    elif intent == "unclear":
        state["next_agent"] = "clarification"
    else:
        state["next_agent"] = "nl_response"

    state["metadata"]["chain"].append(f"master->{state['next_agent']}")
    return state
