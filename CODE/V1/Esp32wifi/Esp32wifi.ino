#include <WiFi.h>
#include <WiFiUdp.h>
#include <Arduino.h>
#include <Secrets.h>

const char* ssid = Secret_Wifi_SSID;
const char* password = Secret_Wifi_PASS;
const int tcpPort = 11112;
const int udpPort = 11113;
const char* uniqueID = "Esp32_1";

WiFiServer server(tcpPort);
WiFiUDP udp;
WiFiClient tcp;

bool connected = false;
unsigned long lastReconnectAttempt = 0;
const unsigned long reconnectInterval = 5000;

TaskHandle_t Task1;  // WiFi Connection Control task
TaskHandle_t Task2;  // TCP task
TaskHandle_t Task3;  // UDP task
TaskHandle_t Task4;  // Online print task
TaskHandle_t Task5;  // Serial Echo task

void setup() {
  Serial.begin(115200);
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  Serial.println("Connected to WiFi");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  server.begin();
  udp.begin(udpPort);
  Serial.println("Server started");

  xTaskCreatePinnedToCore(wifiConnectionControl, "WiFiConnControl", 4096, NULL, 1, &Task1, 1);
  xTaskCreatePinnedToCore(tcpTask, "TCPTask", 4096, NULL, 1, &Task2, 1);
  xTaskCreatePinnedToCore(udpTask, "UDPTask", 4096, NULL, 1, &Task3, 1);
  xTaskCreatePinnedToCore(printOnlineTask, "OnlineTask", 2048, NULL, 1, &Task4, 0);
  xTaskCreatePinnedToCore(serialEchoTask, "SerialEchoTask", 2048, NULL, 1, &Task5, 0);
}

void loop() {
  vTaskDelete(NULL);
}

void wifiConnectionControl(void * pvParameters) {
  while (true) {
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("Reconnecting to WiFi...");
      WiFi.disconnect();
      WiFi.begin(ssid, password);
      while (WiFi.status() != WL_CONNECTED) {
        vTaskDelay(pdMS_TO_TICKS(1000));
      }
      Serial.println("Reconnected to WiFi");
    }
    vTaskDelay(pdMS_TO_TICKS(5000));
  }
}

void tcpTask(void * pvParameters) {
  while (true) {
    if (!tcp.connected()) {
      tcp = server.available();
      if (tcp) {
        Serial.println("New client connected");
        connected = true;
      }
    }
    
    if (tcp.connected()) {
      if (tcp.available()) {
        String received = tcp.readStringUntil('\n');
        received.trim();
        Serial.println("TCP Packet: " + received);
        tcp.println("TCP Echo: " + received);
        if (received == "ping") {
          tcp.println("pong");
        }
      }
    } else if (connected) {
      Serial.println("Client disconnected");
      connected = false;
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

void udpTask(void * pvParameters) {
  while (true) {
    if (udp.parsePacket()) {
      char incomingPacket[255];
      int packetSize = udp.read(incomingPacket, 255);
      if (packetSize) {
        incomingPacket[packetSize] = 0;
        String packetContent = String(incomingPacket);
        Serial.println("UDP Packet: " + packetContent);
        
        if (packetContent == "DISCOVER") {
          udp.beginPacket(udp.remoteIP(), udp.remotePort());
          udp.print(uniqueID);
          udp.endPacket();
        } else {
          udp.beginPacket(udp.remoteIP(), udp.remotePort());
          udp.println("UDP Echo: " + packetContent);
          udp.endPacket();
        }
      }
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

void printOnlineTask(void * pvParameters) {
  while (true) {
    Serial.println("Online");
    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}

void serialEchoTask(void * pvParameters) {
  while (true) {
    if (Serial.available() > 0) {
      String received = Serial.readStringUntil('\n');
      received.trim();
      Serial.println("Serial Echo: " + received);
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}
