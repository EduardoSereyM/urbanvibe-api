# app/models.py
from pydantic import BaseModel
from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime

class LocalCard(BaseModel):
    id: UUID
    name: str

    description: Optional[str] = None
    menu_url: Optional[str] = None
    instagram_url: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

    fundador_badge: Optional[bool] = None
    verificado: Optional[bool] = None
    estado: Optional[str] = None
    activo: Optional[bool] = None

    lat: Optional[float] = None
    lon: Optional[float] = None

    visitas_count: Optional[int] = None
    favoritos_count: Optional[int] = None
    actualizaciones_count: Optional[int] = None

    # timestamps tal como vienen de Supabase
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # si en la vista v1_locals_public incluyes tags_slug_array:
    tags_slug_array: Optional[List[str]] = None


class MapPoint(BaseModel):
    id: UUID
    name: str
    geometry: Dict
