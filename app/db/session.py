from contextvars import ContextVar
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Context variables for tenant/RLS information
tenant_dsp_id: ContextVar[str] = ContextVar("tenant_dsp_id", default="")
tenant_role: ContextVar[str] = ContextVar("tenant_role", default="")
tenant_area_id: ContextVar[str] = ContextVar("tenant_area_id", default="")

async def get_db():
    async with AsyncSessionLocal() as session:
        # Set RLS parameters for PostgreSQL
        dsp_id = tenant_dsp_id.get()
        role = tenant_role.get()
        area_id = tenant_area_id.get()
        if role:
            await session.execute(text(f"SET LOCAL app.role = '{role}'"))
        if dsp_id:
            await session.execute(text(f"SET LOCAL app.dsp_id = '{dsp_id}'"))
        if area_id:
            await session.execute(text(f"SET LOCAL app.area_id = '{area_id}'"))

        yield session
