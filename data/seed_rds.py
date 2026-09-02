import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from app.db.models import Base, User, Merchant, Interaction, CoachingBrief
from app.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_rds():
    print(f"Connecting to {settings.database_url}")
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Seed users
        admin_id = uuid.uuid4()
        dsp_id = uuid.uuid4()
        manager_id = uuid.uuid4()
        
        users = [
            User(id=admin_id, username="admin_user", hashed_password=pwd_context.hash("admin123"), role="admin"),
            User(id=dsp_id, username="dsp_user", hashed_password=pwd_context.hash("dsp123"), role="dsp"),
            User(id=manager_id, username="manager_user", hashed_password=pwd_context.hash("manager123"), role="manager"),
        ]
        session.add_all(users)
        
        # Seed merchants
        merchant_id1 = uuid.uuid4()
        merchant_id2 = uuid.uuid4()
        merchants = [
            Merchant(
                id=merchant_id1,
                name="Store A",
                business_type="Retail",
                location="Manila",
                status="Active",
                metrics={"mrr": 5000, "churn_risk": "low"}
            ),
            Merchant(
                id=merchant_id2,
                name="Store B",
                business_type="Food",
                location="Makati",
                status="Inactive",
                metrics={"mrr": 1000, "churn_risk": "high"}
            )
        ]
        session.add_all(merchants)
        await session.commit()
        
        print("Database seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_rds())
