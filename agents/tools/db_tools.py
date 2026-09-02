from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def get_outlet_profile(outlet_id: str, db: AsyncSession) -> dict:
    query = text("SELECT * FROM outlets WHERE outlet_id = :outlet_id")
    result = await db.execute(query, {"outlet_id": outlet_id})
    row = result.fetchone()
    return dict(row._mapping) if row else {}

async def get_ranked_outlets(dsp_id: str, date: str, db: AsyncSession) -> list:
    query = text('''
        SELECT o.outlet_id, o.name, s.score, s.factors, s.days_since_last_visit
        FROM outlets o
        JOIN outlet_scores s ON o.outlet_id = s.outlet_id
        WHERE o.dsp_id = :dsp_id AND s.date = :date
        ORDER BY s.score DESC
        LIMIT 10
    ''')
    result = await db.execute(query, {"dsp_id": dsp_id, "date": date})
    return [dict(row._mapping) for row in result.fetchall()]

async def get_transaction_summary(outlet_id: str, days: int, db: AsyncSession) -> dict:
    # Mocking transaction summary for brevity
    return {"total_tx": 100, "volume": 50000, "days": days}

async def get_visit_history(outlet_id: str, dsp_id: str, db: AsyncSession) -> list:
    return [{"date": "2023-10-01", "notes": "Good visit"}]

async def get_action_history(outlet_id: str, db: AsyncSession) -> list:
    return []

async def get_area_summary(area_id: str, db: AsyncSession) -> dict:
    return {"area_id": area_id, "total_outlets": 50, "avg_score": 75}
