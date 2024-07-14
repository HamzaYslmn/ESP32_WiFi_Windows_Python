#include <WiFi.h>
#include <AsyncUDP.h>
#include <Secrets.h>

const char* ssid = Secret_Wifi_SSID;
const char* password = Secret_Wifi_PASS;
const uint16_t UDP_PORT = 11112;

AsyncUDP udp;
const char* deviceName = "ESP32_1"; // Change this to your device name

void setupWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println(".");
  }
  Serial.print("Connected to WiFi. IP: ");
  Serial.println(WiFi.localIP());
}

void handleUDPPacket(AsyncUDPPacket packet) {
  // udp.writeTo("Some data to send", strlen("Some data to send"), IPAddress(192, 168, 1, 100), 1234);  // Example of sending data to a specific IP
  // packet.printf("Some data to send");  // Example of sending data back to the sender

  uint32_t receiveTime = micros();

  String UDPMessage = String((char*)packet.data(), packet.length());
  if (UDPMessage.length() == 0) return;
  String response;

  Serial.println("Received: " + UDPMessage);
  
  if (UDPMessage == "DISCOVER") {
    response = "ESP32:" + String(deviceName) + ":" + WiFi.localIP().toString();
    packet.printf(response.c_str());
    Serial.println("DISCOVERED: " + response);
  } else {
    response = "Echo: " + UDPMessage;
    packet.printf(response.c_str());

    uint32_t sendTime = micros();
    float processingTime = (sendTime - receiveTime) / 1000.0;
    
    Serial.println(String(processingTime) + " ms" + " | " + "Echo: " + UDPMessage);
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
