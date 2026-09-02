from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.master_agent import master_node
from agents.intent_agent import intent_node
from agents.profile_agent import profile_node
from agents.ranking_agent import ranking_node
from agents.recommendation_agent import recommendation_node
from agents.brief_agent import brief_node
from agents.nudge_agent import nudge_node
from agents.nl_response_agent import nl_response_node
from agents.clarification_agent import clarification_node

def build_sales_coach_graph():
    graph = StateGraph(AgentState)
    
    graph.add_node("master", master_node)
    graph.add_node("intent", intent_node)
    graph.add_node("profile", profile_node)
    graph.add_node("ranking", ranking_node)
    graph.add_node("recommendation", recommendation_node)
    graph.add_node("brief", brief_node)
    graph.add_node("nudge", nudge_node)
    graph.add_node("nl_response", nl_response_node)
    graph.add_node("clarification", clarification_node)
    
    graph.set_entry_point("master")
    
    def get_next_node(state: AgentState) -> str:
        return state.get("next_agent") or "nl_response"
    
    nodes = ["intent", "profile", "ranking", "recommendation", "brief", "nudge"]
    for node in nodes:
        graph.add_edge(node, "master")
        
    graph.add_conditional_edges(
        "master",
        get_next_node,
        {
            "intent": "intent",
            "profile": "profile",
            "ranking": "ranking",
            "recommendation": "recommendation",
            "brief": "brief",
            "nudge": "nudge",
            "nl_response": "nl_response",
            "clarification": "clarification"
        }
    )
    
    graph.add_edge("nl_response", END)
    graph.add_edge("clarification", END)
    
    return graph.compile()

async def run_agent(query: str, tenant_context) -> AgentState:
    graph = build_sales_coach_graph()
    initial_state = AgentState(
        user_query=query,
        user_id=tenant_context.user_id,
        dsp_id=tenant_context.dsp_id,
        role=tenant_context.role,
        area_id=tenant_context.area_id,
        intent=None,
        outlet_id=None,
        outlet_data=None,
        ranked_outlets=None,
        recommendation=None,
        brief=None,
        response=None,
        conversation_history=[],
        error=None,
        next_agent=None,
        metadata={"chain": []}
    )
    result = await graph.ainvoke(initial_state)
    return result
