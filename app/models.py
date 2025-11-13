# app/models.py

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
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

    tags_slug_array: Optional[List[str]] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MapPoint(BaseModel):
    id: UUID
    name: str
    geometry: Dict[str, Any]


class LocalsPage(BaseModel):
    items: List[LocalCard]
    limit: int
    offset: int
    total: int
