"""Contrato entre el worker del agente y la API.

El worker solo necesita dos operaciones (documento de arquitectura, 5.3):

* obtener el contexto de la ceremonia antes de entrar a la sala;
* entregar el resultado cuando la ceremonia termina.

Todo lo que cruza esa frontera está aquí. Un cambio incompatible en estos
modelos rompe el contrato entre desplegables y debe marcarse con
``BREAKING CHANGE`` en el pie del commit, además de subir ``VERSION_CONTRATO``.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from agilina_shared.enums import EstadoCeremonia, Idioma, ModoOperacion, RolEquipo


class ModeloContrato(BaseModel):
    """Base común: prohíbe campos desconocidos para que una incompatibilidad
    entre worker y API falle de inmediato y no de forma silenciosa."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ParticipanteContexto(ModeloContrato):
    """Quién participa en la ceremonia y en qué orden le toca el turno."""

    usuario_id: UUID
    nombre: str
    identidad_sala: str = Field(
        description="Identidad con la que el participante se une a LiveKit; es la que "
        "el worker usa para atribuir lo que se dice."
    )
    rol: RolEquipo
    orden_turno: int = Field(ge=0)


class ContextoCeremonia(ModeloContrato):
    """Lo que el worker necesita saber antes de entrar a la sala."""

    ceremonia_id: UUID
    equipo_id: UUID
    sala: str
    idioma: Idioma
    modo: ModoOperacion
    dia_sprint: int = Field(ge=1, description="Día del sprint en curso, para el saludo.")
    total_dias_sprint: int = Field(ge=1)
    participantes: list[ParticipanteContexto]
    segundos_silencio: int = Field(
        default=10, ge=1, description="Umbral X: silencio tras el que Agilina pregunta."
    )
    segundos_turno_trabado: int = Field(
        default=30, ge=1, description="Umbral Y: turno sin avance tras el que Agilina interviene."
    )


class SegmentoTranscripcion(ModeloContrato):
    """Un fragmento de transcripción final atribuido a quien lo dijo.

    La atribución no se calcula por análisis acústico: la identidad llega
    firmada en el token de la pista de audio.
    """

    usuario_id: UUID
    identidad_sala: str
    texto: str
    inicio_ms: int = Field(ge=0)
    fin_ms: int = Field(ge=0)


class ResultadoCeremonia(ModeloContrato):
    """Lo que el worker entrega a la API al cerrar la ceremonia.

    El razonamiento no ocurre aquí: el worker entrega la transcripción completa
    atribuida y la API la procesa una sola vez, ya fuera de la ruta crítica de
    latencia (AD-19).
    """

    ceremonia_id: UUID
    estado: EstadoCeremonia
    iniciada_en: datetime = Field(description="Siempre en UTC.")
    cerrada_en: datetime = Field(description="Siempre en UTC.")
    participantes_presentes: list[UUID]
    participantes_ausentes: list[UUID] = Field(default_factory=list)
    segmentos: list[SegmentoTranscripcion]
    degradada: bool = Field(
        default=False,
        description="True cuando el servicio de transcripción no respondió y la "
        "ceremonia continuó sin facilitación automática.",
    )
    detalle_degradacion: str | None = None
