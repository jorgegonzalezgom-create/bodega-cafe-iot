-- init.sql: crea la tabla donde se guardan las lecturas del sensor.
-- MySQL lo ejecuta automaticamente solo la primera vez que arranca.
CREATE TABLE IF NOT EXISTS lecturas (
  id INT AUTO_INCREMENT PRIMARY KEY,  -- numero consecutivo de cada lectura
  fecha DATETIME,                     -- cuando llego el dato
  dispositivo VARCHAR(30),            -- que ESP32 lo envio (ej. esp32-01)
  temperatura FLOAT,                  -- grados C
  humedad FLOAT,                      -- % humedad relativa
  estado VARCHAR(10)                  -- OK o ALERTA
);
