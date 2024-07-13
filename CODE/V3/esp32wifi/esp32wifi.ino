#include <WiFi.h>
#include <AsyncUDP.h>
#include <Secrets.h>

const char* ssid = Secret_Wifi_SSID;
const char* password = Secret_Wifi_PASS;
const uint16_t UDP_PORT = 11112;

AsyncUDP udp;

void setupWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
  Serial.printf("Connected to WiFi. IP: %s\n", WiFi.localIP().toString().c_str());
}

void handleUDPPacket(AsyncUDPPacket packet) {
  uint32_t receiveTime = micros();
  udp.writeTo(packet.data(), packet.length(), packet.remoteIP(), packet.remotePort());
  uint32_t sendTime = micros();
  
  float processingTime = (sendTime - receiveTime) / 1000.0; // Convert to ms
  Serial.printf("Echo: %.*s, Processing time: %.3f ms\n", packet.length(), packet.data(), processingTime);
}

void setupUDP() {
  if (udp.listen(UDP_PORT)) {
    Serial.printf("UDP listening on port %d\n", UDP_PORT);
    udp.onPacket(handleUDPPacket);
  }
}

void setup() {
  Serial.begin(115200);
  setupWiFi();
  setupUDP();
}

void loop() {
  vTaskDelete(NULL);
}