from sqlalchemy import select, desc
from agents.state import AgentState
from app.aws.xray_helpers import trace
from app.db.session import AsyncSessionLocal
from app.models.outlet import Outlet
from app.models.score import OutletScore
from app.models.merchant import Merchant
from app.models.transaction import Transaction
from app.models.action import ActionRecommendation

@trace("profile_node")
async def profile_node(state: AgentState) -> AgentState:
    outlet_id = state.get("outlet_id")
    user_query = state.get("user_query", "").lower()

    async with AsyncSessionLocal() as db:
        query = (
            select(Outlet, Merchant, OutletScore.priority_score, OutletScore.contributing_factors)
            .outerjoin(Merchant, Outlet.merchant_id == Merchant.id)
            .outerjoin(OutletScore, Outlet.id == OutletScore.outlet_id)
        )
        
        if outlet_id:
            query = query.where(Outlet.id == outlet_id)
        else:
            if "makati" in user_query:
                query = query.where(Outlet.outlet_name.ilike("%makati%"))
            elif "quezon" in user_query:
                query = query.where(Outlet.outlet_name.ilike("%quezon%"))
            elif "eastwood" in user_query:
                query = query.where(Outlet.outlet_name.ilike("%eastwood%"))
            elif "aling nena" in user_query or "nena" in user_query or "taguig" in user_query:
                query = query.where(Outlet.outlet_name.ilike("%nena%"))
            elif "cebu" in user_query:
                query = query.where(Outlet.outlet_name.ilike("%cebu%"))
            elif "puregold" in user_query:
                query = query.where(Outlet.outlet_name.ilike("%puregold%"))
            elif "7-eleven" in user_query or "7 eleven" in user_query or "convenience" in user_query:
                query = query.where(Outlet.outlet_name.ilike("%7-eleven%"))
            else:
                # Default to highest priority store
                query = query.order_by(OutletScore.priority_score.desc().nullslast())
                
        result = await db.execute(query.limit(1))
        row = result.first()
        
        if row:
            outlet, merchant, score, factors = row
            state["outlet_id"] = str(outlet.id)
            
            # Fetch recent transactions
            txns_res = await db.execute(
                select(Transaction)
                .where(Transaction.outlet_id == outlet.id)
                .order_by(desc(Transaction.txn_date))
                .limit(3)
            )
            txns = txns_res.scalars().all()
            
            # Fetch pending actions
            acts_res = await db.execute(
                select(ActionRecommendation)
                .where(ActionRecommendation.outlet_id == outlet.id)
                .limit(3)
            )
            actions = acts_res.scalars().all()

            state["outlet_data"] = {
                "profile": {
                    "id": str(outlet.id),
                    "name": outlet.outlet_name,
                    "merchant": merchant.business_name if merchant else "Independent Merchant",
                    "owner": merchant.owner_name if merchant else "Verified Owner",
                    "business_type": merchant.business_type if merchant else (outlet.outlet_type or "Retail"),
                    "kyc_status": merchant.kyc_status if merchant else "verified",
                    "risk_tier": merchant.risk_tier if merchant else "low",
                    "city": outlet.city or "Metro Manila",
                    "status": outlet.status or "active",
                    "address": outlet.address or ""
                },
                "score": float(score) if score else 0.0,
                "factors": factors or ["declining_volume"],
                "recent_transactions": [
                    {"amount": float(t.amount), "type": t.txn_type, "status": t.status}
                    for t in txns
                ],
                "pending_actions": [
                    {"type": a.action_type, "detail": a.action_detail, "priority": a.priority}
                    for a in actions
                ]
            }
        else:
            state["outlet_data"] = {}
            
    return state


