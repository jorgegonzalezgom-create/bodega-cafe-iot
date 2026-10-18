# app.py: servidor web Flask de la bodega de cafe.
#   - Recibe las lecturas del ESP32 en /api/lecturas (POST)
#   - Las guarda en un archivo CSV y en MySQL
#   - Muestra las ultimas lecturas en / (pagina web)

from flask import Flask, request, jsonify
from datetime import datetime
from zoneinfo import ZoneInfo   # para usar la hora de Colombia
import csv, os, pymysql

app = Flask(__name__)   # crea la aplicacion web

# Ruta del CSV (data/ esta conectada con la carpeta del proyecto en Windows)
CSV_FILE = "data/lecturas.csv"

# Datos de conexion a MySQL (vienen de docker-compose.yml / .env)
DB = dict(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME"),
)


# Regla del caso de uso: rango seguro para almacenar cafe pergamino
#   Temperatura: 15 a 25 C   |   Humedad: 50 a 65 %
def calcular_estado(t, h):
    return "OK" if 15 <= t <= 25 and 50 <= h <= 65 else "ALERTA"


# ---------- RUTA 1: el ESP32 envia los datos aqui ----------
@app.route("/api/lecturas", methods=["POST"])
def recibir():
    # 1. Leer el JSON que envio el ESP32: {"temperatura":24.5,"humedad":60}
    d = request.get_json()
    t, h = float(d["temperatura"]), float(d["humedad"])
    disp = d.get("dispositivo", "esp32-01")
    fecha = datetime.now(ZoneInfo("America/Bogota")).strftime("%Y-%m-%d %H:%M:%S")
    estado = calcular_estado(t, h)

    # 2. Guardar en el CSV (si el archivo no existe, primero escribe el encabezado)
    nuevo = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["fecha", "dispositivo", "temperatura", "humedad", "estado"])
        w.writerow([fecha, disp, t, h, estado])

    # 3. Guardar en MySQL
    con = pymysql.connect(**DB)
    with con:
        with con.cursor() as c:
            c.execute(
                "INSERT INTO lecturas (fecha, dispositivo, temperatura, humedad, estado) "
                "VALUES (%s, %s, %s, %s, %s)",
                (fecha, disp, t, h, estado),
            )
        con.commit()   # confirma el guardado

    # 4. Mostrar en el log (se ve con: docker compose logs -f web)
    print(f"{fecha} {disp} T={t} H={h} {estado}", flush=True)

    # 5. Responder al ESP32: 201 = "creado correctamente"
    return jsonify(ok=True, estado=estado), 201


# ---------- RUTA 2: pagina web para ver los datos ----------
@app.route("/")
def inicio():
    # Consulta las ultimas 20 lecturas en MySQL
    con = pymysql.connect(**DB)
    with con:
        with con.cursor() as c:
            c.execute("SELECT fecha, temperatura, humedad, estado FROM lecturas ORDER BY id DESC LIMIT 20")
            filas = c.fetchall()

    # Arma una tabla HTML sencilla
    html = "<h1>Bodega de cafe</h1><table border=1><tr><th>Fecha</th><th>T C</th><th>HR %</th><th>Estado</th></tr>"
    for f in filas:
        html += f"<tr><td>{f[0]}</td><td>{f[1]}</td><td>{f[2]}</td><td>{f[3]}</td></tr>"
    return html + "</table>"


# Arranca el servidor escuchando en todas las interfaces, puerto 5000
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
