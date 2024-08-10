import paho.mqtt.client as mqtt
import time

# Variable de estado para controlar la emisión de números
emitting = False
counter = 0  # Variable para contar los números emitidos

def on_connect(client, userdata, flags, reason_code, properties):
    print('connected!')
    client.subscribe('commands/irrigation/on')
    client.subscribe('commands/irrigation/off')
    client.subscribe('commands/yf/ping')

def on_message(client, userdata, msg):
    global emitting, counter
    topic = msg.topic
    payload = msg.payload.decode('utf-8')  # Decodifica el payload a string

    if topic == 'commands/irrigation/on':
        print("Received ON command")
        emitting = True

    elif topic == 'commands/yf/ping':
        print('Received PING')
        client.publish('commands/yf/pong')

    elif topic == 'commands/irrigation/off':
        print("Received OFF command")
        emitting = False
        client.publish('sensors/yf/data/irrigation', 'id=fff111&irrigation=' + str(counter))
        counter = 0  # Reinicia el contador

# Función para emitir números
def emit_numbers():
    global counter
    while True:
        if emitting:
            counter += 1
            client.publish('sensors/yf/data/flow', counter)
        time.sleep(1)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.on_message = on_message
client.on_connect = on_connect

client.connect("localhost", 1883, 60)

# Ejecuta el loop de MQTT en un hilo separado para permitir la emisión de números
client.loop_start()

# Llama a la función para emitir números
emit_numbers()
