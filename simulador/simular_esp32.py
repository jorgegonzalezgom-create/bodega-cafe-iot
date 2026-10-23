"""simular_esp32.py: imita al ESP32 de la bodega para probar sin el hardware.

Envia el mismo JSON que el ESP32 a POST /api/lecturas. Solo usa librerias que
ya vienen con Python (no hay que instalar nada).

    python simulador/simular_esp32.py                         # cada 10 s, sin fin
    python simulador/simular_esp32.py --cantidad 30 --intervalo 1 --picos
    python simulador/simular_esp32.py --url http://192.168.1.50:5000
"""

import argparse
import json
import random
import time
import urllib.error
import urllib.request


def enviar(url, dispositivo, temp, hum):
    cuerpo = json.dumps({"dispositivo": dispositivo, "temperatura": round(temp, 1), "humedad": round(hum, 1)})
    req = urllib.request.Request(
        url.rstrip("/") + "/api/lecturas",
        data=cuerpo.encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.load(e)
        except ValueError:   # la respuesta de error no era JSON
            return e.code, {"error": e.reason}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default="http://localhost:5000", help="direccion del servidor")
    p.add_argument("--dispositivo", default="esp32-simulado")
    p.add_argument("--intervalo", type=float, default=10, help="segundos entre lecturas (el ESP32 usa 10)")
    p.add_argument("--cantidad", type=int, default=0, help="cuantas lecturas enviar (0 = sin fin)")
    p.add_argument("--picos", action="store_true", help="de vez en cuando sube la humedad por encima de 65 %% (ALERTA)")
    args = p.parse_args()

    temp, hum = 21.0, 58.0
    n = 0
    while args.cantidad == 0 or n < args.cantidad:
        # Cambios suaves alrededor de condiciones normales de bodega
        temp = min(max(temp + random.uniform(-0.3, 0.3), 17), 27)
        hum = min(max(hum + random.uniform(-0.8, 0.8), 52), 63)
        hum_enviada = hum + (random.uniform(4, 10) if args.picos and random.random() < 0.2 else 0)

        try:
            codigo, resp = enviar(args.url, args.dispositivo, temp, hum_enviada)
            print(f"{codigo}  T={temp:4.1f} C  H={hum_enviada:4.1f} %  -> {resp.get('estado', resp.get('error'))}", flush=True)
        except urllib.error.URLError as e:
            print(f"No se pudo conectar a {args.url}: {e.reason}", flush=True)

        n += 1
        if args.cantidad == 0 or n < args.cantidad:
            time.sleep(args.intervalo)


if __name__ == "__main__":
    main()
