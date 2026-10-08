#!/usr/bin/env python3
"""Analiza corridas de turno manual del spike HU-01 a partir de los logs del agente.

Uso (sin instalar Python en el Mac; jiwer es opcional):
  docker compose logs --since 10m agent > logs/A.txt
  docker run --rm -v "$PWD":/w -w /w python:3.12-slim \
      python analizar_corrida.py logs/A.txt --referencia pruebas/intervencion_larga.txt
  # comparación (control corto frente a corridas largas); la referencia por corrida es opcional:
  docker run --rm -v "$PWD":/w -w /w python:3.12-slim python analizar_corrida.py --comparar \
      C=logs/C.txt A=logs/A.txt:pruebas/intervencion_larga.txt B=logs/B.txt:pruebas/intervencion_larga.txt

Fuentes en el log (JSON, modo start --log-level debug):
- agilina.turnos: vad_fin_voz, whisper_peticion, whisper_respuesta, boton_recibido, espera_terminada,
  commit_invocado, turno_confirmado, agilina_habla (todos con t_ms en epoch ms; ver agent/turnos.py).
- livekit.agents: "received user transcript" (transcript_delay oficial) y el aviso de Silero
  "max_buffered_speech reached" (audio descartado).
Por segmento, la métrica fiable es finvoz→resp_ms (fin de voz del VAD → respuesta de Whisper). El transcript_delay
oficial se mide contra last_speaking_time, que avanza si la persona sigue hablando: en segmentos intermedios marca
casi 0 y en el último puede medirse contra un segmento posterior (p. ej. ruido). Se muestra solo como referencia.
"botón" = momento en que el agente recibe el RPC, no el clic (el cliente muestra la ida y vuelta del RPC).
Ningún número se estima: si un dato no está en el log, se muestra "—".
"""

import argparse
import json
import re
import statistics
import sys
from datetime import datetime

PALABRAS_CLAVE = ["keycloak", "playwright", "whisper", "jira"]


# ---------- lectura del log ----------
def leer_eventos(ruta):
    eventos = []
    with open(ruta, encoding="utf-8", errors="replace") as f:
        for linea in f:
            i = linea.find("{")
            if i < 0:
                continue
            try:
                ev = json.loads(linea[i:])
            except json.JSONDecodeError:
                continue
            if "message" not in ev:
                continue
            if "t_ms" not in ev and "timestamp" in ev:
                ev["t_ms"] = int(datetime.fromisoformat(ev["timestamp"]).timestamp() * 1000)
            eventos.append(ev)
    eventos.sort(key=lambda e: e.get("t_ms", 0))
    return eventos


def turnos(eventos):
    """Un turno por cada botón; la ventana va del turno confirmado anterior a la voz de Agilina siguiente."""
    resultado = []
    previo = 0
    botones = [e for e in eventos if e["message"] == "boton_recibido"]
    for b in botones:
        conf = next((e for e in eventos if e["message"] == "turno_confirmado" and e["t_ms"] >= b["t_ms"]), None)
        fin = conf["t_ms"] if conf else float("inf")
        espera = next((e for e in eventos if e["message"] == "espera_terminada" and e["t_ms"] >= b["t_ms"]), None)
        voz = next((e for e in eventos if e["message"] == "agilina_habla" and conf and e["t_ms"] >= conf["t_ms"]), None)
        ventana = [e for e in eventos if previo < e["t_ms"] <= fin]
        posteriores = [e for e in eventos if e["t_ms"] > fin]
        resultado.append(
            {
                "boton": b,
                "espera": espera,
                "confirmado": conf,
                "voz": voz,
                "segmentos": segmentos(ventana, posteriores),
                "max_en_vuelo": max(
                    [e.get("max_en_vuelo") or e.get("en_vuelo") or 0 for e in ventana if e["name"] == "agilina.turnos"]
                    or [0]
                ),
                "audio_descartado": sum(1 for e in ventana if "max_buffered_speech reached" in e["message"]),
            }
        )
        previo = fin
    return resultado


def segmentos(ventana, posteriores):
    pet = {e["segmento"]: e for e in ventana if e["message"] == "whisper_peticion"}
    fin_voz = {e["segmento"]: e for e in ventana if e["message"] == "vad_fin_voz"}
    resp = {e["segmento"]: e for e in ventana + posteriores if e["message"] == "whisper_respuesta"}
    oficiales = [e for e in ventana if e["message"] == "received user transcript"]
    filas = []
    k = 0
    for n in sorted(pet):
        p, r = pet[n], resp.get(n)
        tardio = r is not None and r in posteriores
        delay = None
        if r is not None and not tardio and r.get("texto") and k < len(oficiales):
            delay = oficiales[k].get("transcript_delay")
            k += 1
        filas.append(
            {
                "n": n,
                "audio_s": p.get("audio_s"),
                "cola_ms": p.get("espera_en_cola_ms"),
                "finvoz_resp_ms": r["t_ms"] - fin_voz[n]["t_ms"] if r is not None and n in fin_voz else None,
                "stt_ms": r.get("stt_ms") if r else None,
                "rtf": r.get("rtf") if r else None,
                "transcript_delay_s": delay,
                "texto": r.get("texto", "") if r else "",
                "tardio": tardio,
            }
        )
    return filas


