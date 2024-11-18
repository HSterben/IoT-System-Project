#include <WiFi.h>
#include <PubSubClient.h>

// Wi-Fi credentials
const char* ssid = "Liam";
const char* password = "Cristian";

// MQTT broker details
const char* mqtt_server = "172.20.10.6";

// MQTT client setup
WiFiClient espClient;
PubSubClient client(espClient);

// LED Pin
const int ledPin = 4;

// Function prototypes
void setup_wifi();
void callback(String topic, byte* message, unsigned int length);
void reconnect();

void setup() {
  Serial.begin(115200);

  // Setup Wi-Fi and MQTT
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  // Configure LED pin
  pinMode(ledPin, OUTPUT);
}

void setup_wifi() {
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(String topic, byte* message, unsigned int length) {
  // Handle messages on the subscribed topic
  String messageIn;
  for (unsigned int i = 0; i < length; i++) {
    messageIn += (char)message[i];
  }

  if (topic == "room/light") {
    Serial.print("Message received: ");
    Serial.println(messageIn);

    if (messageIn == "ON") {
      digitalWrite(ledPin, HIGH);
      Serial.println("Light turned ON");
    } else if (messageIn == "OFF") {
      digitalWrite(ledPin, LOW);
      Serial.println("Light turned OFF");
    }
  }
}

void reconnect() {
  // Reconnect to the MQTT broker if disconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("vanieriot")) {
      Serial.println("connected");
      client.subscribe("room/light");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds...");
      delay(5000);
    }
  }
}

void loop() {
  // Maintain MQTT connection
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Publish an analog value to "room/light" every 5 seconds
  String payload = String(analogRead(32)); // Convert analog reading to String
  client.publish("room/light", payload.c_str());
  delay(5000);
}
