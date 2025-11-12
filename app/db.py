# app/db.py
import os, asyncpg
from typing import Optional
from urllib.parse import urlparse

_pool: Optional[asyncpg.pool.Pool] = None

async def get_pool():
    global _pool
    if not _pool:
        dsn = os.environ["DATABASE_URL"]
        p = urlparse(dsn)
        # 🔎 diagnóstico seguro: NO imprime secretos
        print(f"[DB] Using host={p.hostname} user={p.username}")
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=1, max_size=10,
            command_timeout=10
        )
    return _pool

