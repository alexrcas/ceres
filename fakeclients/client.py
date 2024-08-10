import paho.mqtt.client as mqtt
import json
import time
# The callback for when the client receives a CONNACK response from the server.

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.connect("localhost", 1883, 60)# Blocking call that processes network traffic, dispatches callbacks and# handles reconnecting.# Other loop*() functions are available that give a threaded interface and a# manual interface.

id = 'abc123'
id2 = 'def456'
temp = 30
hum = 50

terr = 70

factor = 1

while True:

    client.publish('sensors/dth/data', 'id=' + id + '&temp=' + str(temp) + '&hum=' + str(hum))
    client.publish('sensors/fc/data', 'id=' + id2 + '&terr=' + str(terr))

    temp = temp + 1 * factor
    hum = hum + 1 * factor
    terr = terr + 1 * factor

    if (temp >= 60):
        factor = -1
    
    if (temp <= 30):
        factor = 1


    time.sleep(1)