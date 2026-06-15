#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <Adafruit_BMP280.h>
#include <math.h>
#include <ArduinoJson.h>

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

// ================= PONTE H (L298N) — Tração Diferencial =================
// 2 motores lado esquerdo → canal A (ENA, IN1, IN2)
// 2 motores lado direito  → canal B (ENB, IN3, IN4)
#define ENA 14
#define IN1 27
#define IN2 26
#define IN3 25
#define IN4 33
#define ENB 32

// ================= MOVIMENTO =================
float last_ax = 0;
float last_ay = 0;
float last_az = 0;

// --- Núcleo do controlo diferencial ---
// left/right: -255..+255 (negativo = ré, positivo = frente)
void setMotores(int left, int right) {
  left  = constrain(left,  -255, 255);
  right = constrain(right, -255, 255);

  // Canal A — lado esquerdo
  if (left >= 0) {
    digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  } else {
    digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
  }
  analogWrite(ENA, abs(left));

  // Canal B — lado direito
  if (right >= 0) {
    digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
  } else {
    digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
  }
  analogWrite(ENB, abs(right));
}

void pararMotor() { setMotores(0, 0); }

// --- Curvas suaves com mistura proporcional ---
// forward-left:   esquerda 60%, direita 100%
// forward-right:  esquerda 100%, direita 60%
// backward-left:  esquerda -60%, direita -100%
// backward-right: esquerda -100%, direita -60%
// left (pivot):   esquerda -100%, direita +100%
// right (pivot):  esquerda +100%, direita -100%

void frente(int pwm)      { setMotores(pwm, pwm); }
void tras(int pwm)        { setMotores(-pwm, -pwm); }
void pivotEsq(int pwm)    { setMotores(-pwm, pwm); }
void pivotDir(int pwm)    { setMotores(pwm, -pwm); }
void curvaFrenteEsq(int pwm) { setMotores(pwm * 0.6, pwm); }
void curvaFrenteDir(int pwm) { setMotores(pwm, pwm * 0.6); }
void curvaTrasEsq(int pwm)   { setMotores(-pwm * 0.6, -pwm); }
void curvaTrasDir(int pwm)   { setMotores(-pwm, -pwm * 0.6); }

void callback(char* topic, byte* payload, unsigned int length) {
  if (strcmp(topic, "G.R.I.D/drive/command") != 0) return;

  char msg[length + 1];
  memcpy(msg, payload, length);
  msg[length] = '\0';

  StaticJsonDocument<128> doc;
  DeserializationError err = deserializeJson(doc, msg);
  if (err) return;

  const char* command = doc["command"];
  int speed = constrain(doc["speed"] | 60, 0, 100);
  int pwm = map(speed, 0, 100, 0, 255);

  if      (strcmp(command, "forward")        == 0)  frente(pwm);
  else if (strcmp(command, "backward")       == 0)  tras(pwm);
  else if (strcmp(command, "left")           == 0)  pivotEsq(pwm);
  else if (strcmp(command, "right")          == 0)  pivotDir(pwm);
  else if (strcmp(command, "forward-left")   == 0)  curvaFrenteEsq(pwm);
  else if (strcmp(command, "forward-right")  == 0)  curvaFrenteDir(pwm);
  else if (strcmp(command, "backward-left")  == 0)  curvaTrasEsq(pwm);
  else if (strcmp(command, "backward-right") == 0)  curvaTrasDir(pwm);
  else if (strcmp(command, "stop")           == 0)  pararMotor();
}

void setup() {
  Serial.begin(115200);
  Wire.begin(SDA_PIN, SCL_PIN);

  pinMode(pinoMQ2, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // Motor pins
  pinMode(ENA, OUTPUT); pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT); pinMode(ENB, OUTPUT);
  pararMotor();

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
  client.setCallback(callback);

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
