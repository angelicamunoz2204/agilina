"""Punto de entrada del worker.

    make agent     → registra el worker en LiveKit y queda esperando trabajos

El worker abre una conexión de salida hacia LiveKit y se registra. Cuando se
crea la sala de una ceremonia, LiveKit ofrece el trabajo por esa conexión y
este módulo lanza el subproceso que se une a la sala como un participante más.

Lo que hay aquí es el esqueleto que demuestra el ciclo de vida: entrar a la
sala, anunciarse y quedar en espera. La facilitación completa llega con las
historias del Release 1 y 2; la lógica que ya existe vive en
``agilina_agent.facilitacion`` y se prueba sin sala ni audio.
"""

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli

from agilina_agent.adaptadores.tts_elevenlabs import SintesisSimulada
from agilina_agent.config import obtener_configuracion
from agilina_agent.registro import configurar_registro, obtener_registro

registro = obtener_registro(__name__)


async def punto_de_entrada(ctx: JobContext) -> None:
    """Se ejecuta una vez por ceremonia, en su propio subproceso."""
    configuracion = obtener_configuracion()
    configurar_registro(configuracion.nivel_log)

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    registro.info("Agilina entró a la sala %s", ctx.room.name)

    # En espera: Agilina está en la sala pero no envía audio al servicio de
    # transcripción hasta que alguien inicia la daily desde la aplicación.
    voz = SintesisSimulada()
    await voz.sintetizar("Agilina está en la sala y en espera.", configuracion.idioma_por_defecto)


def ejecutar() -> None:
    configuracion = obtener_configuracion()
    configurar_registro(configuracion.nivel_log)
    registro.info("Registrando el worker en %s", configuracion.livekit_url or "(sin configurar)")

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=punto_de_entrada,
            ws_url=configuracion.livekit_url,
            api_key=configuracion.livekit_api_key,
            api_secret=configuracion.livekit_api_secret,
        )
    )


__all__ = ["ejecutar", "punto_de_entrada"]

if __name__ == "__main__":
    ejecutar()
