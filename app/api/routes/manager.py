from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from datetime import datetime

from app.api.dependencies import get_db, get_current_user
from app.schemas.auth import UserClaims
from app.models.outlet import Outlet
from app.models.dsp import Dsp
from app.models.transaction import Transaction
from app.models.action import ActionRecommendation
from app.models.area import Area
from app.models.score import OutletScore
from app.models.visit_log import VisitLog
from app.models.assignment import DspOutletAssignment

router = APIRouter()

@router.get("/dashboard")
async def manager_dashboard(
    current_user: UserClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    area_id = current_user.area_id
    if not area_id:
        return {"error": "Manager has no assigned area"}

    # Area name
    area_name = await db.scalar(select(Area.area_name).where(Area.id == area_id)) or "Unknown Area"
    
    # Outlet counts
    total_outlets = await db.scalar(select(func.count(Outlet.id)).where(Outlet.area_id == area_id)) or 0
    active_count = await db.scalar(select(func.count(Outlet.id)).where(Outlet.area_id == area_id, Outlet.status == "active")) or 0
    at_risk_count = await db.scalar(select(func.count(Outlet.id)).where(Outlet.area_id == area_id, Outlet.status == "at_risk")) or 0
    
    # Avg Score
    avg_score = await db.scalar(
        select(func.avg(OutletScore.priority_score))
        .join(Outlet, Outlet.id == OutletScore.outlet_id)
        .where(Outlet.area_id == area_id)
    ) or 0.0

    # Total Transactions
    total_transactions = await db.scalar(
        select(func.count(Transaction.id))
        .join(Outlet, Outlet.id == Transaction.outlet_id)
        .where(Outlet.area_id == area_id)
    ) or 0
    
    # Total Visits this month
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_visits_this_month = await db.scalar(
        select(func.count(VisitLog.id))
        .join(Outlet, Outlet.id == VisitLog.outlet_id)
        .where(Outlet.area_id == area_id, VisitLog.visit_date >= current_month)
    ) or 0
    
    # DSP Count
    dsp_count = await db.scalar(select(func.count(Dsp.id)).where(Dsp.area_id == area_id)) or 0

    return {
        "area_name": area_name,
        "total_outlets": total_outlets,
        "active_count": active_count,
        "at_risk_count": at_risk_count,
        "avg_score": float(avg_score),
        "total_transactions": total_transactions,
        "total_visits_this_month": total_visits_this_month,
        "dsp_count": dsp_count
    }


@router.get("/dsps")
async def manager_dsps(
    current_user: UserClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    area_id = current_user.area_id
    
    # Get dsps in area
    result = await db.execute(select(Dsp).where(Dsp.area_id == area_id))
    dsps = result.scalars().all()
    
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    dsps_data = []
    for d in dsps:
        outlet_count = await db.scalar(
            select(func.count(DspOutletAssignment.outlet_id))
            .where(DspOutletAssignment.dsp_id == d.id)
        ) or 0
        
        visits = await db.scalar(
            select(func.count(VisitLog.id))
            .where(VisitLog.dsp_id == d.id, VisitLog.visit_date >= current_month)
        ) or 0
        
        actions_completed = await db.scalar(
            select(func.count(ActionRecommendation.id))
            .where(ActionRecommendation.dsp_id == d.id, ActionRecommendation.status == 'completed')
        ) or 0
        
        actions_total = await db.scalar(
            select(func.count(ActionRecommendation.id))
            .where(ActionRecommendation.dsp_id == d.id)
        ) or 0
        
        completion_rate = (actions_completed / actions_total * 100) if actions_total > 0 else 0.0
        
        dsps_data.append({
            "dsp_id": d.id,
            "name": d.name,
            "email": d.email,
            "outlet_count": outlet_count,
            "visits_this_month": visits,
            "actions_completed": actions_completed,
            "actions_total": actions_total,
            "completion_rate": completion_rate
        })
        
    return dsps_data
