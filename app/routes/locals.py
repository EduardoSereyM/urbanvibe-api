# app/routes/locals.py

import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Query, HTTPException

from ..models import LocalCard, MapPoint, LocalsPage, LocalDetail, Tag
from ..db import get_pool

router = APIRouter(tags=["locals"])


@router.get("", response_model=LocalsPage)
async def list_locals(
    q: Optional[str] = Query(default=None, min_length=1, max_length=64),
    tags: Optional[List[str]] = Query(default=None),
    bbox: Optional[str] = Query(
        default=None,
        description="minLon,minLat,maxLon,maxLat"
    ),
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

    # -----------------------
    # Query de datos (items)
    # -----------------------
    data_sql = """
    SELECT
      l.id,
      l.name,
      l.description,
      l.logo_url,
      l.cover_image_url,
      l.menu_url,
      l.instagram_url,
      l.phone,
      l.email,
      l.founder_badge,
      l.is_verified,
      l.status,
      l.is_active,
      l.lat,
      l.lon,
      l.visits_count,
      l.favorites_count,
      l.updates_count,
      l.tags_slug_array,
      l.created_at,
      l.updated_at
    FROM public.v1_locals_public AS l
    WHERE
      l.status = 'publicado'
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

    # -----------------------
    # Query de conteo (total)
    # -----------------------
    count_sql = """
    SELECT
      COUNT(*) AS total
    FROM public.v1_locals_public AS l
    WHERE
      l.status = 'publicado'
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
      );
    """

    pool = await get_pool()
    async with pool.acquire() as conn:
        # total
        count_row = await conn.fetchrow(
            count_sql,
            effective_q,
            tags,
            min_lon,
            min_lat,
            max_lon,
            max_lat,
        )
        total = count_row["total"] if count_row is not None else 0

        # items
        rows = await conn.fetch(
            data_sql,
            effective_q,
            tags,
            min_lon,
            min_lat,
            max_lon,
            max_lat,
            limit,
            offset,
        )

    items = [dict(r) for r in rows]

    return LocalsPage(
        items=items,
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get("/map", response_model=List[MapPoint])
async def locals_map(
    tags: Optional[List[str]] = Query(default=None),
    bbox: Optional[str] = Query(
        default=None,
        description="minLon,minLat,maxLon,maxLat"
    ),
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
      ST_AsGeoJSON(l.geom) AS geometry,
      l.lat,
      l.lon,
      l.logo_url
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
                "lat": r["lat"],
                "lon": r["lon"],
                "logo_url": r["logo_url"],
            }
        )

    return result


@router.get("/{local_id}", response_model=LocalDetail)
async def get_local_detail(local_id: UUID):
    """
    Devuelve el detalle de un local:
    - Datos básicos (LocalCard)
    - Tags asociados
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Datos del local
        local_row = await conn.fetchrow(
            """
            SELECT
              l.id,
              l.name,
              l.description,
              l.logo_url,
              l.cover_image_url,
              l.menu_url,
              l.instagram_url,
              l.phone,
              l.email,
              l.founder_badge,
              l.is_verified,
              l.status,
              l.is_active,
              l.lat,
              l.lon,
              l.visits_count,
              l.favorites_count,
              l.updates_count,
              l.tags_slug_array,
              l.created_at,
              l.updated_at
            FROM public.v1_locals_public AS l
            WHERE l.id = $1
              AND l.status = 'publicado';
            """,
            local_id,
        )

        if local_row is None:
            raise HTTPException(status_code=404, detail="Local not found")

        # Tags del local
        tags_rows = await conn.fetch(
            """
            SELECT
              t.id,
              t.nombre,
              t.slug,
              t.categoria,
              t.descripcion,
              t.icon_url
            FROM public.locales_tags AS lt
            JOIN public.tags AS t ON t.id = lt.tag_id
            WHERE lt.local_id = $1
            ORDER BY t.nombre;
            """,
            local_id,
        )

    local_dict = dict(local_row)
    # Tag usa alias en models.py, así que esto se mapea a name/category/description
    local_dict["tags"] = [dict(r) for r in tags_rows]

    return LocalDetail(**local_dict)
