#include <ESP8266WiFi.h>
#include <PubSubClient.h>  // Include PubSubClient library for MQTT
#include "DHTesp.h"

const char* ssid = "Red Wifi A_1";
const char* password = "Turing0906";
const char* mqtt_server = "192.168.0.22";  // Removed port from this line

const char* DEVICE_ID = "esp01dht11a";

WiFiClient espClient;
PubSubClient client(espClient);

DHTesp dht;

String messageString = "";

void setup(void) {
  // Initialize serial communication
  Serial.begin(115200);
  dht.setup(2, DHTesp::DHT11);  // Connect DHT sensor to GPIO 2 (not GPIO 17 as mentioned)

  // Connect to WiFi network
  WiFi.begin(ssid, password);
  Serial.print("\n\r \n\rWorking to connect");

  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("DHT Weather Reading Server");
  Serial.print("Connected to ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Setup MQTT
  client.setServer(mqtt_server, 1883);

  delay(dht.getMinimumSamplingPeriod());
}

void loop(void) {
  if (!client.connected()) {
    reconnect();  // Reconnect to MQTT broker if disconnected
  }
  client.loop();

  // Read humidity and temperature
  float humidity = dht.getHumidity();
  float temperature = dht.getTemperature();

  // Create message string
  messageString = "id=" + String(DEVICE_ID) + "&temp=" + String((int)temperature) + "&hum=" + String((int)humidity);

  // Publish the message to the MQTT topic
  client.publish("outTopic", messageString.c_str());

  // Wait for 5 seconds
  delay(5000);
}

void reconnect() {
  // Attempt to reconnect until successful
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(DEVICE_ID)) {
      Serial.println("connected");
      client.publish("outTopic", "ESP8266 connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}
