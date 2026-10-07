# AD-25: organizar las pruebas con árbol espejo, *Data Builders* y cobertura total

- **Estado:** propuesta (pasa a aceptada al integrarse este PR)
- **Fecha:** 2026-10-04
- **Deciden:** Diego, Angélica
- **Historia:** HU-02

## Contexto

Al terminar el servidor de HU-02 las pruebas del backend eran 211, repartidas en carpetas
por tema (`identity/`, `integration/`, `keycloak/` y once archivos sueltos en la raíz).
Medido entonces:

- **No se veía qué capa probaba cada archivo**: `tests/identity/` mezclaba dominio, casos
  de uso, HTTP y el adaptador de Keycloak.
- **Cada archivo armaba sus propios datos** con funciones sueltas (`_invitation`,
  `_issue`, `_setup`, `make_team`…): una `Invitation` se construía de seis formas
  distintas, con valores por defecto que no coincidían.
- **La cobertura era del 94,7 %**, con `bootstrap` en 70 %, y nada la hacía cumplir.
- Una prueba dependía del entorno (`status in (200, 503)` según hubiera o no base de datos).

## Decisión

1. **Las pruebas viven en `tests/` en la raíz del repositorio**, no dentro de cada pieza:
   `tests/api/`, `tests/agent/`, `tests/stt/` y `tests/shared/`.
2. **Dos árboles por pieza, `unit/` e `integration/`, cada uno con la estructura de
   `src/`**: el archivo que prueba `identity/domain/invitation.py` es
   `tests/api/unit/identity/domain/test_invitation.py`. Lo que necesita PostgreSQL o
   Keycloak reales va en `integration/`, en la misma ruta, con su marcador. Un módulo que
   pasó a ser un paquete de una clase por archivo (`errors/`) conserva un solo archivo de
   pruebas, `test_errors.py`, en la ruta del paquete.
3. **Los datos se arman con *Data Builders*** (`tests/api/builders/`): valores por defecto
   válidos y fijos, un cambio por llamada (`.with_…`, `.as_admin()`, `.expired()`), cada
   llamada devuelve un builder nuevo y `build()` pasa por las reglas del dominio. Un estado
   como «usada» se alcanza con el comportamiento (`Invitation.accept`), nunca escribiendo
   atributos privados. Los identificadores salen de un contador que se reinicia en cada
   prueba, no de `uuid4`.
4. **Los dobles de los puertos viven en `tests/api/doubles/`** y cumplen el mismo
   `Protocol` que los adaptadores reales.
5. **La cobertura de la API y del contrato compartido es del 100 %** (líneas y ramas, con
   las pruebas unitarias y de integración sumadas) y la CI falla por debajo. `agent/` y
   `stt/` entran cuando sus historias escriban pruebas.
6. **Se admiten tres exclusiones**, todas en `pyproject.toml`: `pragma: no cover`,
   `TYPE_CHECKING`/`NotImplementedError`/cuerpos `...` de un `Protocol`, y
   `if __name__ == "__main__":`.

## Alternativas descartadas

- **Pruebas junto al código (`api/tests/`)**: es lo habitual en un monorrepo, pero se pidió
  separarlas del código de producción y poder ver todas las pruebas en un solo lugar.
- **Un solo árbol con marcadores**: más corto, pero mezcla en una carpeta lo que corre en
  segundos con lo que necesita servidores. Se prefirió que la ruta ya diga cuál es cuál.
- **Una fábrica de objetos (*object mother*) o funciones `make_*`**: no dejan componer
  variaciones sin una función por variación, y es lo que ya estaba pasando.
- **Un umbral menor (90 %)**: se llegó a 100 % sin pruebas forzadas; un umbral más bajo
  habría dejado sin vigilar justo las ramas de error de los adaptadores.

## Consecuencias

- Mover una prueba cuando se mueve su módulo es parte del cambio.
- Escribir una prueba empieza por el builder: si falta uno, se agrega en `builders/` y no
  dentro del archivo de la prueba.
- Cuando `agent/` y `stt/` implementen sus historias, se les aplica este mismo esquema y se
  agregan a la lista de cobertura.
- El umbral del 100 % obliga a justificar cada línea que no se pueda probar; es un costo
  querido.

## Cómo se verifica

`make coverage` (y `make verify`, y la CI) corre las pruebas unitarias y de integración y
falla si algo de `api/src` o `shared/src` queda sin cubrir. La guía práctica está en
[testing.md](../testing.md).
