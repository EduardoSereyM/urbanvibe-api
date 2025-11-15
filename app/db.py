"""Utilidades de conexión a la base de datos PostgreSQL.

Este módulo encapsula la creación de un pool de conexiones asíncronas con
`asyncpg`. El objetivo es reutilizar la conexión entre peticiones y mantener
el código del resto de la aplicación más limpio.
"""

import os
from typing import Optional
from urllib.parse import urlparse

import asyncpg

# Variable global donde guardaremos la referencia al pool. Se inicializa en
# `None` y sólo se crea la primera vez que se solicita.
_pool: Optional[asyncpg.pool.Pool] = None


async def get_pool() -> asyncpg.pool.Pool:
    """Devuelve un pool de conexiones `asyncpg`, creándolo si no existe."""

    global _pool  # Indicamos que vamos a modificar la variable global.

    # Si el pool aún no está creado, procedemos a inicializarlo.
    if not _pool:
        # La cadena de conexión completa viene de la variable de entorno
        # `DATABASE_URL`. Es obligatoria: si falta, `os.environ[...]` lanzará
        # una excepción clara para detectar el problema de configuración.
        dsn = os.environ["DATABASE_URL"]
        # Usamos `urlparse` para poder extraer elementos individuales de la URL
        # (host, usuario, contraseña, etc.) para efectos de depuración.
        parsed_dsn = urlparse(dsn)

        # No es buena práctica mostrar contraseñas en logs. Construimos una
        # versión "segura" reemplazando la contraseña por asteriscos.
        safe_dsn = (
            dsn.replace(parsed_dsn.password, "***")
            if parsed_dsn.password
            else dsn
        )

        # Mostramos en consola el DSN enmascarado junto con host y usuario para
        # facilitar la depuración cuando se despliega en distintos entornos.
        print(f"[DB] DSN={safe_dsn}")
        print(
            "[DB] Using host=%s user=%s"
            % (parsed_dsn.hostname, parsed_dsn.username)
        )

        # Finalmente creamos el pool con parámetros conservadores: SSL obligado
        # (aunque no validamos certificado), entre 1 y 10 conexiones abiertas y
        # un tiempo máximo de espera por comando de 10 segundos.
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            ssl="require",
            min_size=1,
            max_size=10,
            command_timeout=10,
        )

    # Si el pool ya existía simplemente lo devolvemos.
    return _pool
