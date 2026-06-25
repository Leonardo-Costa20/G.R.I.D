#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <Adafruit_BMP280.h>
#include <ArduinoJson.h>
#include <math.h>

// ================= WIFI =================
const char* ssid     = "iphonedeleo";
const char* password = "123456789";

// ================= MQTT =================
const char* mqtt_server = "79cfe6e1598b447b95c57a4303744c21.s1.eu.hivemq.cloud";
const char* mqtt_user   = "ROVER-1";
const char* mqtt_pass   = "Rover1grid";

WiFiClientSecure espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;

// ================= SENSORES =================
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);
Adafruit_BMP280 bmp;

// ================= PINOS SENSORES =================
const int pinoMQ2 = 34;
#define TRIG_PIN 5
#define ECHO_PIN 18
#define SDA_PIN  21
#define SCL_PIN  22

// ================= PINOS MOTORES =================
#define IN1 26
#define IN2 27
#define ENA 14
#define IN3 25
#define IN4 33
#define ENB 32

// ================= ESTADO =================
float last_ax = 0, last_ay = 0, last_az = 0;

// ================= MOTORES =================
void setMotores(bool a1, bool a2, bool b1, bool b2, int velA, int velB) {
  digitalWrite(IN1, a1);
  digitalWrite(IN2, a2);
  digitalWrite(IN3, b1);
  digitalWrite(IN4, b2);
  ledcWrite(ENA, map(velA, 0, 100, 0, 255));
  ledcWrite(ENB, map(velB, 0, 100, 0, 255));
}

void executarComando(String command, int speed) {
  if (command == "forward") {
    setMotores(LOW, HIGH, LOW, HIGH, speed, speed);
  } else if (command == "backward") {
    setMotores(HIGH, LOW, HIGH, LOW, speed, speed);
  } else if (command == "left") {
    setMotores(LOW, HIGH, HIGH, LOW, speed, speed);
  } else if (command == "right") {
    setMotores(HIGH, LOW, LOW, HIGH, speed, speed);
  } else if (command == "forward-left") {
    setMotores(HIGH, LOW, HIGH, LOW, speed / 2, speed);
  } else if (command == "forward-right") {
    setMotores(HIGH, LOW, HIGH, LOW, speed, speed / 2);
  } else if (command == "backward-left") {
    setMotores(LOW, HIGH, LOW, HIGH, speed / 2, speed);
  } else if (command == "backward-right") {
    setMotores(LOW, HIGH, LOW, HIGH, speed, speed / 2);
  } else if (command == "stop") {
    setMotores(LOW, LOW, LOW, LOW, 0, 0);
  }
  Serial.printf("CMD: %s | Speed: %d\n", command.c_str(), speed);
}

// ================= CALLBACK MQTT =================
void callback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];

  if (String(topic) == "G.R.I.D/drive/command") {
    StaticJsonDocument<128> doc;
    DeserializationError err = deserializeJson(doc, msg);
    if (err) { Serial.println("JSON invalido"); return; }
    String command = doc["command"].as<String>();
    int speed      = doc["speed"] | 0;
    executarComando(command, speed);
  }
}

// ================= RECONNECT =================
void reconnect() {
  while (!client.connected()) {
    Serial.print("MQTT Connecting...");
    String clientId = "ESP32_Rover-";
    clientId += String(random(0xffff), HEX);
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      Serial.println("CONNECTED");
      client.publish("G.R.I.D/status", "online");
      client.subscribe("G.R.I.D/drive/command");
    } else {
      Serial.print("failed, rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  Wire.begin(SDA_PIN, SCL_PIN);

  // Motores
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  ledcAttach(ENA, 1000, 8);
  ledcAttach(ENB, 1000, 8);
  setMotores(LOW, LOW, LOW, LOW, 0, 0);

  // Sensores
  pinMode(pinoMQ2, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi Conectado!");

  // MQTT
  espClient.setInsecure();
  client.setServer(mqtt_server, 8883);
  client.setCallback(callback);

  // ADXL345
  if (!accel.begin()) { Serial.println("Erro ADXL345"); while (1); }
  accel.setRange(ADXL345_RANGE_16_G);

  // BMP280
  if (!bmp.begin(0x76)) Serial.println("BMP280 nao encontrado");

  Serial.println("Sistema iniciado!");
}

// ================= LOOP =================
void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > 300) {
    lastMsg = now;

    // MQ2
    int gas = analogRead(pinoMQ2);

    // ADXL345
    sensors_event_t event;
    accel.getEvent(&event);
    float ax = event.acceleration.x;
    float ay = event.acceleration.y;
    float az = event.acceleration.z;
    float delta = abs(ax - last_ax) + abs(ay - last_ay) + abs(az - last_az);
    char movimento[15];
    strcpy(movimento, delta > 0.8 ? "MOVIMENTO" : "PARADO");
    float tiltX = atan2(ax, sqrt(ay * ay + az * az)) * 180.0 / PI;
    last_ax = ax; last_ay = ay; last_az = az;

    // BMP280
    float temp     = bmp.readTemperature();
    float press    = bmp.readPressure() / 100.0F;
    float altitude = 44330.0 * (1.0 - pow(press / 1013.25, 0.1903));

    // HC-SR04
    digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    long duracao = pulseIn(ECHO_PIN, HIGH, 30000);
    float distancia = duracao * 0.0343 / 2.0;
    if (duracao == 0 || distancia > 400 || distancia < 0) distancia = 0;

    // Publish
    char buf[12];
    sprintf(buf, "%d", gas);           client.publish("G.R.I.D/gas", buf);
    client.publish("G.R.I.D/motion", movimento);
    dtostrf(tiltX,     1, 2, buf);     client.publish("G.R.I.D/tilt", buf);
    dtostrf(temp,      1, 2, buf);     client.publish("G.R.I.D/temperatura", buf);
    dtostrf(press,     1, 2, buf);     client.publish("G.R.I.D/pressao", buf);
    dtostrf(altitude,  1, 2, buf);     client.publish("G.R.I.D/altitude", buf);
    dtostrf(distancia, 1, 2, buf);     client.publish("G.R.I.D/Distancia", buf);

    Serial.printf("GAS:%d | TILT:%.2f° | %s | T:%.2f | P:%.2f | ALT:%.2f | DIST:%.2f cm\n",
      gas, tiltX, movimento, temp, press, altitude, distancia);
  }
}
