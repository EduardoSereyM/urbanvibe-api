# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.locals import router as locals_router

app = FastAPI(title="UrbanVibe API v1", version="0.1.0")

# --- CORS ---
_allowed = os.getenv("ALLOWED_ORIGINS", "")
origins = [o.strip() for o in _allowed.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],   # si no se configuró, abre para pruebas
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)
# ------------



@app.get("/health")
async def health():
    """
    Healthcheck básico + verificación de conexión a la base de datos.
    """
    db_status = "ok"
    detail = None

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1;")
    except Exception as e:
        db_status = "error"
        detail = str(e)

    resp = {"status": "ok", "db": db_status}
    if detail and db_status == "error":
        resp["detail"] = detail

    return resp


app.include_router(locals_router, prefix="/api/v1/locals")
