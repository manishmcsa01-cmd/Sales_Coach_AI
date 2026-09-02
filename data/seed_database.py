import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from data.generators.users import UserGenerator
from data.generators.dsps import DSPGenerator
from data.generators.merchants import MerchantGenerator
from data.generators.products import ProductGenerator
from data.generators.transactions import TransactionGenerator
from data.generators.visits import VisitGenerator
from data.generators.scores import ScoreGenerator
from data.generators.actions import ActionGenerator
from data.generators.conversations import ConversationGenerator

async def seed_all():
    print("Generating users...")
    ug = UserGenerator()
    users = ug.generate_users(60)
    managers = [u["id"] for u in users if u["role"] == "manager"]
    dsp_users = [u["id"] for u in users if u["role"] == "dsp"]
    
    print("Generating DSPs and Areas...")
    dg = DSPGenerator()
    areas = dg.generate_areas(managers)
    dsps = dg.generate_dsps(areas, dsp_users)
    
    print("Generating Merchants and Outlets...")
    mg = MerchantGenerator()
    merchants = mg.generate_merchants(500)
    outlets = mg.generate_outlets(merchants, 2000)
    
    print("Assigning Outlets to DSPs...")
    assignments = dg.assign_outlets(dsps, outlets)
    
    print("Generating Products...")
    pg = ProductGenerator()
    products = pg.generate_products()
    outlet_products = pg.generate_outlet_products(outlets, products, 5000)
    
    print("Generating Transactions (takes time)...")
    tg = TransactionGenerator()
    transactions = tg.generate_transactions(outlets, 200000)
    
    print("Generating Visits...")
    vg = VisitGenerator()
    visits = vg.generate_visits(assignments, 15000)
    
    print("Generating Scores...")
    sg = ScoreGenerator()
    from datetime import timedelta
    scores = sg.generate_scores(outlets, days=30)
    
    print("Generating Actions...")
    ag = ActionGenerator()
    actions = ag.generate_actions(assignments, 10000)
    
    print("Generating Conversations...")
    cg = ConversationGenerator()
    conversations = cg.generate_conversations(dsps, 500)
    
    print(f"Data Generation Complete. Stats:")
    print(f"Users: {len(users)}, Areas: {len(areas)}, DSPs: {len(dsps)}")
    print(f"Merchants: {len(merchants)}, Outlets: {len(outlets)}")
    print(f"Assignments: {len(assignments)}")
    print(f"Transactions: {len(transactions)}, Visits: {len(visits)}")
    
    # DB Insertion step would go here using SQLAlchemy async.
    # engine = create_async_engine(os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:"))
    # async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    # async with async_session() as session:
    #    ... insert data ...
    #    await session.commit()
    print("Skipping actual DB insertion since tables are not yet defined.")

if __name__ == "__main__":
    asyncio.run(seed_all())
