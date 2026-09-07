from sqlalchemy import select
from agents.state import AgentState
from app.aws.xray_helpers import trace
from app.db.session import AsyncSessionLocal
from app.models.outlet import Outlet
from app.models.score import OutletScore

@trace("profile_node")
async def profile_node(state: AgentState) -> AgentState:
    outlet_id = state.get("outlet_id")
    async with AsyncSessionLocal() as db:
        query = select(Outlet, OutletScore.priority_score).outerjoin(OutletScore, Outlet.id == OutletScore.outlet_id)
        
        if outlet_id:
            query = query.where(Outlet.id == outlet_id)
        else:
            # Check if any merchant or outlet name is mentioned in user_query
            user_query = state.get("user_query", "").lower()
            if "makati" in user_query:
                query = query.where(Outlet.outlet_name.ilike("%makati%"))
            elif "quezon" in user_query:
                query = query.where(Outlet.outlet_name.ilike("%quezon%"))
            elif "eastwood" in user_query:
                query = query.where(Outlet.outlet_name.ilike("%eastwood%"))
            elif "cebu" in user_query:
                query = query.where(Outlet.outlet_name.ilike("%cebu%"))
            elif "aling nena" in user_query or "taguig" in user_query:
                query = query.where(Outlet.outlet_name.ilike("%nena%"))
            else:
                # Default to the highest priority outlet
                query = query.order_by(OutletScore.priority_score.desc().nullslast())
                
        result = await db.execute(query.limit(1))
        row = result.first()
        
        if row:
            outlet, score = row
            state["outlet_id"] = str(outlet.id)
            state["outlet_data"] = {
                "profile": {
                    "id": str(outlet.id),
                    "name": outlet.outlet_name,
                    "city": outlet.city or "Metro Manila",
                    "status": outlet.status or "active",
                    "address": outlet.address or ""
                },
                "score": float(score) if score else 0.0
            }
        else:
            state["outlet_data"] = {}
            
    return state

