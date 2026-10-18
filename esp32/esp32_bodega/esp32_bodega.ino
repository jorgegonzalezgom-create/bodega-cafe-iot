// ===== Librerias =====
#include <WiFi.h>         // conexion WiFi
#include <HTTPClient.h>   // enviar peticiones HTTP al servidor
#include <DHT.h>          // leer el sensor DHT11

// ===== Configuracion de red =====
// Los datos reales (WiFi e IP del servidor) estan en secrets.h, que NO se sube a GitHub
#include "secrets.h"
const char* ssid      = WIFI_SSID;
const char* password  = WIFI_PASS;
const char* serverUrl = SERVER_URL;

// ===== Sensor =====
#define DHTPIN 4          // cable de datos en D4
#define DHTTYPE DHT11     // sensor azul
DHT dht(DHTPIN, DHTTYPE);

// Conecta al WiFi y espera hasta lograrlo
void conectarWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Conectando WiFi");
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.print("\nConectado. IP del ESP32: ");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);   // monitor serial
  dht.begin();            // arranca el sensor
  conectarWiFi();
}

void loop() {
  // Si se cayo el WiFi, reconecta (conexion estable = criterio de evaluacion)
  if (WiFi.status() != WL_CONNECTED) conectarWiFi();

  // 1. Leer el sensor
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (isnan(t) || isnan(h)) { Serial.println("Error sensor"); delay(2000); return; }

  // 2. Armar el JSON: {"dispositivo":"esp32-01","temperatura":24.5,"humedad":60.0}
  String json = "{\"dispositivo\":\"esp32-01\",\"temperatura\":" + String(t, 1) +
                ",\"humedad\":" + String(h, 1) + "}";

  // 3. Enviarlo al servidor por HTTP POST
  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(json);   // 201 = guardado OK
  Serial.printf("Enviado %s -> HTTP %d\n", json.c_str(), code);
  http.end();

  delay(10000);   // espera 10 segundos antes de la siguiente lectura
}
