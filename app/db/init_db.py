from app.db.session import engine
from app.models import Base
import logging

logger = logging.getLogger(__name__)

async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Successfully created all database tables.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
