"""Máquina de estados de la reunión diaria.

Lo que Agilina dice sale siempre de plantillas por idioma, nunca del modelo de
lenguaje (AD-19): las intervenciones dependen del estado de la ceremonia, que
el worker conoce, y no del contenido de lo que se dijo.

Los controles de la sala llegan por el canal de datos de LiveKit, no por la
API, y su emisor lo aporta LiveKit firmado en el token. Por eso la validación
de permisos vive aquí, contra el roster del contexto, y nunca confía en el
contenido del mensaje.
"""

from dataclasses import dataclass, field
from enum import StrEnum

from agilina_shared.contrato import ContextoCeremonia, ParticipanteContexto
from agilina_shared.enums import RolEquipo
from agilina_shared.i18n import texto


class EstadoFacilitacion(StrEnum):
    ESPERA = "espera"
    SALUDO = "saludo"
    TURNO = "turno"
    CERRADA = "cerrada"
    DEGRADADA = "degradada"


class AccionNoPermitida(Exception):
    """El emisor no tiene permiso para esa acción según el roster."""


@dataclass
class MaquinaFacilitacion:
    """Conduce una ceremonia. Una instancia por sala.

    En estado ESPERA, Agilina está en la sala pero no envía audio al servicio
    de transcripción: por eso el inicio de la daily es por botón y no por
    palabra clave.
    """

    contexto: ContextoCeremonia
    estado: EstadoFacilitacion = EstadoFacilitacion.ESPERA
    indice_turno: int = -1
    motivo_degradacion: str | None = None
    _orden: list[ParticipanteContexto] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self._orden = sorted(self.contexto.participantes, key=lambda p: p.orden_turno)

    # ------------------------------------------------------------- consultas --
    @property
    def turno_actual(self) -> ParticipanteContexto | None:
        if self.estado is not EstadoFacilitacion.TURNO:
            return None
        return self._orden[self.indice_turno]

    def participante(self, identidad_sala: str) -> ParticipanteContexto:
        for participante in self._orden:
            if participante.identidad_sala == identidad_sala:
                return participante
        raise AccionNoPermitida(f"'{identidad_sala}' no está en el roster de la ceremonia")

    def es_administrador(self, identidad_sala: str) -> bool:
        return self.participante(identidad_sala).rol is RolEquipo.ADMINISTRADOR

    # ----------------------------------------------------------- transiciones --
    def iniciar(self, identidad_sala: str) -> str:
        """Inicia la ceremonia. Solo el Administrador o Scrum Master puede."""
        if not self.es_administrador(identidad_sala):
            raise AccionNoPermitida("Solo el Administrador o Scrum Master inicia la ceremonia")
        if self.estado is not EstadoFacilitacion.ESPERA:
            raise AccionNoPermitida("La ceremonia ya fue iniciada")

        self.estado = EstadoFacilitacion.SALUDO
        return texto(
            "saludo",
            self.contexto.idioma,
            dia=self.contexto.dia_sprint,
            total=self.contexto.total_dias_sprint,
        )

    def ceder_turno(self) -> str | None:
        """Pasa al siguiente participante. Devuelve None cuando ya no quedan."""
        if self.estado not in (EstadoFacilitacion.SALUDO, EstadoFacilitacion.TURNO):
            raise AccionNoPermitida("La ceremonia no está en curso")

        if self.indice_turno + 1 >= len(self._orden):
            return None

        self.indice_turno += 1
        self.estado = EstadoFacilitacion.TURNO
        siguiente = self._orden[self.indice_turno]
        return texto("cede_turno", self.contexto.idioma, nombre=siguiente.nombre)

    def terminar_turno(self, identidad_sala: str) -> str | None:
        """Cierra el turno en curso.

        Cada quien puede terminar el suyo; el Administrador o Scrum Master
        puede terminar el de cualquiera.
        """
        actual = self.turno_actual
        if actual is None:
            raise AccionNoPermitida("No hay un turno en curso")

        emisor = self.participante(identidad_sala)
        propio = emisor.usuario_id == actual.usuario_id
        if not propio and emisor.rol is not RolEquipo.ADMINISTRADOR:
            raise AccionNoPermitida("Solo el Administrador puede terminar el turno de otra persona")

        return self.ceder_turno()

    def preguntar_por_silencio(self) -> str:
        actual = self.turno_actual
        if actual is None:
            raise AccionNoPermitida("No hay un turno en curso")
        return texto("silencio", self.contexto.idioma, nombre=actual.nombre)

    def preguntar_por_turno_trabado(self) -> str:
        actual = self.turno_actual
        if actual is None:
            raise AccionNoPermitida("No hay un turno en curso")
        return texto("turno_trabado", self.contexto.idioma, nombre=actual.nombre)

    def cerrar(self, identidad_sala: str | None = None) -> str:
        """Cierra la ceremonia.

        Con emisor, valida que sea el Administrador o Scrum Master; sin emisor,
        es el cierre automático al agotarse los turnos.
        """
        if identidad_sala is not None and not self.es_administrador(identidad_sala):
            raise AccionNoPermitida("Solo el Administrador o Scrum Master cierra la ceremonia")

        self.estado = EstadoFacilitacion.CERRADA
        return texto("despedida", self.contexto.idioma)

    def degradar(self, motivo: str) -> str:
        """El servicio de transcripción no responde.

        Agilina lo anuncia en voz alta y la ceremonia continúa sin facilitación
        automática, en vez de dejar la sala en silencio esperando.
        """
        self.estado = EstadoFacilitacion.DEGRADADA
        self.motivo_degradacion = motivo
        return texto("degradado", self.contexto.idioma)
