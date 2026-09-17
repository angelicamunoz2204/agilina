"""La máquina de facilitación se prueba sin sala, sin audio y sin red: es el
motor de la ceremonia y debe poder verificarse en segundos."""

from uuid import uuid4

import pytest

from agilina_agent.facilitacion.maquina import (
    AccionNoPermitida,
    EstadoFacilitacion,
    MaquinaFacilitacion,
)
from agilina_shared.contrato import ContextoCeremonia, ParticipanteContexto
from agilina_shared.enums import Idioma, ModoOperacion, RolEquipo

ADMIN = "sm-1"
MIEMBRO_A = "dev-1"
MIEMBRO_B = "dev-2"


def _contexto(idioma: Idioma = Idioma.ES) -> ContextoCeremonia:
    return ContextoCeremonia(
        ceremonia_id=uuid4(),
        equipo_id=uuid4(),
        sala="ceremonia-1",
        idioma=idioma,
        modo=ModoOperacion.SOPORTE,
        dia_sprint=4,
        total_dias_sprint=15,
        participantes=[
            ParticipanteContexto(
                usuario_id=uuid4(),
                nombre="Diego",
                identidad_sala=ADMIN,
                rol=RolEquipo.ADMINISTRADOR,
                orden_turno=0,
            ),
            ParticipanteContexto(
                usuario_id=uuid4(),
                nombre="Angélica",
                identidad_sala=MIEMBRO_A,
                rol=RolEquipo.MIEMBRO,
                orden_turno=1,
            ),
            ParticipanteContexto(
                usuario_id=uuid4(),
                nombre="Oscar",
                identidad_sala=MIEMBRO_B,
                rol=RolEquipo.MIEMBRO,
                orden_turno=2,
            ),
        ],
    )


def test_agilina_arranca_en_espera_sin_transmitir_audio():
    maquina = MaquinaFacilitacion(contexto=_contexto())
    assert maquina.estado is EstadoFacilitacion.ESPERA
    assert maquina.turno_actual is None


def test_el_saludo_anuncia_el_dia_del_sprint():
    maquina = MaquinaFacilitacion(contexto=_contexto())
    saludo = maquina.iniciar(ADMIN)
    assert "4" in saludo and "15" in saludo


def test_un_miembro_no_puede_iniciar_la_ceremonia():
    maquina = MaquinaFacilitacion(contexto=_contexto())
    with pytest.raises(AccionNoPermitida):
        maquina.iniciar(MIEMBRO_A)


def test_quien_no_esta_en_el_roster_no_controla_nada():
    maquina = MaquinaFacilitacion(contexto=_contexto())
    with pytest.raises(AccionNoPermitida):
        maquina.iniciar("intruso")


def test_los_turnos_siguen_el_orden_configurado():
    maquina = MaquinaFacilitacion(contexto=_contexto())
    maquina.iniciar(ADMIN)

    maquina.ceder_turno()
    assert maquina.turno_actual.nombre == "Diego"
    maquina.ceder_turno()
    assert maquina.turno_actual.nombre == "Angélica"
    maquina.ceder_turno()
    assert maquina.turno_actual.nombre == "Oscar"
    assert maquina.ceder_turno() is None


def test_cada_quien_termina_su_propio_turno():
    maquina = MaquinaFacilitacion(contexto=_contexto())
    maquina.iniciar(ADMIN)
    maquina.ceder_turno()
    maquina.ceder_turno()

    assert maquina.turno_actual.identidad_sala == MIEMBRO_A
    maquina.terminar_turno(MIEMBRO_A)
    assert maquina.turno_actual.identidad_sala == MIEMBRO_B


def test_un_miembro_no_termina_el_turno_de_otro():
    maquina = MaquinaFacilitacion(contexto=_contexto())
    maquina.iniciar(ADMIN)
    maquina.ceder_turno()
    maquina.ceder_turno()

    with pytest.raises(AccionNoPermitida):
        maquina.terminar_turno(MIEMBRO_B)


def test_el_administrador_puede_terminar_el_turno_de_cualquiera():
    maquina = MaquinaFacilitacion(contexto=_contexto())
    maquina.iniciar(ADMIN)
    maquina.ceder_turno()
    maquina.ceder_turno()

    maquina.terminar_turno(ADMIN)
    assert maquina.turno_actual.identidad_sala == MIEMBRO_B


def test_solo_el_administrador_cierra_la_ceremonia():
    maquina = MaquinaFacilitacion(contexto=_contexto())
    maquina.iniciar(ADMIN)

    with pytest.raises(AccionNoPermitida):
        maquina.cerrar(MIEMBRO_A)

    maquina.cerrar(ADMIN)
    assert maquina.estado is EstadoFacilitacion.CERRADA


def test_sin_transcripcion_la_ceremonia_continua_en_modo_degradado():
    maquina = MaquinaFacilitacion(contexto=_contexto())
    maquina.iniciar(ADMIN)

    anuncio = maquina.degradar("El servicio de transcripción no responde")

    assert maquina.estado is EstadoFacilitacion.DEGRADADA
    assert anuncio
    assert maquina.motivo_degradacion


def test_la_ceremonia_se_conduce_igual_en_ingles():
    """El idioma es un atributo del equipo y parametriza todo lo que Agilina dice."""
    maquina = MaquinaFacilitacion(contexto=_contexto(Idioma.EN))

    saludo = maquina.iniciar(ADMIN)
    cesion = maquina.ceder_turno()

    assert "sprint" in saludo.lower()
    assert "turn" in cesion.lower()
    assert "Diego" in cesion
