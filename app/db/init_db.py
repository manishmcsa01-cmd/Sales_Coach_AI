import logging
import uuid
from datetime import date, datetime
from sqlalchemy import select, func
from app.db.session import engine, AsyncSessionLocal
from app.models import Base
from app.models.area import Area
from app.models.merchant import Merchant
from app.models.dsp import Dsp
from app.models.outlet import Outlet
from app.models.score import OutletScore
from app.models.transaction import Transaction
from app.models.visit_log import VisitLog
from app.models.user import UserAccount

logger = logging.getLogger(__name__)

async def seed_data_if_empty():
    """Seed initial sample data if the database is empty."""
    async with AsyncSessionLocal() as session:
        try:
            area_count = await session.scalar(select(func.count(Area.id)))
            if area_count and area_count > 0:
                logger.info("Database already contains data, skipping seed.")
                return

            logger.info("Database is empty. Populating initial sample data...")

            # 1. Areas
            north = Area(id=uuid.uuid4(), area_name="Metro Manila North", region="NCR")
            south = Area(id=uuid.uuid4(), area_name="Metro Manila South", region="NCR")
            cebu = Area(id=uuid.uuid4(), area_name="Cebu Central", region="Visayas")
            session.add_all([north, south, cebu])
            await session.flush()

            # 2. DSPs
            dsp1 = Dsp(
                id=uuid.uuid4(),
                name="Juan Dela Cruz",
                email="dsp@test.com",
                role="dsp",
                area_id=north.id,
                status="active",
                hire_date=date(2023, 1, 15)
            )
            dsp2 = Dsp(
                id=uuid.uuid4(),
                name="Maria Santos",
                email="manager@test.com",
                role="manager",
                area_id=south.id,
                status="active",
                hire_date=date(2022, 5, 10)
            )
            dsp3 = Dsp(
                id=uuid.uuid4(),
                name="Pedro Reyes",
                email="admin@salescoach.com",
                role="admin",
                area_id=cebu.id,
                status="active",
                hire_date=date(2021, 3, 20)
            )
            session.add_all([dsp1, dsp2, dsp3])
            await session.flush()

            # 3. Merchants
            m1 = Merchant(
                id=uuid.uuid4(),
                business_name="Puregold Price Club",
                owner_name="Lucio Co",
                business_type="Supermarket",
                kyc_status="verified",
                risk_tier="low"
            )
            m2 = Merchant(
                id=uuid.uuid4(),
                business_name="7-Eleven Convenience",
                owner_name="Philippine Seven Corp",
                business_type="Convenience",
                kyc_status="verified",
                risk_tier="low"
            )
            m3 = Merchant(
                id=uuid.uuid4(),
                business_name="Aling Nena Sari-Sari Store",
                owner_name="Elena Bautista",
                business_type="Retail",
                kyc_status="verified",
                risk_tier="medium"
            )
            session.add_all([m1, m2, m3])
            await session.flush()

            # 4. Outlets
            o1 = Outlet(
                id=uuid.uuid4(),
                merchant_id=m1.id,
                outlet_name="Puregold Quezon Ave",
                address="Quezon Ave cor Timog",
                city="Quezon City",
                region="NCR",
                outlet_type="Supermarket",
                status="active",
                area_id=north.id
            )
            o2 = Outlet(
                id=uuid.uuid4(),
                merchant_id=m2.id,
                outlet_name="7-Eleven Eastwood",
                address="Eastwood City Cyberpark",
                city="Quezon City",
                region="NCR",
                outlet_type="Convenience",
                status="active",
                area_id=north.id
            )
            o3 = Outlet(
                id=uuid.uuid4(),
                merchant_id=m1.id,
                outlet_name="Puregold Makati",
                address="Chino Roces Ave",
                city="Makati",
                region="NCR",
                outlet_type="Supermarket",
                status="active",
                area_id=south.id
            )
            o4 = Outlet(
                id=uuid.uuid4(),
                merchant_id=m3.id,
                outlet_name="Aling Nena Store Taguig",
                address="Signal Village",
                city="Taguig",
                region="NCR",
                outlet_type="Sari-Sari",
                status="active",
                area_id=south.id
            )
            o5 = Outlet(
                id=uuid.uuid4(),
                merchant_id=m2.id,
                outlet_name="7-Eleven Cebu IT Park",
                address="Salinas Dr Lahug",
                city="Cebu City",
                region="Visayas",
                outlet_type="Convenience",
                status="active",
                area_id=cebu.id
            )
            session.add_all([o1, o2, o3, o4, o5])
            await session.flush()

            # 5. Outlet Priority Scores
            s1 = OutletScore(
                id=uuid.uuid4(),
                outlet_id=o1.id,
                priority_score=88.5,
                contributing_factors=["declining_volume", "high_potential"],
                score_date=date.today(),
                model_version="v1.0"
            )
            s2 = OutletScore(
                id=uuid.uuid4(),
                outlet_id=o2.id,
                priority_score=72.0,
                contributing_factors=["churn_risk"],
                score_date=date.today(),
                model_version="v1.0"
            )
            s3 = OutletScore(
                id=uuid.uuid4(),
                outlet_id=o3.id,
                priority_score=94.0,
                contributing_factors=["dormant_merchant", "high_volume"],
                score_date=date.today(),
                model_version="v1.0"
            )
            s4 = OutletScore(
                id=uuid.uuid4(),
                outlet_id=o4.id,
                priority_score=45.0,
                contributing_factors=["stable_activity"],
                score_date=date.today(),
                model_version="v1.0"
            )
            s5 = OutletScore(
                id=uuid.uuid4(),
                outlet_id=o5.id,
                priority_score=60.0,
                contributing_factors=["new_merchant"],
                score_date=date.today(),
                model_version="v1.0"
            )
            session.add_all([s1, s2, s3, s4, s5])

            # 5. DSP Outlet Assignments
            from app.models.assignment import DspOutletAssignment
            as1 = DspOutletAssignment(id=uuid.uuid4(), dsp_id=dsp1.id, outlet_id=o1.id, assigned_date=date.today())
            as2 = DspOutletAssignment(id=uuid.uuid4(), dsp_id=dsp1.id, outlet_id=o2.id, assigned_date=date.today())
            as3 = DspOutletAssignment(id=uuid.uuid4(), dsp_id=dsp2.id, outlet_id=o3.id, assigned_date=date.today())
            as4 = DspOutletAssignment(id=uuid.uuid4(), dsp_id=dsp2.id, outlet_id=o4.id, assigned_date=date.today())
            as5 = DspOutletAssignment(id=uuid.uuid4(), dsp_id=dsp3.id, outlet_id=o5.id, assigned_date=date.today())
            session.add_all([as1, as2, as3, as4, as5])

            # 6. Action Recommendations
            from app.models.action import ActionRecommendation
            act1 = ActionRecommendation(id=uuid.uuid4(), outlet_id=o1.id, dsp_id=dsp1.id, action_type="Merchandising Audit", action_detail="Replace damaged GCash QR tent cards and stickers", priority="HIGH", status="pending")
            act2 = ActionRecommendation(id=uuid.uuid4(), outlet_id=o3.id, dsp_id=dsp2.id, action_type="Cash-In Training", action_detail="Train store clerk on Cash-In limit updates", priority="CRITICAL", status="pending")
            act3 = ActionRecommendation(id=uuid.uuid4(), outlet_id=o2.id, dsp_id=dsp1.id, action_type="POS Health Check", action_detail="Diagnose barcode scanner connectivity errors", priority="MEDIUM", status="completed")
            session.add_all([act1, act2, act3])

            # 7. Transactions
            now = datetime.utcnow()
            t1 = Transaction(id=uuid.uuid4(), outlet_id=o1.id, txn_type="QR_PAYMENT", amount=1500.0, txn_date=now, status="SUCCESS")
            t2 = Transaction(id=uuid.uuid4(), outlet_id=o2.id, txn_type="CASH_IN", amount=500.0, txn_date=now, status="SUCCESS")
            t3 = Transaction(id=uuid.uuid4(), outlet_id=o3.id, txn_type="BILL_PAY", amount=2300.0, txn_date=now, status="SUCCESS")
            t4 = Transaction(id=uuid.uuid4(), outlet_id=o4.id, txn_type="QR_PAYMENT", amount=250.0, txn_date=now, status="SUCCESS")
            t5 = Transaction(id=uuid.uuid4(), outlet_id=o5.id, txn_type="QR_PAYMENT", amount=890.0, txn_date=now, status="SUCCESS")
            session.add_all([t1, t2, t3, t4, t5])

            # 8. Visits
            v1 = VisitLog(id=uuid.uuid4(), dsp_id=dsp1.id, outlet_id=o1.id, visit_date=now, visit_type="SCHEDULED", outcome="COMPLETED", notes="Marketing collaterals replaced", duration_minutes=25)
            v2 = VisitLog(id=uuid.uuid4(), dsp_id=dsp2.id, outlet_id=o3.id, visit_date=now, visit_type="AD_HOC", outcome="COMPLETED", notes="Assisted with QR scanner issue", duration_minutes=15)
            session.add_all([v1, v2])

            # 9. User Accounts
            u1 = UserAccount(id=uuid.uuid4(), email="admin@salescoach.com", password_hash="managed_by_cognito", role="admin", status="active", last_login=now)
            u2 = UserAccount(id=uuid.uuid4(), email="manager@salescoach.com", password_hash="managed_by_cognito", role="manager", status="active", last_login=now)
            u3 = UserAccount(id=uuid.uuid4(), email="dsp@salescoach.com", password_hash="managed_by_cognito", role="dsp", status="active", last_login=now)
            session.add_all([u1, u2, u3])

            await session.commit()
            logger.info("Successfully seeded database with initial sample data!")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error seeding database: {e}")

async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Successfully created all database tables.")
        await seed_data_if_empty()
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
