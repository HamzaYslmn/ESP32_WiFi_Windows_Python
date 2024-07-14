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
  if (WiFi.waitForConnectResult() != WL_CONNECTED) {
    Serial.println("WiFi Failed");
    while (1) {
      delay(1000);
    }
  }
  Serial.print("Connected to WiFi. IP: ");
  Serial.println(WiFi.localIP());
}

void handleUDPPacket(AsyncUDPPacket packet) {
  if (strncmp((char*)packet.data(), "DISCOVER", packet.length()) == 0) {
    String response = "ESP32:" + WiFi.localIP().toString();
    packet.printf(response.c_str());
    Serial.println("DISCOVERED: " + response);
  } else {
    uint32_t receiveTime = micros();
    udp.writeTo(packet.data(), packet.length(), packet.remoteIP(), packet.remotePort());
    uint32_t sendTime = micros();
    
    float processingTime = (sendTime - receiveTime) / 1000.0;
    String message = String((char*)packet.data());
    Serial.println(String(processingTime) + " ms" + " | " + "Echo: " + message);
  }
}

void setupUDP() {
  if (udp.listen(UDP_PORT)) {
    Serial.println("UDP listening on port " + String(UDP_PORT));
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
