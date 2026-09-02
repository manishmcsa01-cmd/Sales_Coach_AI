import asyncio
from data.seed_database import seed_all

if __name__ == "__main__":
    asyncio.run(seed_all())
