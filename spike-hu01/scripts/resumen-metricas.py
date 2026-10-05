#!/usr/bin/env python3
"""Resumen de métricas del spike HU-01 contra UMBRALES.md.

Uso (sin instalar Python en el Mac):
  docker run --rm -v "$PWD":/w -w /w python:3.12-slim python scripts/resumen-metricas.py metrics/*.csv
Opciones:
  --participantes N   participantes por ceremonia para proyectar U6 (por defecto 5)
  --cuota N           caracteres mensuales disponibles en ElevenLabs para comparar U6 (opcional)
  --dias N            dailies por mes para la proyección de U6 (por defecto 22, días hábiles)

"Cumple" = al menos el 90 % de las interacciones dentro del umbral (9 de 10, según UMBRALES.md).
U3 se reporta por separado para USAR_LLM=0 (decide la viabilidad) y USAR_LLM=1 (informativo).
U4 y U5 (costo de GPU) no salen de estos CSV.
"""

import argparse
import csv
import math
import statistics
import sys

UMBRALES = [
    # (id, columna, descripción, límite, estricto)
    ("U1", "u1_transcripcion_s", "fin de voz → transcripción final", 3.0, True),
    ("U2", "u2_tts_ttfb_s", "TTFB de ElevenLabs", 2.0, True),
    ("U3", "u3_aprox_s", "fin de voz → voz de Agilina (aprox.)", 5.0, False),
]
U3_DESEABLE = 3.0
MINIMO_PROTOCOLO = 10


def leer(rutas):
    filas = []
    for ruta in rutas:
        with open(ruta, newline="", encoding="utf-8") as f:
            filas.extend(csv.DictReader(f))
    return filas


def valores(filas, columna):
    return [float(f[columna]) for f in filas if f.get(columna, "") != ""]


def evaluar(vals, limite, estricto):
    dentro = sum(1 for v in vals if (v < limite if estricto else v <= limite))
    necesarias = math.ceil(0.9 * len(vals))
    return dentro, necesarias


def linea(nombre, desc, vals, limite, estricto, extra=""):
    if not vals:
        print(f"{nombre:<10} {desc:<40} sin datos")
        return
    dentro, necesarias = evaluar(vals, limite, estricto)
    signo = "<" if estricto else "≤"
    veredicto = "CUMPLE" if dentro >= necesarias else "NO CUMPLE"
    aviso = "" if len(vals) >= MINIMO_PROTOCOLO else f"  (n={len(vals)} < {MINIMO_PROTOCOLO}: muestra menor al protocolo)"
    print(
        f"{nombre:<10} {desc:<40} mediana {statistics.median(vals):6.2f} s  máx {max(vals):6.2f} s  "
        f"{signo} {limite:g} s: {dentro}/{len(vals)} → {veredicto}{extra}{aviso}"
    )


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", nargs="+")
    p.add_argument("--participantes", type=int, default=5)
    p.add_argument("--cuota", type=int)
    p.add_argument("--dias", type=int, default=22)
    a = p.parse_args()

    filas = leer(a.csv)
    if not filas:
        sys.exit("Sin filas en los CSV indicados.")

    contexto = sorted({(f["entorno"], f["whisper_model"], f["prompt_activo"], f["eleven_model"]) for f in filas})
    print(f"Interacciones: {len(filas)} · salas: {', '.join(sorted({f['sala'] for f in filas}))}")
    for entorno, modelo, prompt, eleven in contexto:
        print(f"  entorno={entorno} whisper={modelo} prompt={prompt} tts={eleven}")
    if len(contexto) > 1:
        print("  AVISO: hay más de una configuración mezclada; el protocolo exige la misma para las 10.")
    print()

    for uid, col, desc, limite, estricto in UMBRALES:
        if uid != "U3":
            linea(uid, desc, valores(filas, col), limite, estricto)
            continue
        for llm in ("0", "1"):
            sub = [f for f in filas if f["usar_llm"] == llm]
            vals = valores(sub, col)
            if not vals:
                continue
            deseable = sum(1 for v in vals if v <= U3_DESEABLE)
            etiqueta = "U3 sin LLM" if llm == "0" else "U3 con LLM"
            linea(etiqueta, desc, vals, limite, estricto, extra=f"  [deseable ≤ {U3_DESEABLE:g} s: {deseable}/{len(vals)}]")

    llm_ttft = valores([f for f in filas if f["usar_llm"] == "1"], "llm_ttft_s")
    if llm_ttft:
        print(f"{'LLM':<10} {'TTFT de Gemini (informativo)':<40} mediana {statistics.median(llm_ttft):6.2f} s  máx {max(llm_ttft):6.2f} s")

    chars = [int(f["caracteres_tts"]) for f in filas if f.get("caracteres_tts", "") != ""]
    if chars:
        por_turno = statistics.median(chars)
        ceremonia = por_turno * a.participantes
        mes = ceremonia * a.dias
        print(
            f"\nU6 · caracteres a ElevenLabs por turno (respuesta + anuncio): mediana {por_turno:g}, máx {max(chars)}, "
            f"total {sum(chars)}"
        )
        print(
            f"     proyección: {a.participantes} participantes → ~{ceremonia:g} por ceremonia (sin saludo inicial); "
            f"{a.dias} dailies → ~{mes:g} al mes"
        )
        if a.cuota:
            print(f"     cuota {a.cuota} caracteres/mes → {'CABE' if mes <= a.cuota else 'NO CABE'}")
        else:
            print("     (pasar --cuota con los caracteres mensuales del plan para el veredicto de U6)")


if __name__ == "__main__":
    main()
