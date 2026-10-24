// ===== Librerias =====
#include <WiFi.h>
#include <HTTPClient.h>     // Parte 1: HTTP hacia Flask (local)
#include <PubSubClient.h>   // Parte 2: MQTT hacia Mosquitto (AWS)
#include <DHT.h>
#include "secrets.h"        // WiFi, URL local e IP de AWS (no se sube a GitHub)

const char* topicLecturas = "bodegacafe/lecturas";   // tema que lee Telegraf

// ===== Sensor =====
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

// Regla del cafe: igual que en el servidor Flask
String calcularEstado(float t, float h) {
  return (t >= 15 && t <= 25 && h >= 50 && h <= 65) ? "OK" : "ALERTA";
}

void conectarWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Conectando WiFi");
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.print("\nWiFi OK. IP del ESP32: ");
  Serial.println(WiFi.localIP());
}

// Intenta conectar a MQTT una vez (no bloquea si AWS esta apagado)
void conectarMQTT() {
  if (mqtt.connected()) return;
  String id = "esp32-" + String((uint32_t)ESP.getEfuseMac(), HEX);
  Serial.print("Conectando MQTT AWS... ");
  Serial.println(mqtt.connect(id.c_str()) ? "OK" : "fallo");
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  conectarWiFi();
  mqtt.setServer(MQTT_SERVER, 1883);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) conectarWiFi();   // reconexion WiFi
  conectarMQTT();                                      // reconexion MQTT
  mqtt.loop();

  // 1. Leer sensor
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (isnan(t) || isnan(h)) { Serial.println("Error sensor"); delay(2000); return; }

  // 2. Armar JSON (incluye estado para Telegraf/InfluxDB)
  String json = "{\"dispositivo\":\"esp32-01\",\"temperatura\":" + String(t, 1) +
                ",\"humedad\":" + String(h, 1) +
                ",\"estado\":\"" + calcularEstado(t, h) + "\"}";

  // 3. PARTE 1: HTTP POST al servidor local (Flask)
  HTTPClient http;
  http.setTimeout(3000);                 // si la VM esta apagada, no se queda pegado
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(json);
  http.end();

  // 4. PARTE 2: MQTT publish al broker en AWS
  bool okMqtt = mqtt.publish(topicLecturas, json.c_str());

  Serial.printf("%s -> HTTP %d | MQTT %s\n", json.c_str(), code, okMqtt ? "OK" : "fallo");
  delay(10000);
}
