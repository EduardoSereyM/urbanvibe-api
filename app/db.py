# app/db.py
import os
import asyncpg
from typing import Optional
from urllib.parse import urlparse

_pool: Optional[asyncpg.pool.Pool] = None

async def get_pool():
    global _pool
    if not _pool:
        dsn = os.environ["DATABASE_URL"]
        p = urlparse(dsn)

        # construir un DSN "seguro" para debug
        safe_dsn = dsn.replace(p.password, "***") if p.password else dsn

        print(f"[DB] DSN={safe_dsn}")
        print(f"[DB] Using host={p.hostname} user={p.username}")

        _pool = await asyncpg.create_pool(
            dsn=dsn,
            ssl="require",      # seguimos forzando SSL sin validar certificado
            min_size=1,
            max_size=10,
            command_timeout=10,
        )
    return _pool



