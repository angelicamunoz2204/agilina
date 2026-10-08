# AD-31: guardar la hora de la daily en UTC con su zona de captura

- **Estado:** propuesta (pasa a aceptada al integrarse este PR)
- **Fecha:** 2026-10-07
- **Deciden:** Diego, Angélica
- **Historia:** HU-07

## Contexto

AD-20 manda operar y guardar los instantes en UTC, y hasta ahora la zona horaria era asunto
exclusivo del navegador: la API no guardaba ninguna. La HU-07 pide una hora de daily que el
Administrador fija para todo el equipo y que se repite cada día del sprint, más el conteo
«día N de M» que muestra el dashboard. Las dos cosas dependen de una zona:

- La daily es una **hora de pared** («a las 9:00»), no un instante. Un `TIME` en UTC se corre
  una hora cuando cambia el horario de verano: una daily de las 9:00 en Nueva York es 14:00Z en
  invierno y 13:00Z en verano.
- Una daily temprana al este de UTC cae en **otra fecha UTC**: las 8:00 del lunes en Tokio son
  las 23:00Z del domingo. Si el calendario fuera el de UTC, la daily caería un día corrida y el
  día del sprint cambiaría a las 9:00 de la mañana en Tokio.
- La ceremonia es síncrona: es **un solo instante para todos**, aunque cada integrante lo vea
  en su zona.

La historia limitaba además la daily a los días hábiles (lunes a viernes). El usuario decidió
otra cosa: hay equipos que trabajan el sábado o que cierran el sprint en domingo, así que el
inicio y el fin son libres y cuentan todos los días del calendario.

## Decisión

- El sprint guarda la hora de la daily como un **instante UTC de anclaje** (`TIMESTAMPTZ`: la
  hora elegida, en el día de inicio) más la **zona de captura** (`TEXT`, zona IANA del navegador
  de quien guardó el sprint). Ninguna columna guarda una hora local. La hora de pared se
  recupera convirtiendo el anclaje a la zona de captura.
- **Las ocurrencias** de la daily son esa hora de pared en la zona de captura en cada fecha del
  periodo del sprint, convertida a UTC. Una hora inexistente o ambigua por el cambio de horario
  se resuelve con `fold=0` (el desfase vigente antes del cambio).
- **El calendario del sprint es el de la zona de captura:** «hoy» es la fecha local del
  instante actual en esa zona. El instante entra siempre en UTC desde el puerto `Clock`.
- **Cuentan todos los días del calendario**, sábado y domingo incluidos. M es la cantidad de
  días del periodo, ambos extremos incluidos; N vale 0 antes del inicio (`not_started`), de 1 a
  M durante el sprint (`in_progress`) y M después del fin (`finished`). Festivos y días
  laborables configurables quedan fuera.
- Al guardar, **siempre se guarda la zona del navegador de quien guarda**, y la pantalla muestra
  la zona vigente.
- Las dos reglas son **funciones puras** en `agilina_shared/sprint_calendar/`
  (`daily_occurrences` y `sprint_day_at`), solo con la biblioteca estándar, para que la API, el
  agente y el planificador calculen lo mismo.
- La base de zonas es el **tzdata del sistema** de la imagen de Python; no se agrega el paquete
  `tzdata` de PyPI.

## Alternativas descartadas

| Alternativa | Por qué no |
| --- | --- |
| Zona horaria por equipo | Es un dato más que alguien debe mantener al día, y el único que la necesita es la daily del sprint. La zona de captura sale sola del navegador de quien la configura |
| Zona horaria por integrante | La ceremonia es una sola para todos: no hay un instante ni un «día N» común si cada uno tiene su calendario. La zona del integrante sirve para mostrar, no para calcular |
| `TIME` en UTC, sin fecha ni zona | El horario de verano corre la hora de pared una hora, y no hay forma de saber en qué fecha local cae una daily temprana al este de UTC |
| Hora local `HH:MM` más la zona | Guarda una hora local, que el DoD de la historia prohíbe, y deja el instante sin anclar |
| Solo días hábiles (lunes a viernes) | Era la regla de la historia; el usuario la descartó porque hay equipos que trabajan el sábado o terminan el sprint en domingo |
| Calendario en UTC para el día N | El día cambiaría a medianoche UTC, que en Tokio son las 9:00 y en Bogotá las 19:00 |
| Paquete `tzdata` de PyPI | Una dependencia más en el lock para algo que la imagen ya trae |

## Consecuencias

- La API es la única autoridad del horario: entrega la próxima ocurrencia ya calculada y la web
  solo la formatea en la zona del navegador, sin recalcular el horario de verano. Mostrar el
  anclaje a alguien de otra zona podría verse corrido una hora en verano; por eso no se hace.
- Si dos Administradores en zonas distintas editan el sprint, manda la zona del último que
  guarda: cambia la hora de pared y el calendario de todo el equipo. La pantalla muestra la zona
  vigente para que no pase inadvertido.
- `N=0` en `not_started` no cabe en `CeremonyContext.sprint_day` (`ge=1`): una ceremonia solo
  se convoca con el sprint en curso. Se revisa en HU-55/56, sin tocar el contrato ahora.
- La validez de una zona depende del tzdata de la imagen (`python:3.12-slim-bookworm` lo trae);
  una imagen base sin él daría `ZoneInfoNotFoundError` en producción. La CI corre en Ubuntu,
  que también lo trae, así que no lo detectaría.
- Agregar festivos o días laborables configurables más adelante es una entrada nueva de las
  funciones (el conjunto de días que cuentan), sin cambiar cómo se guarda la hora.
- Revertir hacia una zona por equipo sería migrar `daily_time_zone` al equipo; los instantes
  UTC de anclaje no cambian.

## Cómo se verifica

- `tests/shared/unit/sprint_calendar/`: las ocurrencias en America/New_York al cruzar el cambio
  de horario de marzo de 2027 conservan las 9:00 de pared; una daily a las 8:00 en Asia/Tokyo
  cae en la fecha de Tokio de cada día del sprint, sábado y domingo incluidos; el día N de M en
  el primer y el último día, el fin de semana, antes del inicio, después del fin y con un
  instante UTC que en la zona de captura todavía es el día anterior.
