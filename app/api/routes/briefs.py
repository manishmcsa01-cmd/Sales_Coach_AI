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

@router.get("/summary/area", response_model=AreaSummaryResponse,
            dependencies=[Depends(require_role(["manager", "admin", "dsp"]))])
async def get_area_summary(user: UserClaims = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get area-level summary stats from real database."""
    # Count outlets by status
    total_q = await db.execute(select(func.count(Outlet.id)))
    total = total_q.scalar() or 0

    active_q = await db.execute(select(func.count(Outlet.id)).where(Outlet.status == "active"))
    active = active_q.scalar() or 0

    churned_q = await db.execute(select(func.count(Outlet.id)).where(Outlet.status == "churned"))
    churned = churned_q.scalar() or 0

    inactive_q = await db.execute(select(func.count(Outlet.id)).where(Outlet.status == "inactive"))
    inactive = inactive_q.scalar() or 0

    # Average score
    avg_q = await db.execute(select(func.avg(OutletScore.priority_score)))
    avg_score = avg_q.scalar() or 0

    # Top issues (most common contributing factors)
    at_risk = churned + inactive

    return AreaSummaryResponse(
        area_name="All Areas",
        total_outlets=total,
        active_count=active,
        at_risk_count=at_risk,
        avg_score=round(float(avg_score), 1),
        top_issues=[
            f"{churned} churned outlets",
            f"{inactive} inactive outlets",
            f"Average priority score: {round(float(avg_score), 1)}"
        ]
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