# ---------- texto ----------
def normalizar(texto):
    """Minúsculas y sin signos de puntuación, conservando tildes y eñes."""
    texto = re.sub(r"[^\w\s]", " ", texto.lower())
    return texto.replace("_", " ").split()


def alinear(ref, hip):
    """Levenshtein por palabras con retroceso: lista de (op, palabras_ref, palabras_hip)."""
    n, m = len(ref), len(hip)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (ref[i - 1] != hip[j - 1]))
    ops, i, j = [], n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (ref[i - 1] != hip[j - 1]):
            ops.append(("igual" if ref[i - 1] == hip[j - 1] else "sust", i - 1, j - 1))
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            ops.append(("omision", i - 1, None))
            i -= 1
        else:
            ops.append(("insercion", None, j - 1))
            j -= 1
    return list(reversed(ops))


def tramos(ops, tipo):
    """Agrupa operaciones consecutivas del mismo tipo."""
    grupos, actual = [], []
    for op in ops:
        if op[0] == tipo:
            actual.append(op)
        elif actual:
            grupos.append(actual)
            actual = []
    if actual:
        grupos.append(actual)
    return grupos


def analizar_texto(referencia, hipotesis):
    ref, hip = normalizar(referencia), normalizar(hipotesis)
    ops = alinear(ref, hip)
    s = sum(1 for o in ops if o[0] == "sust")
    o_ = sum(1 for o in ops if o[0] == "omision")
    i_ = sum(1 for o in ops if o[0] == "insercion")
    try:
        import jiwer

        wer, motor = jiwer.wer(" ".join(ref), " ".join(hip)), "jiwer"
    except ImportError:
        wer, motor = (s + o_ + i_) / len(ref) if ref else 0.0, "Levenshtein propio (jiwer no instalado)"
    omisiones = [" ".join(ref[x[1]] for x in g) for g in tramos(ops, "omision")]
    inserciones, repeticiones = [], []
    for g in tramos(ops, "insercion"):
        j1, j2 = g[0][2], g[-1][2] + 1
        k = j2 - j1
        tramo = hip[j1:j2]
        repetido = hip[max(0, j1 - k) : j1] == tramo or hip[j2 : j2 + k] == tramo  # la copia puede ir antes o después
        (repeticiones if repetido else inserciones).append(" ".join(tramo))
    sustituciones = [(ref[o[1]], hip[o[2]]) for o in ops if o[0] == "sust"]
    claves = {}
    for c in PALABRAS_CLAVE:
        en_ref = [o for o in ops if o[1] is not None and ref[o[1]] == c]
        claves[c] = {
            "referencia": len(en_ref),
            "bien": sum(1 for o in en_ref if o[0] == "igual"),
            "salio_como": [hip[o[2]] if o[2] is not None else "(omitida)" for o in en_ref if o[0] != "igual"],
        }
    return {
        "palabras_ref": len(ref),
        "palabras_hip": len(hip),
        "wer": wer,
        "motor": motor,
        "S": s,
        "D": o_,
        "I": i_,
        "omisiones": omisiones,
        "inserciones": inserciones,
        "repeticiones": repeticiones,
        "sustituciones": sustituciones,
        "claves": claves,
    }


# ---------- salida ----------
def fmt(v, dec=0, suf=""):
    if v is None:
        return "—"
    return f"{v:.{dec}f}{suf}" if isinstance(v, float) or dec else f"{v}{suf}"


def ms(a, b):
    return b["t_ms"] - a["t_ms"] if a and b else None


