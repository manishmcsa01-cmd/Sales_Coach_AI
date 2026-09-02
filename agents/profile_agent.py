from sqlalchemy import select
from agents.state import AgentState
from app.aws.xray_helpers import trace
from app.db.session import AsyncSessionLocal
from app.models.outlet import Outlet
from app.models.score import OutletScore

@trace("profile_node")
async def profile_node(state: AgentState) -> AgentState:
    outlet_id = state.get("outlet_id")
    
    if not outlet_id:
        state["error"] = "No outlet_id provided for profile lookup."
        return state
        
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Outlet, OutletScore.priority_score)
            .outerjoin(OutletScore, Outlet.id == OutletScore.outlet_id)
            .where(Outlet.id == outlet_id)
        )
        row = result.first()
        
        if row:
            outlet, score = row
            state["outlet_data"] = {
                "profile": {
                    "id": outlet.id,
                    "name": outlet.outlet_name,
                    "city": outlet.city,
                    "status": outlet.status
                },
                "score": score or 0
            }
        else:
            state["outlet_data"] = {}
            
    return state
