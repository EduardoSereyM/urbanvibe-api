"""Aplicación principal de la API UrbanVibe.

Este módulo crea la instancia de FastAPI, configura CORS y monta los
routers que exponen los endpoints públicos. Se añaden comentarios
explicativos paso a paso para facilitar la lectura a nuevas personas en el
proyecto.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import get_pool
from .routes.locals import router as locals_router
from .routes.tags import router as tags_router

# ---------------------------------------------------------------------------
# Configuración de la aplicación FastAPI
# ---------------------------------------------------------------------------
# Se instancia la aplicación indicando un título y versión para que la
# documentación automática (Swagger/OpenAPI) muestre la información básica.
app = FastAPI(title="UrbanVibe API v1", version="0.1.0")

# ---------------------------------------------------------------------------
# Configuración de CORS
# ---------------------------------------------------------------------------
# La API puede ser consumida por aplicaciones alojadas en otros dominios. Para
# permitirlo, leemos una lista de orígenes autorizados desde la variable de
# entorno `ALLOWED_ORIGINS`. Si no existe, el valor por defecto abre CORS para
# todos los orígenes, lo cual es útil en entornos de desarrollo y pruebas.
_allowed = os.getenv("ALLOWED_ORIGINS", "")
# Se limpian los valores quitando espacios en blanco y descartando entradas
# vacías. El resultado es una lista con cada origen permitido.
origins = [o.strip() for o in _allowed.split(",") if o.strip()]

# FastAPI permite registrar middlewares. Aquí agregamos el middleware de CORS
# especificando los orígenes permitidos, si se permite el envío de cookies y
# qué métodos y cabeceras se aceptan. Al dejar `allow_origins` con una lista
# vacía se cae en el comodín `*` para aceptar cualquier origen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoint de salud
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    """Comprueba que la API y la base de datos estén operativas."""

    # `db_status` indica si la conexión a la base de datos fue exitosa. El
    # valor "ok" significa que la consulta de prueba se ejecutó correctamente.
    db_status = "ok"
    # En caso de error guardamos el mensaje para retornarlo al cliente y poder
    # diagnosticar rápidamente qué salió mal.
    detail = None

    try:
        # Obtenemos (o creamos si no existe) el pool de conexiones asíncronas.
        pool = await get_pool()
        # Abrimos una conexión temporal dentro de un contexto asíncrono. El
        # contexto garantiza que la conexión se libere de vuelta al pool.
        async with pool.acquire() as conn:
            # Se ejecuta una consulta trivial para validar la conexión.
            await conn.execute("SELECT 1;")
    except Exception as e:  # pylint: disable=broad-except
        # Cualquier excepción implica que la base de datos no respondió como se
        # esperaba. Marcamos el estado como error y capturamos el detalle.
        db_status = "error"
        detail = str(e)

    # Armamos la respuesta básica. Siempre incluye `status` (estado general de
    # la API) y `db` (estado de la base de datos).
    resp = {"status": "ok", "db": db_status}
    # Sólo agregamos el detalle cuando hubo un error para no enviar mensajes
    # innecesarios en el camino feliz.
    if detail and db_status == "error":
        resp["detail"] = detail

    return resp


# ---------------------------------------------------------------------------
# Registro de routers
# ---------------------------------------------------------------------------
# Se montan los routers que contienen las rutas de negocio. El prefijo asegura
# que todas las rutas queden agrupadas bajo `/api/v1/...`.
app.include_router(locals_router, prefix="/api/v1/locals")
app.include_router(tags_router, prefix="/api/v1/tags")
