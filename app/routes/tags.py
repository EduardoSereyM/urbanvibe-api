# app/routes/tags.py

from typing import List, Optional

from fastapi import APIRouter, Query

from ..models import Tag, TagsByCategory
from ..db import get_pool

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
    """
    Devuelve los tags agrupados por categoría.

    - Si se pasa `categoria`, solo incluye esa categoría.
    - Si se pasa `q`, filtra por nombre o slug que contengan el texto (ILIKE).
    """

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

    grouped: dict[str, list[Tag]] = {}

    for r in rows:
        tag_dict = dict(r)
        cat = tag_dict["categoria"]
        grouped.setdefault(cat, []).append(Tag(**tag_dict))

    result: List[TagsByCategory] = [
        TagsByCategory(categoria=cat, tags=tags)
        for cat, tags in grouped.items()
    ]

    return result
