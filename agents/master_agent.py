from agents.state import AgentState
from app.aws.xray_helpers import trace

@trace("master_node")
def master_node(state: AgentState) -> AgentState:
    intent = state.get("intent")
    if "metadata" not in state or not isinstance(state["metadata"], dict):
        state["metadata"] = {"chain": []}
    if "chain" not in state["metadata"]:
        state["metadata"]["chain"] = []
        
    chain = state["metadata"]["chain"]
    if len(chain) > 8:
        # Loop prevention: terminate at nl_response
        state["next_agent"] = "nl_response"
        return state

    if not intent:
        state["next_agent"] = "intent"
    elif intent == "get_priority_list":
        if not state.get("ranked_outlets"):
            state["next_agent"] = "ranking"
        elif "nudges" not in state.get("metadata", {}):
            state["next_agent"] = "nudge"
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
        if not state.get("ranked_outlets") and not state.get("outlet_data"):
            state["next_agent"] = "ranking"
        else:
            state["next_agent"] = "nl_response"
    elif intent == "unclear":
        state["next_agent"] = "clarification"
    else:
        state["next_agent"] = "nl_response"

    state["metadata"]["chain"].append(f"master->{state['next_agent']}")
    return state

