from fastapi import FastAPI
from .routes.locals import router as locals_router

app = FastAPI(title="UrbanVibe API v1", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(locals_router, prefix="/api/v1/locals")
