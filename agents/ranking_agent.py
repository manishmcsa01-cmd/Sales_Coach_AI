from sqlalchemy import select
from agents.state import AgentState
from app.aws.xray_helpers import trace
from app.db.session import AsyncSessionLocal
from app.models.outlet import Outlet
from app.models.score import OutletScore

@trace("ranking_node")
async def ranking_node(state: AgentState) -> AgentState:
    dsp_id = state.get("dsp_id")
    
    async with AsyncSessionLocal() as db:
        query = select(Outlet, OutletScore.priority_score).outerjoin(OutletScore, Outlet.id == OutletScore.outlet_id)
        
        # dsp_id is currently not heavily enforced if we want full list, but good to filter if present
        if dsp_id:
            query = query.where(Outlet.dsp_id == dsp_id)
            
        query = query.order_by(OutletScore.priority_score.desc().nullslast()).limit(10)
        
        result = await db.execute(query)
        rows = result.all()
        
        ranked_outlets = []
        for outlet, score in rows:
            ranked_outlets.append({
                "id": outlet.id,
                "name": outlet.outlet_name,
                "score": score
            })
            
        state["ranked_outlets"] = ranked_outlets
            
    return state
