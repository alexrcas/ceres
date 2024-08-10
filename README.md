# Ceres

Ceres es un sistema para monitorizar y gestionar un huerto casero, registrando temperatura y humedad del aire y humedad del suelo. También permite activar un riego, registrando la cantidad de agua empleada.

## Arquitectura y tecnologías

Para la comunicación entre los diferentes dispositivos *IoT* se utilizará el protocolo *MQTT*, habitual en estos casos por su sencillez y ligereza. La lógica y comunicación entre dispositivos será realizada por *Node-RED*, herramienta también ampliamente usada en este campo que permite de manera muy gráfica y simple llevar a cabo estas tareas. Será necesaria también la existencia de un broker de mensajes como *Mosquitto* y por último, una base de datos como *Postgres* para almacenar la información y sobre la que se sustenterá el backoffice, que se mencionará más adelante.

Para facilitar el despliegue e instalación de todos estos elementos se utiliza docker compose. Se provee un fichero de despliegue `docker-compose.yml` que ya contiene todas las configuraciones necesarias de los diferentes sistemas y las interconexiones entre estos.

![](/docs/arquitectura.jpg)

Uno de los planteamientos del proyecto es separar la implementación de un backoffice del resto del sistema. Es decir, simplemente con desplegar el docker-compose el sistema quedaría operativo y funcionando, siendo otra fase posterior y desacoplada la de desarrollar un backoffice que explotase y presentase la información que ya contendría la base de datos (que se inicia con un esquema mínimo como se explica en la siguiente sección) o permitiese activar el riego en su interfaz gráfica (o tomase decisiones en base a datos para activarlo de forma autónoma).


## Sistemas

### Sensores

Se utilizan una serie de dispositivos que serán descritos más adelante en la sección de *Hardware*, pero nótese que en realidad podría utilizarse cualquier hardware siempre que se comporte como describe esta sección. De hecho, como se detalla en la sección *Despliegue*, se provee un código Python que simula virtualmente estos dispositivos para poder probar de manera simple el correcto funcionamiento del sistema.

#### Sensor DHT
Mide la temperatura y la emitad del aire. Publica un mensaje en el topic `sensors/dht/data` con el formato `id={id}&temp={temp}&hum={hum}`. Donde:

* id: id del dispositivo físico.
* temp: temperatura del aire en grados celsius.
* hum: humedad del aire en porcentaje.

Ejemplo:
```
id=abcd123&temp=24&hum=65
```

#### Sensor FC
Mide la humedad del suelo. Publica un mensaje en el topic `sensors/fc/data` con el formato `id={id}&terr={terr}`. Donde:

* id: id del dispositivo físico.
* temp: humedad del suelo en porcentaje.

Ejemplo:
```
id=defg456&terr=58
```

#### Sensor YF

Este sensor mide el caudal de agua que lo atraviesa, pero se ha programado para que utilice el concepto de *riego*. Un riego viene determinado por un flujo de agua que atraviesa el sensor de manera ininterrumpida, desde que comienza hasta que termina. Si una flujo de agua atraviesa el sensor y luego se detiene, esto se considera un riego. Si posteriormente se repite la operación, esto se considera otro riego.

Así, este sensor emite dos tipos de mensajes. Por un lado, la cantidad de agua que se va acumulando en el riego actual en `sensors/yf/data/flow` sin formato, siendo únicamente un número decimal.

Por otro lado, una vez terminado el riego publica un mensaje en el topic `sensors/yf/data/irrigation` con la cantidad total de agua empleada en dicho riego. Este mensaje tiene el formato `id={id}&irrigation={irrigation}`. Donde:

* id: id del dispositivo físico.
* irrigation: litros utilizados.

Ejemplo:

1. Se dispara el riego y el agua comienza a atravesar el sensor. Este comienza a publicar en el topic `sensors/yf/data/flow` de manera consecutiva cada pocos ms:

