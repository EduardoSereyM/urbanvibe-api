from fastapi import APIRouter, Query
from typing import List, Optional
from ..models import LocalCard, MapPoint
from ..db import get_pool

router = APIRouter(tags=["locals"])

@router.get("", response_model=List[LocalCard])
async def list_locals(
    q: Optional[str] = Query(default=None, min_length=1, max_length=64),
    tags: Optional[List[str]] = Query(default=None),
    bbox: Optional[str] = Query(default=None, description="minLon,minLat,maxLon,maxLat"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    min_lon = min_lat = max_lon = max_lat = None
    if bbox:
        parts = [float(x) for x in bbox.split(",")]
        if len(parts) == 4:
            min_lon, min_lat, max_lon, max_lat = parts

    sql = """
    SELECT *
    FROM public.v1_locals_public l
    WHERE 1=1
      AND ( $1::text IS NULL
            OR EXISTS (
                 SELECT 1
                 FROM public.locales lx
                 WHERE lx.id = l.id
                   AND lx.fts @@ plainto_tsquery('spanish', $1)
            )
          )
      AND ( $2::text[] IS NULL
            OR EXISTS (
                 SELECT 1
                 FROM public.locales_tags lt
                 JOIN public.tags t ON t.id = lt.tag_id
                 WHERE lt.local_id = l.id
                   AND t.slug = ANY($2)
            )
          )
      AND ( $3::float8 IS NULL
            OR ST_Intersects(
                 l.geom,
                 ST_MakeEnvelope($3,$4,$5,$6,4326)
               )
          )
    ORDER BY l.updated_at DESC
    LIMIT $7 OFFSET $8;
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            sql,
            (q if q and len(q) >= 3 else None),
            tags,
            min_lon, min_lat, max_lon, max_lat,
            limit, offset
        )
    return [dict(r) for r in rows]

@router.get("/map", response_model=List[MapPoint])
async def map_points(
    tags: Optional[List[str]] = Query(default=None),
    bbox: Optional[str] = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
):
    min_lon = min_lat = max_lon = max_lat = None
    if bbox:
        parts = [float(x) for x in bbox.split(",")]
        if len(parts) == 4:
            min_lon, min_lat, max_lon, max_lat = parts

    sql = """
    SELECT l.id, l.name, ST_AsGeoJSON(l.geom)::json AS geometry
    FROM public.v1_locals_map l
    WHERE 1=1
      AND ( $1::text[] IS NULL
            OR EXISTS (
                 SELECT 1
                 FROM public.locales_tags lt
                 JOIN public.tags t ON t.id = lt.tag_id
                 WHERE lt.local_id = l.id
                   AND t.slug = ANY($1)
            )
          )
      AND ( $2::float8 IS NULL
            OR ST_Intersects(
                 l.geom,
                 ST_MakeEnvelope($2,$3,$4,$5,4326)
               )
          )
    LIMIT $6;
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, tags, min_lon, min_lat, max_lon, max_lat, limit)
    return [{"id": r["id"], "name": r["name"], "geometry": r["geometry"]} for r in rows]
