import os, asyncpg
from typing import Optional

_pool: Optional[asyncpg.pool.Pool] = None

async def get_pool():
    global _pool
    if not _pool:
        _pool = await asyncpg.create_pool(
            dsn=os.environ["DATABASE_URL"],
            min_size=1, max_size=10,
            command_timeout=10
        )
    return _pool
