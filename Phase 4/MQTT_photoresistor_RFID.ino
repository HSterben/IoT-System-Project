#include <WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>

// RFID Setup
#define SS_PIN 5
#define RST_PIN 4
MFRC522 rfid(SS_PIN, RST_PIN);

// Wi-Fi credentials
const char* ssid = "Liam";
const char* password = "Cristian";

// MQTT broker details
const char* mqtt_server = "172.20.10.6";

// MQTT client setup
WiFiClient espClient;
PubSubClient client(espClient);

// Light sensor pin
const int lightSensorPin = 32;

// Function prototypes
void setup_wifi();
void callback(String topic, byte* message, unsigned int length);
void reconnect();
void publishLightIntensity();
void checkAndPublishRFID();

unsigned long lastLightPublishTime = 0;
const unsigned long lightPublishInterval = 2000; // 2 seconds

void setup() {
    Serial.begin(115200);

    // Setup Wi-Fi and MQTT
    setup_wifi();
    client.setServer(mqtt_server, 1883);
    client.setCallback(callback);

    // RFID Initialization
    SPI.begin();
    rfid.PCD_Init();
    Serial.println("Place your RFID card near the reader...");

    // Light sensor initialization
    pinMode(lightSensorPin, INPUT);
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
    // Handle messages on subscribed topics (if needed)
    String messageIn;
    for (unsigned int i = 0; i < length; i++) {
        messageIn += (char)message[i];
    }

    Serial.print("Message received on topic ");
    Serial.print(topic);
    Serial.print(": ");
    Serial.println(messageIn);
}

void reconnect() {
    // Reconnect to the MQTT broker if disconnected
    while (!client.connected()) {
        Serial.print("Attempting MQTT connection...");
        if (client.connect("vanieriot")) {
            Serial.println("connected");
        } else {
            Serial.print("Failed, rc=");
            Serial.print(client.state());
            Serial.println(" retrying in 5 seconds...");
            delay(5000);
        }
    }
}

void loop() {
    if (!client.connected()) {
        reconnect();
    }
    client.loop();

    // Publish light intensity every 2 seconds
    if (millis() - lastLightPublishTime >= lightPublishInterval) {
        publishLightIntensity();
        lastLightPublishTime = millis();
    }

    // Check and publish RFID UID if a card is detected
    checkAndPublishRFID();
}

void publishLightIntensity() {
    int light = analogRead(lightSensorPin); // Read light intensity
    String lightPayload = String(light); // Convert to string for MQTT
    client.publish("room/light", lightPayload.c_str()); // Publish to light topic
    Serial.print("Published Light Intensity: ");
    Serial.println(lightPayload);
}

void checkAndPublishRFID() {
    if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
        return; // No card detected
    }

    // Construct UID in HEX format
    String uidHex = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
        if (rfid.uid.uidByte[i] < 0x10) {
            uidHex += "0"; // Add leading zero for single-digit hex values
        }
        uidHex += String(rfid.uid.uidByte[i], HEX);
    }
    uidHex.toUpperCase(); // Format to uppercase

    // Publish RFID UID
    client.publish("rfid/user_id", uidHex.c_str()); // Publish to RFID topic
    Serial.print("Published RFID UID: ");
    Serial.println(uidHex);

    rfid.PICC_HaltA(); // Halt the card to be ready for the next one
}
