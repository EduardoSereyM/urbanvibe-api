from pydantic import BaseModel
from typing import Optional, Dict

class LocalCard(BaseModel):
    id: str
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
    updated_at: Optional[str] = None

class MapPoint(BaseModel):
    id: str
    name: str
    geometry: Dict
