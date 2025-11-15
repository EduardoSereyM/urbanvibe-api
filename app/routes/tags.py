"""Rutas que exponen el catálogo de tags."""

from typing import List, Optional

from fastapi import APIRouter, Query

from ..db import get_pool
from ..models import Tag, TagsByCategory

router = APIRouter(tags=["tags"])


@router.get("", response_model=List[TagsByCategory])
async def list_tags(
    categoria: Optional[str] = Query(
        default=None,
        description="Filtra por categoría exacta (ej: 'contexto', 'tipo_local', etc.)",
    ),
    q: Optional[str] = Query(
        default=None,
        min_length=1,
        max_length=64,
        description="Búsqueda por nombre o slug del tag",
    ),
):
    """Recupera los tags agrupados por categoría, aplicando filtros opcionales."""

    # Si la cadena de búsqueda tiene menos de 2 caracteres se ignora para evitar
    # consultas poco eficientes.
    effective_q = q if q and len(q) >= 2 else None

    sql = """
    SELECT
      t.id,
      t.nombre,
      t.slug,
      t.categoria,
      t.descripcion,
      t.icon_url
    FROM public.tags AS t
    WHERE
      ($1::text IS NULL OR t.categoria = $1)
      AND (
        $2::text IS NULL
        OR (t.nombre ILIKE '%' || $2 || '%' OR t.slug ILIKE '%' || $2 || '%')
      )
    ORDER BY t.categoria, t.nombre;
    """

    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, categoria, effective_q)

    # Agrupamos los registros por categoría para satisfacer el modelo de
    # respuesta. `grouped` es un diccionario cuyo valor es la lista de objetos
    # `Tag` pertenecientes a cada categoría.
    grouped: dict[str, list[Tag]] = {}

    for r in rows:
        tag_dict = dict(r)
        cat = tag_dict["categoria"]
        grouped.setdefault(cat, []).append(Tag(**tag_dict))

    # Convertimos el diccionario en una lista de `TagsByCategory` para que
    # FastAPI serialice la respuesta siguiendo el esquema esperado.
    result: List[TagsByCategory] = [
        TagsByCategory(categoria=cat, tags=tags)
        for cat, tags in grouped.items()
    ]

    return result
