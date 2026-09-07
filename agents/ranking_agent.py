from sqlalchemy import select, desc
from agents.state import AgentState
from app.aws.xray_helpers import trace
from app.db.session import AsyncSessionLocal
from app.models.outlet import Outlet
from app.models.score import OutletScore
from app.models.assignment import DspOutletAssignment
from app.models.merchant import Merchant

@trace("ranking_node")
async def ranking_node(state: AgentState) -> AgentState:
    dsp_id = state.get("dsp_id")
    
    async with AsyncSessionLocal() as db:
        query = (
            select(Outlet, Merchant.business_name, OutletScore.priority_score, OutletScore.contributing_factors)
            .outerjoin(Merchant, Outlet.merchant_id == Merchant.id)
            .outerjoin(OutletScore, Outlet.id == OutletScore.outlet_id)
        )
        
        if dsp_id:
            query = query.join(DspOutletAssignment, Outlet.id == DspOutletAssignment.outlet_id).where(DspOutletAssignment.dsp_id == dsp_id)
            
        query = query.order_by(desc(OutletScore.priority_score)).limit(10)
        
        result = await db.execute(query)
        rows = result.all()
        
        if not rows and dsp_id:
            # Fallback to general territory outlets if no direct assignments
            query_all = (
                select(Outlet, Merchant.business_name, OutletScore.priority_score, OutletScore.contributing_factors)
                .outerjoin(Merchant, Outlet.merchant_id == Merchant.id)
                .outerjoin(OutletScore, Outlet.id == OutletScore.outlet_id)
                .order_by(desc(OutletScore.priority_score)).limit(10)
            )
            result = await db.execute(query_all)
            rows = result.all()
        
        ranked_outlets = []
        for outlet, m_name, score, factors in rows:
            ranked_outlets.append({
                "id": str(outlet.id),
                "name": outlet.outlet_name,
                "merchant": m_name or "Independent",
                "score": float(score) if score else 0.0,
                "factors": factors or [],
                "address": f"{outlet.address or ''}, {outlet.city or ''}".strip(", ")
            })
            
        state["ranked_outlets"] = ranked_outlets
            
    return state


