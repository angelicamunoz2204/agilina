"""Planificador de trabajos en segundo plano.

Agilina necesita disparadores por hora fija (convocatoria previa a la daily,
recordatorio matutino, limpieza por retención) y la respuesta diferida a Slack,
que exige contestar en menos de tres segundos y ejecutar el trabajo después.
Eso es un planificador, no un broker: la garantía que hace falta es sobrevivir
a un reinicio, no distribuir carga (AD-08).

El almacén vive en la misma base de datos del dominio, de modo que un reinicio
no pierde trabajos. Corre dentro del proceso de la API con réplica única
declarada; si el despliegue creciera, el almacén persistido permite añadir
bloqueo por trabajo.
"""

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from agilina_api.config import obtener_configuracion
from agilina_api.registro import obtener_registro

registro = obtener_registro(__name__)

TABLA_TRABAJOS = "trabajos_programados"


def crear_planificador() -> AsyncIOScheduler:
    """Construye el planificador con su almacén en Postgres.

    La misma cadena de conexión sirve tal cual: ``psycopg`` es síncrono para
    SQLAlchemy clásico, que es lo que APScheduler 3 sabe usar, y asíncrono para
    el motor de la API.
    """
    configuracion = obtener_configuracion()
    almacen = SQLAlchemyJobStore(url=configuracion.dsn, tablename=TABLA_TRABAJOS)
    planificador = AsyncIOScheduler(
        jobstores={"default": almacen},
        timezone="UTC",  # Todo se almacena y se opera en UTC; la zona es cosa del navegador.
    )
    registro.info("Planificador creado con almacén en %s", TABLA_TRABAJOS)
    return planificador
