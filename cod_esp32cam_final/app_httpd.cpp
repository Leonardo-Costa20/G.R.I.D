#include "Arduino.h"
#include "esp_http_server.h"
#include "esp_camera.h"

extern httpd_handle_t camera_httpd;
extern httpd_handle_t stream_httpd;

#define FLASH_GPIO_NUM 4 // PINO DO LED FLASH (Altera se for diferente)

#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

bool flash_on = false;

static esp_err_t flash_handler(httpd_req_t *req) {
    flash_on = !flash_on;
    digitalWrite(FLASH_GPIO_NUM, flash_on ? HIGH : LOW);
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    return httpd_resp_send(req, NULL, 0);
}

static esp_err_t stream_handler(httpd_req_t *req) {
    camera_fb_t * fb = NULL;
    esp_err_t res = ESP_OK;
    char * part_buf[64];
    res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
    if(res != ESP_OK) return res;

    while(true){
        fb = esp_camera_fb_get();
        if (!fb) { res = ESP_FAIL; } 
        else {
            res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
            if(res == ESP_OK){
                size_t hlen = snprintf((char *)part_buf, 64, _STREAM_PART, fb->len);
                res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
            }
            if(res == ESP_OK) res = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
            esp_camera_fb_return(fb);
        }
        if(res != ESP_OK) break;
    }
    return res;
}

static esp_err_t index_handler(httpd_req_t *req) {
    httpd_resp_set_type(req, "text/html");
    const char* html = 
        "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<style>body{background:#020617;color:#f8fafc;font-family:sans-serif;text-align:center;padding:20px}"
        ".container{max-width:600px;margin:auto}"
        "img{width:100%;border-radius:20px;border:2px solid #1e293b;box-shadow:0 20px 50px rgba(0,0,0,0.7)}"
        "button{background:#38bdf8;color:#020617;border:none;padding:20px;border-radius:15px;width:100%;font-weight:bold;font-size:18px;margin-top:20px;cursor:pointer;box-shadow:0 4px 0 #0284c7}button:active{transform:translateY(4px);box-shadow:none}</style></head>"
        "<body><div class='container'><h2>ROVER CAM 🛰️</h2><img src='' id='photo'>"
        "<button onclick=\"fetch('/flash')\">ALTERNAR FLASH 🔦</button></div>"
        "<script>window.onload=function(){document.getElementById('photo').src='http://'+window.location.hostname+':81/stream';};</script></body></html>";
    return httpd_resp_send(req, html, strlen(html));
}

void startCameraServer() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 80;
    config.ctrl_port = 32768;
    if (httpd_start(&camera_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(camera_httpd, new httpd_uri_t{ .uri = "/", .method = HTTP_GET, .handler = index_handler });
        httpd_register_uri_handler(camera_httpd, new httpd_uri_t{ .uri = "/flash", .method = HTTP_GET, .handler = flash_handler });
    }
    config.server_port = 81;
    config.ctrl_port = 32769;
    if (httpd_start(&stream_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, new httpd_uri_t{ .uri = "/stream", .method = HTTP_GET, .handler = stream_handler });
    }
}

void setupLedFlash() {
    pinMode(FLASH_GPIO_NUM, OUTPUT);
    digitalWrite(FLASH_GPIO_NUM, LOW);
}