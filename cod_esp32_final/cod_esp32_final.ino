#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <Adafruit_BMP280.h>
#include <math.h>

// ================= WIFI =================
const char* ssid = "-------";
const char* password = "-------";

// ================= MQTT =================
const char* mqtt_server = "---------------------------------------";
const char* mqtt_user = "----------";
const char* mqtt_pass = "--------";

WiFiClientSecure espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;

// ================= SENSORES =================
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);
Adafruit_BMP280 bmp;

// ================= PINOS =================
const int pinoMQ2 = 34;
#define TRIG_PIN 5
#define ECHO_PIN 18
#define SDA_PIN 21
#define SCL_PIN 22

// ================= MOVIMENTO =================
float last_ax = 0;
float last_ay = 0;
float last_az = 0;

void setup() {
  Serial.begin(115200);
  Wire.begin(SDA_PIN, SCL_PIN);

  pinMode(pinoMQ2, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Conectado!");

  // MQTT
  espClient.setInsecure();
  client.setServer(mqtt_server, 8883);

  // ADXL345
  if (!accel.begin()) {
    Serial.println("Erro ADXL345");
    while (1);
  }
  accel.setRange(ADXL345_RANGE_16_G);

  // BMP280
  if (!bmp.begin(0x76)) {
    Serial.println("BMP280 nao encontrado");
  }

  Serial.println("Sistema iniciado!");
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("MQTT Connecting...");
    String clientId = "ESP32_Rover-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      Serial.println("CONNECTED");
      client.publish("G.R.I.D/status", "online");
      client.subscribe("G.R.I.D/#");
    } else {
      Serial.print("failed, rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();

  if (now - lastMsg > 300) {
    lastMsg = now;

    // ================= MQ2 =================
    int gas = analogRead(pinoMQ2);

    // ================= ADXL345 =================
    sensors_event_t event;
    accel.getEvent(&event);

    float ax = event.acceleration.x;
    float ay = event.acceleration.y;
    float az = event.acceleration.z;

    float delta = abs(ax - last_ax) + abs(ay - last_ay) + abs(az - last_az);

    char movimento[15];
    if (delta > 0.8) {
      strcpy(movimento, "MOVIMENTO");
    } else {
      strcpy(movimento, "PARADO");
    }

    // Inclinação em graus (frente/trás)
    float tiltX = atan2(ax, sqrt(ay * ay + az * az)) * 180.0 / PI;

    last_ax = ax;
    last_ay = ay;
    last_az = az;

    // ================= BMP280 =================
    float temp     = bmp.readTemperature();
    float press    = bmp.readPressure() / 100.0F;
    float altitude = 44330.0 * (1.0 - pow(press / 1013.25, 0.1903));

    // ================= HC-SR04 =================
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);

    long duracao  = pulseIn(ECHO_PIN, HIGH, 30000);
    float distancia = duracao * 0.0343 / 2.0;

    if (duracao == 0 || distancia > 400 || distancia < 0) {
      distancia = 0;
    }

    // ================= CONVERSÃO MQTT =================
    char msgGas[10];
    char msgTemp[10];
    char msgPress[12];
    char msgAlt[12];
    char msgDist[10];
    char msgTilt[10];

    sprintf(msgGas, "%d", gas);
    dtostrf(temp,      1, 2, msgTemp);
    dtostrf(press,     1, 2, msgPress);
    dtostrf(altitude,  1, 2, msgAlt);
    dtostrf(distancia, 1, 2, msgDist);
    dtostrf(tiltX,     1, 2, msgTilt);  // número simples ex: "10.45"

    // ================= MQTT PUBLISH =================
    client.publish("G.R.I.D/gas",        msgGas);
    client.publish("G.R.I.D/motion",     movimento);
    client.publish("G.R.I.D/tilt",       msgTilt);
    client.publish("G.R.I.D/temperatura",msgTemp);
    client.publish("G.R.I.D/pressao",    msgPress);
    client.publish("G.R.I.D/altitude",   msgAlt);
    client.publish("G.R.I.D/Distancia",  msgDist);

    // ================= DEBUG =================
    Serial.printf(
      "GAS:%d | TILT:%.2f° | %s | T:%.2f | P:%.2f | ALT:%.2f | DIST:%.2f cm\n",
      gas, tiltX, movimento, temp, press, altitude, distancia
    );
  }
}
