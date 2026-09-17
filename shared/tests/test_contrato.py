"""El contrato es lo que mantiene alineados al worker y a la API: si estas
pruebas fallan, un desplegable dejó de entender al otro."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from agilina_shared import (
    ContextoCeremonia,
    EstadoCeremonia,
    Idioma,
    ModoOperacion,
    ParticipanteContexto,
    ResultadoCeremonia,
    RolEquipo,
    SegmentoTranscripcion,
)


def _participante(orden: int = 0) -> ParticipanteContexto:
    return ParticipanteContexto(
        usuario_id=uuid4(),
        nombre="Diego",
        identidad_sala="usuario-1",
        rol=RolEquipo.MIEMBRO,
        orden_turno=orden,
    )


def _contexto() -> ContextoCeremonia:
    return ContextoCeremonia(
        ceremonia_id=uuid4(),
        equipo_id=uuid4(),
        sala="ceremonia-1",
        idioma=Idioma.ES,
        modo=ModoOperacion.SOPORTE,
        dia_sprint=3,
        total_dias_sprint=15,
        participantes=[_participante(0), _participante(1)],
    )


def test_contexto_viaja_completo_en_un_ida_y_vuelta_json():
    contexto = _contexto()
    recuperado = ContextoCeremonia.model_validate_json(contexto.model_dump_json())
    assert recuperado == contexto


def test_los_umbrales_tienen_los_valores_de_arranque_acordados():
    contexto = _contexto()
    assert contexto.segundos_silencio == 10
    assert contexto.segundos_turno_trabado == 30


def test_un_campo_desconocido_rompe_de_inmediato():
    """Una incompatibilidad entre versiones debe fallar, no pasar inadvertida."""
    datos = _contexto().model_dump(mode="json")
    datos["campo_que_no_existe"] = True
    with pytest.raises(ValidationError):
        ContextoCeremonia.model_validate(datos)


def test_resultado_admite_ceremonia_degradada_sin_segmentos():
    resultado = ResultadoCeremonia(
        ceremonia_id=uuid4(),
        estado=EstadoCeremonia.DEGRADADA,
        iniciada_en=datetime.now(UTC),
        cerrada_en=datetime.now(UTC),
        participantes_presentes=[uuid4()],
        segmentos=[],
        degradada=True,
        detalle_degradacion="El servicio de transcripción no respondió",
    )
    assert resultado.degradada is True


def test_el_segmento_conserva_hablante_y_marcas_de_tiempo():
    segmento = SegmentoTranscripcion(
        usuario_id=uuid4(),
        identidad_sala="usuario-1",
        texto="Ayer terminé la migración",
        inicio_ms=0,
        fin_ms=2400,
    )
    assert segmento.fin_ms > segmento.inicio_ms
