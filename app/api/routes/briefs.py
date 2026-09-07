from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.brief import BriefResponse, AreaSummaryResponse
from app.api.dependencies import get_db, get_current_user
from app.schemas.auth import UserClaims
from app.middleware.rbac import require_role
from app.models.outlet import Outlet
from app.models.score import OutletScore
from app.models.merchant import Merchant
from datetime import datetime

router = APIRouter()

from app.models.area import Area
from app.models.dsp import Dsp

@router.get("/summary/area", response_model=AreaSummaryResponse,
            dependencies=[Depends(require_role(["manager", "admin", "dsp"]))])
async def get_area_summary(user: UserClaims = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get area-level summary stats from real database with role-based scoping."""
    area_id = user.area_id
    area_name = "All Areas"
    
    if (user.role or "").lower() == "manager":
        # Resolve manager's area
        if not area_id:
            email = user.email or "manager@salescoach.com"
            manager_dsp = await db.scalar(select(Dsp).where(Dsp.email == email))
            if manager_dsp and manager_dsp.area_id:
                area_id = manager_dsp.area_id
            else:
                mgr = await db.scalar(select(Dsp).where(Dsp.role == "manager"))
                if mgr and mgr.area_id:
                    area_id = mgr.area_id
                else:
                    area_id = await db.scalar(select(Area.id).limit(1))
        
        if area_id:
            a_obj = await db.scalar(select(Area).where(Area.id == area_id))
            if a_obj:
                area_name = a_obj.area_name

    # Queries
    total_q = select(func.count(Outlet.id))
    active_q = select(func.count(Outlet.id)).where(Outlet.status == "active")
    churned_q = select(func.count(Outlet.id)).where(Outlet.status == "churned")
    inactive_q = select(func.count(Outlet.id)).where(Outlet.status.in_(["inactive", "at_risk"]))
    avg_q = select(func.avg(OutletScore.priority_score)).select_from(Outlet).outerjoin(OutletScore, Outlet.id == OutletScore.outlet_id)

    if area_id and (user.role or "").lower() == "manager":
        total_q = total_q.where(Outlet.area_id == area_id)
        active_q = active_q.where(Outlet.area_id == area_id)
        churned_q = churned_q.where(Outlet.area_id == area_id)
        inactive_q = inactive_q.where(Outlet.area_id == area_id)
        avg_q = avg_q.where(Outlet.area_id == area_id)

    total = (await db.execute(total_q)).scalar() or 0
    active = (await db.execute(active_q)).scalar() or 0
    churned = (await db.execute(churned_q)).scalar() or 0
    inactive = (await db.execute(inactive_q)).scalar() or 0
    avg_score = (await db.execute(avg_q)).scalar() or 0.0

    at_risk = churned + inactive

    # Build rich key issues list
    top_issues = []
    if churned > 0:
        top_issues.append(f"{churned} churned outlets requiring retention follow-up")
    if inactive > 0:
        top_issues.append(f"{inactive} at-risk / inactive outlets needing immediate field visit")
    top_issues.append(f"Average territory priority score: {round(float(avg_score), 1)} / 100")
    top_issues.append("Monitor QR acceptance and transaction velocity for high-scoring merchants")
    top_issues.append("Ensure Scan-to-Pay collaterals and standees are visibly placed at counters")

    return AreaSummaryResponse(
        area_name=area_name,
        total_outlets=total,
        active_count=active,
        at_risk_count=at_risk,
        avg_score=round(float(avg_score), 1),
        top_issues=top_issues
    )


@router.get("/{outlet_id}", response_model=BriefResponse)
async def get_brief(outlet_id: str, user: UserClaims = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get AI brief for a specific outlet."""
    query = (
        select(Outlet, Merchant.business_name, OutletScore.priority_score, OutletScore.contributing_factors)
        .outerjoin(Merchant, Outlet.merchant_id == Merchant.id)
        .outerjoin(OutletScore, Outlet.id == OutletScore.outlet_id)
        .where(Outlet.id == outlet_id)
    )
    result = await db.execute(query)
    row = result.first()

    if row:
        outlet, merchant_name, score, factors = row
        factors_list = factors if factors else []
        brief = (
            f"**{outlet.outlet_name}** ({merchant_name})\n\n"
            f"📍 {outlet.address}, {outlet.city}\n"
            f"📊 Priority Score: {round(score, 1) if score else 'N/A'}/100\n"
            f"📋 Status: {outlet.status}\n\n"
            f"**Key Factors:** {', '.join(str(f) for f in factors_list) if factors_list else 'None'}\n\n"
            f"**Recommendation:** Based on the priority score, "
            f"{'immediate attention needed — schedule a visit today.' if score and score > 70 else 'routine check — maintain regular contact.' if score and score > 40 else 'low priority — focus on higher-risk outlets first.'}"
        )
        return BriefResponse(
            outlet_id=outlet_id,
            outlet_name=outlet.outlet_name or "Unknown",
            brief_text=brief,
            generated_at=datetime.utcnow(),
            is_cached=False
        )

    return BriefResponse(
        outlet_id=outlet_id,
        outlet_name="Not Found",
        brief_text="Outlet not found in the database.",
        generated_at=datetime.utcnow(),
        is_cached=False
    )