def reportar_turno(t, referencia=None):
    b, e, c, v = t["boton"], t["espera"], t["confirmado"], t["voz"]
    print(f"  botón recibido de {b.get('caller_identity')} · user_state={b.get('user_state')} · en vuelo={b.get('en_vuelo')}")
    print(f"  Segmentos: {len(t['segmentos'])} · máx. en vuelo: {t['max_en_vuelo']}"
          + (f" · AUDIO DESCARTADO por max_buffered_speech: {t['audio_descartado']} aviso(s)" if t["audio_descartado"] else ""))
    print("    #   audio_s  finvoz→resp_ms  cola_ms  stt_ms    rtf  td_oficial_s  texto")
    for s in t["segmentos"]:
        texto = " ".join(s["texto"].split())
        texto = (texto[:60] + "…") if len(texto) > 60 else texto
        marca = "  [TARDÍO: llegó después del commit]" if s["tardio"] else ""
        print(f"   {s['n']:>2} {fmt(s['audio_s'],2):>8} {fmt(s['finvoz_resp_ms']):>15} {fmt(s['cola_ms']):>8} "
              f"{fmt(s['stt_ms']):>7} {fmt(s['rtf'],3):>6} {fmt(s['transcript_delay_s'],3):>13}  {texto}{marca}"
              + ("  [sin texto]" if s["stt_ms"] is not None and not s["texto"] else ""))
    if e:
        print(f"  Espera tras el botón: VAD {e['espera_vad_ms']} ms + Whisper {e['espera_whisper_ms']} ms = "
              f"{e['espera_total_ms']} ms" + (f" · TIMEOUT ({e['timeout_por']}, tope {e['espera_max_s']} s)" if e["timeout"] else ""))
    print(f"  ► botón → turno confirmado: {fmt(ms(b, c), suf=' ms')}")
    print(f"  ► botón → inicio de la voz de Agilina: {fmt(ms(b, v), suf=' ms')}")
    if referencia is not None and c:
        a = analizar_texto(referencia, c.get("transcripcion", ""))
        print(f"  Texto: {a['palabras_ref']} palabras de referencia, {a['palabras_hip']} transcritas · "
              f"WER {a['wer']:.1%} (S={a['S']} D={a['D']} I={a['I']}; {a['motor']})")
        print(f"    omisiones: {a['omisiones'] or 'ninguna'}")
        print(f"    repeticiones: {a['repeticiones'] or 'ninguna'}")
        print(f"    inserciones (posibles alucinaciones): {a['inserciones'] or 'ninguna'}")
        print(f"    sustituciones: {[f'{r}→{h}' for r, h in a['sustituciones']] or 'ninguna'}")
        for c_, d in a["claves"].items():
            estado = "no está en la referencia" if not d["referencia"] else f"{d['bien']}/{d['referencia']} bien"
            print(f"    {c_}: {estado}" + (f" (salió como {d['salio_como']})" if d["salio_como"] else ""))


def cargar_referencia(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("log", nargs="?")
    p.add_argument("--referencia")
    p.add_argument("--comparar", nargs="+", metavar="NOMBRE=LOG[:REFERENCIA]")
    a = p.parse_args()

    if a.comparar:
        filas = []
        for item in a.comparar:
            nombre, _, resto = item.partition("=")
            log, _, ref = resto.partition(":")
            ts = turnos(leer_eventos(log))
            print(f"=== Corrida {nombre} ({log}): {len(ts)} turno(s)")
            for t in ts:
                reportar_turno(t, cargar_referencia(ref) if ref else None)
                # último segmento con texto entregado antes del commit (el que define la espera final)
                con_texto = [s for s in t["segmentos"] if s["texto"] and not s["tardio"]]
                ult = con_texto[-1] if con_texto else {}
                filas.append((nombre, t, ult))
            print()
        print("=== Comparación (un renglón por turno; n = número de turnos por corrida)")
        print("corrida  segs  audio_total_s  máx_vuelo  esp_VAD_ms  esp_Whisper_ms  botón→confirmado_ms  botón→voz_ms  "
              "últ_seg_audio_s  últ_seg_finvoz→resp_ms  timeout")
        for nombre, t, ult in filas:
            e = t["espera"] or {}
            audio = [s["audio_s"] for s in t["segmentos"] if s["audio_s"] is not None]
            print(f"{nombre:<8} {len(t['segmentos']):>4} {fmt(sum(audio) if audio else None,1):>14} {t['max_en_vuelo']:>10} "
                  f"{fmt(e.get('espera_vad_ms')):>11} {fmt(e.get('espera_whisper_ms')):>15} "
                  f"{fmt(ms(t['boton'], t['confirmado'])):>20} {fmt(ms(t['boton'], t['voz'])):>13} "
                  f"{fmt(ult.get('audio_s'),2):>16} {fmt(ult.get('finvoz_resp_ms')):>23} {'sí' if e.get('timeout') else 'no':>8}")
        print("(últ_seg = último segmento con texto antes del commit)")
        por_corrida = {}
        for nombre, t, _ in filas:
            v = ms(t["boton"], t["confirmado"])
            if v is not None:
                por_corrida.setdefault(nombre, []).append(v)
        for nombre, vals in por_corrida.items():
            if len(vals) > 1:
                print(f"{nombre}: botón→confirmado mediana {statistics.median(vals)} ms, n={len(vals)}")
        return

    if not a.log:
        sys.exit("Indica un log o usa --comparar.")
    ts = turnos(leer_eventos(a.log))
    if not ts:
        sys.exit("No hay eventos boton_recibido en el log: ¿el agente corría con MODO_TURNO=manual y --log-level debug?")
    ref = cargar_referencia(a.referencia) if a.referencia else None
    for k, t in enumerate(ts, 1):
        print(f"=== Turno {k}")
        reportar_turno(t, ref)


if __name__ == "__main__":
    main()