```
0.1
0.25
0.38
...
```
2. Finalmente, tras llegar a medio litro el flujo de agua se detiene. El sensor, tras detectar que se ha detenido del todo publica un mensaje en `sensors/yf/data/irrigation`:

```
id=wxyz567&irrigation=0.5
```

#### Relé o electroválvula

Este dispositivo se limita abrir el paso del agua. Está suscrito a los topics `commands/irrigation/on` y `commands/irrigation/off`


### Node-RED

En base a lo descrito anteriomente, los flujos usados en Node-RED son muy simples:

![](/docs/flow.png)

Los tres flujos superiores se limitan a recibir los mensajes vistos en la sección anterior, convertirlos de formato *queryParam* a formato *JSON* y almacenarlos tal cual son recibidos en una tabla de mensajes en base de datos.

El cuarto flujo sirve para escuchar la petición para inicar el riego. Esta petición es una llamada *POST* al endpoint *nodered/api/irrigation* con un cuerpo que indiga la cantidad de agua a utilizar en el riego, por ejemplo:

```
"waterLimit": 2.5
```

Posteriormente hace tres cosas: devuelve un *OK* al servidor, persiste la cantidad de agua a utilizar en el riego, y activa la electroválvula para que el agua empiece a fluir.

El último flujo escucha los datos que va emitiendo el sensor de caudal mientras transcurre el riego y compara esta cantidad de agua utilizada hasta el momento con el límite que se especificó en la orden de regar. Una vez se supera este límite, se emite a la electroválvula la orden de cerrarse.


### Base de datos

La base de datos es creada con un esquema mínimo (una tabla) que almacena los mensajes desde que el sistema es desplegado. Se trata de la tabla *Message* que posee el siguiente aspecto:

Un ejemplo de entrada en esta tabla:

| ID | CREATED | ESTADO | TOPIC | CONTENT |
|----|---------|--------|-------|---------|
|  1  |    2024-08-10T16:45:32     |    PENDIENTE    |  FC     |   {"id": "abcd1234", "terrain":55}      |


Los dos primeros campos no merecen mención, pero veamos el resto:

* ESTADO: Indica si el mensaje ha sido procesado por el backoffice, pudiendo ser también *PROCESADO* o *ERROR*.
* TOPIC: un enumerado que identifica el tipo de mensaje. En este ejemplo, es un mensaje de humedad del terreno.
* CONTENT: contenido del mensaje sin tratar, almacenado directamente por Node-RED.


Esta arquitectura permite desacoplar los eventos que ocurren de cualquier backoffice, ya que desde que el sistema es desplegado por primera vez los eventos van quedando registrados. Un backoffice puede ser desarrollado meses más tarde y procesar estos eventos para proyectarlos en su modelo particular sin perder la información que se fue registrando mientras. También permite que si un sensor envía datos erróneos o sin sentido debido a un mal funcionamiento la información queda registrada para su posterior análisis. El backoffice podría incluso notificar que un determinado sensor está enviando datos incorrectos.

De igual forma, si se cambia el formato del mensaje que envian los dispositivos o se añade un nuevo dispositivo que emite otro tipo de mensaje, estos quedarán registrados. El backoffice fallaría en su procesamiento, pero se harían las adaptaciones necesarias y se relanzaría este procesamiento.

En defintiva, la idea es capturar y registrar los eventos que han ocurrido en la realidad, que es lo realmente valioso. Si se posee este registro luego puede procesarse de cuantas formas y veces se desee.


### Backoffice

Modelo de datos:
![](/docs/model.jpg)

Flujo de Node-RED:


## Despliegue

En la raíz del proyecto ejecutar:

```
docker-compose up -d
```

Una vez estén en ejecución los contenedores:

* La consola de Node-RED está disponible en `localhost:1880`
* La base de datos está expuesta en el puerto 5432, con usuario y contraseña `postgres`
* Mosquitto está expuesto en el puerto 1883. Nótese que los dispositivos *IoT* deben apuntar a la ip externa de la máquina y no a *localhost*.

