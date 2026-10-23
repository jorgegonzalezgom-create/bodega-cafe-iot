# app.py: servidor web Flask de la bodega de cafe.
#   - Recibe las lecturas del ESP32 en /api/lecturas (POST)
#   - Las guarda en MySQL y en un archivo CSV
#   - Muestra un tablero en / que se actualiza solo cada 5 segundos

from flask import Flask, request, jsonify, render_template, send_file
from datetime import datetime
from zoneinfo import ZoneInfo   # para usar la hora de Colombia
from threading import Lock
import csv, math, os, pymysql

app = Flask(__name__)   # crea la aplicacion web

ZONA = ZoneInfo("America/Bogota")

# Ruta del CSV (data/ esta conectada con la carpeta del proyecto en Windows)
CSV_FILE = "data/lecturas.csv"
csv_lock = Lock()   # evita que dos lecturas escriban el CSV al mismo tiempo

# Datos de conexion a MySQL (vienen de docker-compose.yml / .env)
DB = dict(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME"),
)


# Regla del caso de uso: rango seguro para almacenar cafe pergamino
#   Temperatura: 15 a 25 C   |   Humedad: 50 a 65 %
UMBRALES = dict(temp_min=15, temp_max=25, hum_min=50, hum_max=65)


def calcular_estado(t, h):
    u = UMBRALES
    ok = u["temp_min"] <= t <= u["temp_max"] and u["hum_min"] <= h <= u["hum_max"]
    return "OK" if ok else "ALERTA"


# Revisa que el JSON del ESP32 tenga sentido antes de guardarlo.
# Devuelve (datos, None) si esta bien, o (None, "mensaje de error") si no.
def validar(d):
    if not isinstance(d, dict):
        return None, "se esperaba un JSON con temperatura y humedad"
    try:
        t, h = float(d["temperatura"]), float(d["humedad"])
    except (KeyError, TypeError, ValueError):
        return None, "temperatura y humedad son obligatorias y deben ser numeros"
    # NaN o infinito: el sensor fallo (MySQL no los acepta)
    if not (math.isfinite(t) and math.isfinite(h)):
        return None, "lectura invalida del sensor (NaN)"
    # Limites fisicos del sensor: fuera de esto es un error, no una alerta
    if not (-40 <= t <= 80 and 0 <= h <= 100):
        return None, "valores fuera del rango que puede medir el sensor"
    disp = str(d.get("dispositivo") or "esp32-01")
    if len(disp) > 30:   # la columna "dispositivo" es VARCHAR(30)
        return None, "el nombre del dispositivo tiene mas de 30 caracteres"
    return (disp, round(t, 1), round(h, 1)), None


# Si MySQL no responde, se contesta 503 ("no disponible") en JSON en vez de un error 500
@app.errorhandler(pymysql.MySQLError)
def bd_no_disponible(e):
    print(f"Error de MySQL: {e}", flush=True)
    return jsonify(ok=False, error="la base de datos no esta disponible"), 503


# ---------- RUTA 1: el ESP32 envia los datos aqui ----------
@app.route("/api/lecturas", methods=["POST"])
def recibir():
    # 1. Leer y revisar el JSON que envio el ESP32: {"temperatura":24.5,"humedad":60}
    datos, error = validar(request.get_json(silent=True))
    if error:
        return jsonify(ok=False, error=error), 400   # 400 = "datos mal enviados"
    disp, t, h = datos
    fecha = datetime.now(ZONA).strftime("%Y-%m-%d %H:%M:%S")
    estado = calcular_estado(t, h)

    # 2. Guardar en MySQL (primero la BD: si falla, no queda una fila suelta en el CSV)
    con = pymysql.connect(**DB)
    with con:
        with con.cursor() as c:
            c.execute(
                "INSERT INTO lecturas (fecha, dispositivo, temperatura, humedad, estado) "
                "VALUES (%s, %s, %s, %s, %s)",
                (fecha, disp, t, h, estado),
            )
        con.commit()   # confirma el guardado

    # 3. Guardar en el CSV (si el archivo no existe, primero escribe el encabezado)
    with csv_lock:
        nuevo = not os.path.exists(CSV_FILE)
        with open(CSV_FILE, "a", newline="") as f:
            w = csv.writer(f)
            if nuevo:
                w.writerow(["fecha", "dispositivo", "temperatura", "humedad", "estado"])
            w.writerow([fecha, disp, t, h, estado])

    # 4. Mostrar en el log (se ve con: docker compose logs -f web)
    print(f"{fecha} {disp} T={t} H={h} {estado}", flush=True)

    # 5. Responder al ESP32: 201 = "creado correctamente"
    return jsonify(ok=True, estado=estado), 201


# ---------- RUTA 2: ultimas lecturas en JSON (las usa el tablero) ----------
@app.route("/api/lecturas", methods=["GET"])
def listar():
    limite = min(max(request.args.get("limite", 50, type=int), 1), 500)
    con = pymysql.connect(**DB, cursorclass=pymysql.cursors.DictCursor)
    with con:
        with con.cursor() as c:
            c.execute(
                "SELECT id, fecha, dispositivo, temperatura, humedad, estado "
                "FROM lecturas ORDER BY id DESC LIMIT %s",
                (limite,),
            )
            filas = c.fetchall()
    # La fecha se guarda en hora de Colombia: se envia con su zona (-05:00)
    for f in filas:
        f["fecha"] = f["fecha"].replace(tzinfo=ZONA).isoformat()
    return jsonify(filas)


# ---------- RUTA 3: descargar el CSV completo ----------
@app.route("/api/lecturas.csv")
def descargar_csv():
    if not os.path.exists(CSV_FILE):
        return jsonify(ok=False, error="todavia no hay lecturas"), 404
    return send_file(os.path.abspath(CSV_FILE), mimetype="text/csv",
                     as_attachment=True, download_name="lecturas.csv")


# ---------- RUTA 4: revisar que el servidor y la BD respondan ----------
@app.route("/health")
def salud():
    try:
        pymysql.connect(**DB, connect_timeout=3).close()
        return jsonify(status="ok", db=True)
    except pymysql.MySQLError:
        return jsonify(status="error", db=False), 503


# ---------- RUTA 5: tablero web ----------
@app.route("/")
def inicio():
    # La pagina se arma en templates/index.html; los datos los pide sola a /api/lecturas
    return render_template("index.html", umbrales=UMBRALES)


# Arranca el servidor escuchando en todas las interfaces, puerto 5000
if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
