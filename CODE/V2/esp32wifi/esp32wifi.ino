#include <WiFi.h>
#include <Secrets.h>

const char* ssid = Secret_Wifi_SSID;
const char* password = Secret_Wifi_PASS;

WiFiServer server(11112);

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  server.begin();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.reconnect();
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
    }
  }

  WiFiClient client = server.available();

  if (client) {
    while (client.connected() && client.available() == 0) {
      delay(1);
    }

    if (client.available()) {
      String message = client.readStringUntil('\n');
      Serial.println("Received: " + message);

      // Echo the message back to the client
      client.println(message);
    }

    client.stop();
  }
}