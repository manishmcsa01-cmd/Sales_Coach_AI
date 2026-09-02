from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from typing import List, Dict, Any

from app.api.dependencies import get_db, get_current_user
from app.schemas.auth import UserClaims
from app.models.outlet import Outlet
from app.models.dsp import Dsp
from app.models.transaction import Transaction
from app.models.area import Area
from app.models.score import OutletScore
from app.models.user import UserAccount
from app.models.visit_log import VisitLog

router = APIRouter()

@router.get("/dashboard")
async def admin_dashboard(
    current_user: UserClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    total_areas = await db.scalar(select(func.count(Area.id))) or 0
    total_outlets = await db.scalar(select(func.count(Outlet.id))) or 0
    total_dsps = await db.scalar(select(func.count(Dsp.id))) or 0
    total_merchants = await db.scalar(select(func.count(distinct(Outlet.merchant_id)))) or 0
    total_transactions = await db.scalar(select(func.count(Transaction.id))) or 0
    total_visits = await db.scalar(select(func.count(VisitLog.id))) or 0
    
    areas_res = await db.execute(select(Area))
    areas_list = areas_res.scalars().all()
    areas_data = []
    
    for a in areas_list:
        outlet_count = await db.scalar(select(func.count(Outlet.id)).where(Outlet.area_id == a.id)) or 0
        avg_score = await db.scalar(
            select(func.avg(OutletScore.priority_score))
            .join(Outlet, Outlet.id == OutletScore.outlet_id)
            .where(Outlet.area_id == a.id)
        ) or 0.0
        areas_data.append({
            "name": a.area_name,
            "outlet_count": outlet_count,
            "avg_score": float(avg_score)
        })
        
    return {
        "total_areas": total_areas,
        "total_outlets": total_outlets,
        "total_dsps": total_dsps,
        "total_merchants": total_merchants,
        "total_transactions": total_transactions,
        "total_visits": total_visits,
        "areas": areas_data
    }

@router.get("/users")
async def admin_users(
    current_user: UserClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(select(UserAccount))
    users = result.scalars().all()
    
    return [
        {
            "user_id": u.id,
            "email": u.email,
            "role": u.role,
            "status": u.status,
            "last_login": u.last_login.isoformat() if u.last_login else None
        }
        for u in users
    ]

@router.get("/health")
async def admin_health(
    current_user: UserClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    outlets_c = await db.scalar(select(func.count(Outlet.id))) or 0
    dsps_c = await db.scalar(select(func.count(Dsp.id))) or 0
    txns_c = await db.scalar(select(func.count(Transaction.id))) or 0
    users_c = await db.scalar(select(func.count(UserAccount.id))) or 0
    scores_c = await db.scalar(select(func.count(OutletScore.id))) or 0
    
    tables = [
        {"name": "outlets", "count": outlets_c},
        {"name": "dsps", "count": dsps_c},
        {"name": "transactions", "count": txns_c},
        {"name": "users", "count": users_c},
        {"name": "scores", "count": scores_c},
    ]
    
    # get latest score
    latest_score = await db.execute(
        select(OutletScore).order_by(OutletScore.score_date.desc()).limit(1)
    )
    score_obj = latest_score.scalars().first()
    
    scoring_model_version = score_obj.model_version if score_obj and score_obj.model_version else "v1.0"
    last_score_date = score_obj.score_date.isoformat() if score_obj and score_obj.score_date else "N/A"
    
    return {
        "tables": tables,
        "scoring_model_version": scoring_model_version,
        "last_score_date": last_score_date,
        "db_size_mb": 150 # Dummy value
    }
