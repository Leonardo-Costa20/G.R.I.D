#include <Arduino.h>
#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"
#include "board_config.h"

// Variáveis para os handlers do servidor
httpd_handle_t camera_httpd = NULL;
httpd_handle_t stream_httpd = NULL;

// Dados do WiFi
const char *ssid = "-------";
const char *password = "-------";

// Funções que estão no outro ficheiro
void startCameraServer();
void setupLedFlash();

void setup() {
  Serial.begin(115200);
  
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  
  // Otimização para Fluidez / Estabilidade
  config.xclk_freq_hz = 10000000; 
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_CIF;    // Resolução equilibrada (melhor que QVGA)
  config.jpeg_quality = 12;            // 10-12 é o ponto ideal para WiFi
  config.fb_count = 2;                 // Buffer duplo para evitar soluços no vídeo
  config.grab_mode = CAMERA_GRAB_LATEST;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) { return; }

  sensor_t * s = esp_camera_sensor_get();
  
  // ==========================================================
  // AJUSTES MANUAIS DE IMAGEM (Podes alterar aqui)
  // ==========================================================
s->set_brightness(s, 1);      // Aumenta um pouco o brilho
s->set_contrast(s, 1);        // Mantém
s->set_saturation(s, 2);      // Aumenta a saturação (cores mais vivas) — estava em 0
s->set_whitebal(s, 1);        // Mantém
s->set_exposure_ctrl(s, 1);   // Mantém
s->set_aec2(s, 1);            // Mantém
s->set_gain_ctrl(s, 1);       // Mantém
s->set_vflip(s, 0);           
s->set_hmirror(s, 0);
  // ==========================================================

  setupLedFlash();

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  // Desativa o modo de poupança de energia do WiFi.
  // Sem isto, o ESP32 entra em "modem sleep" periodicamente, o que
  // causa atrasos no envio dos frames do stream e leva o handler
  // a falhar -> imagem fica "congelada" no último frame recebido.
  WiFi.setSleep(false);

  startCameraServer();
  
  Serial.println("\nWiFi OK!");
  Serial.print("Acede a: http://");
  Serial.println(WiFi.localIP());
}

void loop() {
  delay(1); // O servidor corre em background
}
