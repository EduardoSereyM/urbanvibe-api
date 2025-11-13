# app/db.py
import os
import ssl
import asyncpg
from typing import Optional
from urllib.parse import urlparse

_pool: Optional[asyncpg.pool.Pool] = None

async def get_pool():
    global _pool
    if not _pool:
        dsn = os.environ["DATABASE_URL"]
        p = urlparse(dsn)

        # diagnóstico seguro
        print(f"[DB] Using host={p.hostname} user={p.username}")

        # crear contexto SSL por defecto
        ssl_ctx = ssl.create_default_context()

        _pool = await asyncpg.create_pool(
            dsn=dsn,
            ssl=ssl_ctx,           # 👈 ESTA ES LA CLAVE
            min_size=1,
            max_size=10,
            command_timeout=10,
        )
    return _pool


