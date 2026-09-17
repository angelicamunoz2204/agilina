"""El Definition of Done exige que todo texto dirigido al usuario exista en los
dos idiomas. Esta prueba es lo que vuelve verificable ese criterio."""

import pytest

from agilina_shared.enums import Idioma
from agilina_shared.i18n import PLANTILLAS, claves_incompletas, texto


def test_ninguna_plantilla_queda_sin_traducir():
    assert claves_incompletas() == []


@pytest.mark.parametrize("idioma", list(Idioma))
def test_el_saludo_incluye_el_dia_del_sprint_en_ambos_idiomas(idioma: Idioma):
    resultado = texto("saludo", idioma, dia=3, total=15)
    assert "3" in resultado
    assert "15" in resultado


def test_una_clave_inexistente_falla_en_vez_de_devolver_vacio():
    with pytest.raises(KeyError):
        texto("clave_que_no_existe", Idioma.ES)


def test_todas_las_plantillas_resuelven_sus_parametros():
    parametros = {"dia": 1, "total": 15, "nombre": "Angélica"}
    for clave, traducciones in PLANTILLAS.items():
        for idioma in traducciones:
            assert texto(clave, idioma, **parametros)
