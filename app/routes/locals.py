"""Rutas relacionadas con locales (listado, mapa y detalle)."""

import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from ..db import get_pool
from ..models import LocalCard, LocalDetail, LocalsPage, MapPoint, Tag

# Todos los endpoints de este módulo comparten el tag "locals" en la
# documentación de FastAPI.
router = APIRouter(tags=["locals"])


@router.get("", response_model=LocalsPage)
async def list_locals(
    q: Optional[str] = Query(default=None, min_length=1, max_length=64),
    tags: Optional[List[str]] = Query(default=None),
    bbox: Optional[str] = Query(default=None, description="minLon,minLat,maxLon,maxLat"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Devuelve una página de locales filtrados por texto, tags y/o bounding box."""

    # ------------------------------------------------------------------
    # Normalización de parámetros de entrada
    # ------------------------------------------------------------------
    # Un bounding box (bbox) se representa como cuatro números separados por
    # comas: lon mínima, lat mínima, lon máxima, lat máxima. Si no se provee un
    # valor válido, se mantienen en `None` para que la query ignore el filtro.
    min_lon = min_lat = max_lon = max_lat = None
    if bbox:
        parts = bbox.split(",")
        if len(parts) == 4:
            min_lon, min_lat, max_lon, max_lat = map(float, parts)

    # Para evitar búsquedas muy costosas, sólo se realiza la búsqueda textual
    # cuando se ingresan al menos 3 caracteres. De lo contrario se ignora.
    effective_q = q if q and len(q) >= 3 else None

    # ------------------------------------------------------------------
    # Consulta SQL principal (obtiene los locales paginados)
    # ------------------------------------------------------------------
    data_sql = """
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

    # ------------------------------------------------------------------
    # Consulta de conteo (total de elementos para paginación)
    # ------------------------------------------------------------------
    count_sql = """
    SELECT
      COUNT(*) AS total
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
      );
    """

    # Se solicita una conexión al pool para ejecutar ambas consultas dentro del
    # mismo contexto.
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Ejecutamos la consulta de conteo para saber cuántos resultados totales
        # existen con los filtros aplicados.
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

        # Luego obtenemos la página actual con los datos detallados.
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

    # `asyncpg.Record` no es serializable, por eso convertimos cada fila en
    # diccionario antes de construir el modelo Pydantic.
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
    bbox: Optional[str] = Query(default=None, description="minLon,minLat,maxLon,maxLat"),
    limit: int = Query(default=500, ge=1, le=2000),
):
    """Devuelve puntos geográficos para mostrar locales en un mapa."""

    # Normalizamos el bounding box de la misma forma que en `list_locals`.
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

    result: List[MapPoint] = []
    for r in rows:
        geom = r["geometry"]
        if isinstance(geom, str):
            try:
                # Las geometrías vienen como cadenas GeoJSON. Las convertimos en
                # diccionarios de Python para que FastAPI los serialice
                # correctamente. Si el JSON es inválido, se deja como `None`.
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


@router.get("/{local_id}", response_model=LocalDetail)
async def get_local_detail(local_id: UUID):
    """Obtiene la información detallada de un local publicado."""

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Primera consulta: extrae todos los campos del local.
        local_row = await conn.fetchrow(
            """
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
            WHERE l.id = $1
              AND l.estado = 'publicado';
            """,
            local_id,
        )

        if local_row is None:
            # Si el local no existe o no está publicado devolvemos un 404.
            raise HTTPException(status_code=404, detail="Local not found")

        # Segunda consulta: obtiene todos los tags asociados al local.
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

    # Convertimos el registro principal en diccionario y agregamos la lista de
    # tags formateada.
    local_dict = dict(local_row)
    local_dict["tags"] = [dict(r) for r in tags_rows]

    return LocalDetail(**local_dict)
