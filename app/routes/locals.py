# app/routes/locals.py

import json
from typing import List, Optional

from fastapi import APIRouter, Query

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
    # --- bbox ---
    min_lon = min_lat = max_lon = max_lat = None
    if bbox:
        parts = bbox.split(",")
        if len(parts) == 4:
            min_lon, min_lat, max_lon, max_lat = map(float, parts)

    # solo buscamos si hay 3+ caracteres
    effective_q = q if q and len(q) >= 3 else None

    sql = """
    SELECT
      l.id,
      l.name,
      l.description,
      l.menu_url,
      l.instagram_url,
      l.telefono,
      l.email,
      l.fundador_badge,
      l.verificado,
      l.estado,
      l.activo,
      l.lat,
      l.lon,
      l.visitas_count,
      l.favoritos_count,
      l.actualizaciones_count,
      l.tags_slug_array,
      l.created_at,
      l.updated_at
    FROM public.v1_locals_public AS l
    WHERE
      l.estado = 'publicado'
      AND (
        $1::text IS NULL
        OR EXISTS (
          SELECT 1
          FROM public.locales AS lx
          WHERE lx.id = l.id
            AND lx.fts @@ plainto_tsquery('spanish', $1)
        )
      )
      AND (
        $2::text[] IS NULL
        OR EXISTS (
          SELECT 1
          FROM public.locales_tags AS lt
          JOIN public.tags AS t ON t.id = lt.tag_id
          WHERE lt.local_id = l.id
            AND t.slug = ANY($2)
        )
      )
      AND (
        $3::float8 IS NULL
        OR ST_Intersects(
             l.geom,
             ST_MakeEnvelope($3, $4, $5, $6, 4326)
        )
      )
    ORDER BY l.created_at DESC
    LIMIT $7 OFFSET $8;
    """

    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            sql,
            effective_q,
            tags,
            min_lon,
            min_lat,
            max_lon,
            max_lat,
            limit,
            offset,
        )

    return [dict(r) for r in rows]


@router.get("/map", response_model=List[MapPoint])
async def locals_map(
    tags: Optional[List[str]] = Query(default=None),
    bbox: Optional[str] = Query(default=None, description="minLon,minLat,maxLon,maxLat"),
    limit: int = Query(default=500, ge=1, le=2000),
):
    min_lon = min_lat = max_lon = max_lat = None
    if bbox:
        parts = bbox.split(",")
        if len(parts) == 4:
            min_lon, min_lat, max_lon, max_lat = map(float, parts)

    sql = """
    SELECT
      l.id,
      l.name,
      ST_AsGeoJSON(l.geom) AS geometry
    FROM public.v1_locals_map AS l
    WHERE
      (
        $1::text[] IS NULL
        OR EXISTS (
          SELECT 1
          FROM public.locales_tags AS lt
          JOIN public.tags AS t ON t.id = lt.tag_id
          WHERE lt.local_id = l.id
            AND t.slug = ANY($1)
        )
      )
      AND (
        $2::float8 IS NULL
        OR ST_Intersects(
             l.geom,
             ST_MakeEnvelope($2, $3, $4, $5, 4326)
        )
      )
    LIMIT $6;
    """

    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            sql,
            tags,
            min_lon,
            min_lat,
            max_lon,
            max_lat,
            limit,
        )

    result = []
    for r in rows:
        geom = r["geometry"]
        # ST_AsGeoJSON devuelve texto → lo convertimos a dict
        if isinstance(geom, str):
            try:
                geom = json.loads(geom)
            except json.JSONDecodeError:
                geom = None

        result.append(
            {
                "id": r["id"],
                "name": r["name"],
                "geometry": geom,
            }
        )

    return result
