// ===== Librerias =====
#include <WiFi.h>
#include <HTTPClient.h>     // Actividad 1: HTTP hacia Flask (local y AWS)
#include <PubSubClient.h>   // Actividad 2: MQTT hacia Mosquitto (AWS)
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
  // Conecta con usuario y clave (el broker no acepta anonimos)
  Serial.println(mqtt.connect(id.c_str(), MQTT_USER, MQTT_PASS) ? "OK" : "fallo");
}

// Envia el JSON por HTTP POST a una URL y devuelve el codigo (201 = OK)
int enviarHTTP(const char* url, const String& json) {
  HTTPClient http;
  http.setTimeout(5000);
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(json);
  http.end();
  return code;
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

    // 3. ACTIVIDAD 1: HTTP al servidor local y al servidor en AWS
  int codeLocal = enviarHTTP(SERVER_URL, json);
  int codeAws   = enviarHTTP(SERVER_URL_AWS, json);

  // 4. ACTIVIDAD 2: MQTT al broker en AWS
  // Topics por variable (estructura bodega1/variable) + lectura completa en JSON
  bool okMqtt = mqtt.publish("bodega1/temperatura", String(t, 1).c_str())
             && mqtt.publish("bodega1/humedad",     String(h, 1).c_str())
             && mqtt.publish("bodega1/estado",      calcularEstado(t, h).c_str())
             && mqtt.publish("bodega1/lecturas",    json.c_str());

  Serial.printf("%s -> Local %d | AWS %d | MQTT %s\n",
                json.c_str(), codeLocal, codeAws, okMqtt ? "OK" : "fallo");
  delay(10000);
}
