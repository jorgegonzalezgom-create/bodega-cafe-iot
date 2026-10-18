# ☕ Bodega de café – Monitoreo IoT

ESP32 + DHT11 mide temperatura y humedad de una bodega de café pergamino y envía los datos por **HTTP POST (JSON)** a un servidor **Flask**, que los guarda en **CSV** y **MySQL**.
Estado **ALERTA** si sale del rango seguro: 15–25 °C y 50–65 % HR.

## Estructura
- `Vagrantfile` → VM Ubuntu 24.04 con Docker (puerto 5000 reenviado)
- `docker-compose.yml` → contenedores `web` (Flask) y `db` (MySQL)
- `server/` → app Flask
- `db/init.sql` → tabla `lecturas`
- `esp32/esp32_bodega/` → código del ESP32
- `data/` → aquí se genera `lecturas.csv`

## Cómo correrlo
1. Copiar `.env.example` como `.env` y poner claves.
2. `vagrant up` → `vagrant ssh` → `cd /vagrant` → `docker compose up -d --build`
3. Abrir `http://localhost:5000`
4. ESP32: copiar `secrets.example.h` como `secrets.h`, poner WiFi e IP del PC, cargar con Arduino IDE (librería *DHT sensor library*).
