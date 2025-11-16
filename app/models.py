# app/models.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


# ---------- LOCALES ----------

class LocalCard(BaseModel):
    id: UUID
    name: str

    description: Optional[str] = None
    menu_url: Optional[str] = None
    instagram_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    founder_badge: bool = False
    is_verified: bool = False
    status: Optional[str] = None
    is_active: bool = True

    lat: Optional[float] = None
    lon: Optional[float] = None

    visits_count: int = 0
    favorites_count: int = 0
    updates_count: int = 0

    tags_slug_array: List[str] = Field(default_factory=list)

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MapPoint(BaseModel):
    id: UUID
    name: str
    # ajusta según tu vista; si usas GeoJSON, normalmente sería geometry
    geometry: Optional[Dict[str, Any]] = None
    lat: float
    lon: float


class LocalsPage(BaseModel):
    items: List[LocalCard]
    limit: int
    offset: int
    total: int


# ---------- TAGS ----------

class Tag(BaseModel):
    id: int
    # la DB sigue en español, pero el JSON saldrá en inglés
    name: str = Field(alias="nombre")
    slug: str
    category: str = Field(alias="categoria")
    description: Optional[str] = Field(default=None, alias="descripcion")
    icon_url: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class LocalDetail(LocalCard):
    # importantísimo: no usar [] directo
    tags: List[Tag] = Field(default_factory=list)


class TagsByCategory(BaseModel):
    category: str = Field(alias="categoria")
    tags: List[Tag]

    class Config:
        allow_population_by_field_name = True
