"""Modelos de datos utilizados por la API."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class LocalCard(BaseModel):
    """Representa la tarjeta/resumen de un local mostrado en listados."""

    # Identificador único del local en formato UUID.
    id: UUID
    # Nombre comercial visible para el usuario final.
    name: str

    # Campos descriptivos y enlaces opcionales.
    description: Optional[str] = None
    menu_url: Optional[str] = None
    instagram_url: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

    # Señales adicionales del local (badges, estados).
    fundador_badge: Optional[bool] = None
    verificado: Optional[bool] = None
    estado: Optional[str] = None
    activo: Optional[bool] = None

    # Ubicación geográfica.
    lat: Optional[float] = None
    lon: Optional[float] = None

    # Métricas de interacción.
    visitas_count: Optional[int] = None
    favoritos_count: Optional[int] = None
    actualizaciones_count: Optional[int] = None

    # Listado de tags asociados en formato slug.
    tags_slug_array: Optional[List[str]] = None

    # Marcas de tiempo de auditoría.
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MapPoint(BaseModel):
    """Elemento resumido utilizado en el mapa interactivo."""

    id: UUID
    name: str
    # Geometría en formato GeoJSON (dict serializable a JSON).
    geometry: Dict[str, Any]


class LocalsPage(BaseModel):
    """Respuesta paginada de locales."""

    items: List[LocalCard]
    limit: int
    offset: int
    total: int


class Tag(BaseModel):
    """Modelo base para representar un tag."""

    id: int
    nombre: str
    slug: str
    categoria: str
    descripcion: Optional[str] = None
    icon_url: Optional[str] = None


class LocalDetail(LocalCard):
    """Extiende `LocalCard` agregando los tags completos del local."""

    tags: List[Tag] = []


class TagsByCategory(BaseModel):
    """Estructura de salida para agrupar tags por categoría."""

    categoria: str
    tags: List[Tag]
