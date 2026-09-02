from fastapi import APIRouter, Depends
from typing import List
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.outlet import OutletResponse, OutletListResponse
from app.api.dependencies import get_db, get_current_user
from app.schemas.auth import UserClaims
from app.models.outlet import Outlet
from app.models.merchant import Merchant
from app.models.score import OutletScore
from app.models.assignment import DspOutletAssignment

router = APIRouter()

@router.get("", response_model=OutletListResponse)
async def get_outlets(user: UserClaims = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get ranked outlet list for the current user."""
    # Query outlets with scores, joined to merchants
    query = (
        select(Outlet, Merchant.business_name, OutletScore.priority_score, OutletScore.contributing_factors)
        .outerjoin(Merchant, Outlet.merchant_id == Merchant.id)
        .outerjoin(OutletScore, Outlet.id == OutletScore.outlet_id)
        .order_by(OutletScore.priority_score.desc().nullslast())
        .limit(50)
    )

    result = await db.execute(query)
    rows = result.all()

    outlets = []
    for outlet, merchant_name, score, factors in rows:
        outlets.append(OutletResponse(
            outlet_id=str(outlet.id),
            outlet_name=outlet.outlet_name or "Unknown",
            merchant_name=merchant_name or "Unknown",
            outlet_type=outlet.outlet_type or "unknown",
            status=outlet.status or "active",
            priority_score=round(score, 1) if score else 0.0,
            contributing_factors=factors if factors else [],
            address=outlet.address or "",
            city=outlet.city or ""
        ))

    return OutletListResponse(
        outlets=outlets,
        total=len(outlets),
        date=datetime.utcnow()
    )

@router.get("/{outlet_id}", response_model=OutletResponse)
async def get_outlet(outlet_id: str, user: UserClaims = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get a single outlet detail."""
    query = (
        select(Outlet, Merchant.business_name, OutletScore.priority_score, OutletScore.contributing_factors)
        .outerjoin(Merchant, Outlet.merchant_id == Merchant.id)
        .outerjoin(OutletScore, Outlet.id == OutletScore.outlet_id)
        .where(Outlet.id == outlet_id)
    )
    result = await db.execute(query)
    row = result.first()

    if not row:
        return OutletResponse(
            outlet_id=outlet_id, outlet_name="Not Found", merchant_name="",
            outlet_type="", status="unknown", priority_score=0, contributing_factors=[],
            address="", city=""
        )

    outlet, merchant_name, score, factors = row
    return OutletResponse(
        outlet_id=str(outlet.id),
        outlet_name=outlet.outlet_name or "Unknown",
        merchant_name=merchant_name or "Unknown",
        outlet_type=outlet.outlet_type or "unknown",
        status=outlet.status or "active",
        priority_score=round(score, 1) if score else 0.0,
        contributing_factors=factors if factors else [],
        address=outlet.address or "",
        city=outlet.city or ""
    )
