# Laboratorio 3 - Algoritmos de Enrutamiento

Este laboratorio implementa una red de routers con enrutamiento por estado de enlace. El ATM y el banco mantienen la lógica bancaria del laboratorio anterior, pero los mensajes `DATA` ahora viajan por una topología de routers y se protegen con Hamming (7,4) en cada salto.

La topología local utiliza nueve routers: `A`, `B`, `C`, `D`, `E`, `F`, `G`, `H` e `I`. El ATM está conectado al router `F` y el banco al router `C`.

```text
ATM -> F -> red de routers A-I -> C -> BANK
BANK -> C -> red de routers A-I -> F -> ATM
```

## Requisitos

- Python 3.
- Java 21.
- Maven.
- Tailscale únicamente para la prueba distribuida.

## Configuración

Antes de iniciar, configuramos los JSON de cada proceso. Para la prueba local todos usan `127.0.0.1`; cada proceso se diferencia por su puerto.

### Router

Cada router tiene un archivo dentro de `router/config`. Esta es la estructura que usamos:

```json
{
  "router_id": "F",
  "listen": { "ip": "127.0.0.1", "port": 9006 },
  "neighbors": [
    { "router_id": "B", "ip": "127.0.0.1", "port": 9002, "cost": 2 },
    { "router_id": "D", "ip": "127.0.0.1", "port": 9004, "cost": 1 }
  ],
  "attached_host": {
    "role": "CLIENT",
    "host_id": "ATM",
    "ip": "127.0.0.1",
    "port": 8001
  }
}
```

`router_id` identifica lógicamente el router. `listen` indica dónde escucha ese router. `neighbors` registra los routers directamente conectados, su dirección y el costo del enlace. `attached_host` indica si el router tiene un host conectado.

El router `F` usa el rol `CLIENT` y está conectado al ATM. El router `C` usa el rol `SERVER` y está conectado al banco. Los demás routers usan:

```json
"attached_host": null
```

### ATM

El ATM usa `cliente-python/config/atm.json`:

```json
{
  "host_id": "ATM",
  "listen": { "ip": "127.0.0.1", "port": 8001 },
  "gateway": { "router_id": "F", "ip": "127.0.0.1", "port": 9006 },
  "remote_host": { "host_id": "BANK", "gateway_id": "C" }
}
```

`listen` es la dirección donde el ATM recibe respuestas. `gateway` identifica el router F, al cual el ATM entrega sus solicitudes. `remote_host` identifica al banco y a su gateway C.

### Banco

El banco usa `servidor-java/config/bank.json`:

```json
{
  "host_id": "BANK",
  "listen": { "ip": "127.0.0.1", "port": 8002 },
  "gateway": { "router_id": "C", "ip": "127.0.0.1", "port": 9003 },
  "remote_host": { "host_id": "ATM", "gateway_id": "F" }
}
```

El banco recibe solicitudes desde C y entrega sus respuestas nuevamente a C. El router C calcula la ruta de regreso hacia F.

## Prueba local

Todos los comandos de esta sección se ejecutan desde la raíz del repositorio:

```bash
cd /Users/bryan/Documents/Redes/Laboratorio_3_Protocolos_de_Enrutamiento
```

Abrimos once terminales: una para cada router, una para el banco y una para el ATM.

### 1. Levantar los routers

Ejecutamos un comando por terminal:

```bash
python3 router/src/main.py --config router/config/A.json
python3 router/src/main.py --config router/config/B.json
python3 router/src/main.py --config router/config/C.json
python3 router/src/main.py --config router/config/D.json
python3 router/src/main.py --config router/config/E.json
python3 router/src/main.py --config router/config/F.json
python3 router/src/main.py --config router/config/G.json
python3 router/src/main.py --config router/config/H.json
python3 router/src/main.py --config router/config/I.json
```

Al iniciar, cada router descubre a sus vecinos mediante `HELLO`, propaga LSAs y genera su tabla en `router/routing_tables`.

### 2. Levantar el banco

En otra terminal ejecutamos:

```bash
mvn -f servidor-java/pom.xml compile exec:java \
  -Dexec.mainClass=ServerMain \
  -Dexec.args="--config servidor-java/config/bank.json"
```

### 3. Levantar el ATM

En la última terminal ejecutamos:

```bash
python3 cliente-python/src/main.py \
  --config cliente-python/config/atm.json
```

El ATM solicita la probabilidad de ruido, el número de tarjeta, el PIN y la operación bancaria. Cada solicitud y respuesta se encapsula en un `DATA`, viaja entre F y C, y se protege nuevamente con Hamming (7,4) en cada salto.

Para detener un proceso usamos `Ctrl + C` en su terminal.

## Prueba distribuida con Tailscale

La misma topología puede ejecutarse entre varias computadoras. El código, los puertos, los `router_id` y los costos no cambian; solamente sustituimos las direcciones IP de los JSON.

En cada computadora obtenemos su IP de Tailscale:

```bash
tailscale ip -4
```

Después actualizamos los archivos JSON:

- En cada router, `listen.ip` debe ser la IP de Tailscale de la computadora que ejecuta ese router.
- En cada vecino, `ip` debe ser la IP de Tailscale de la computadora que ejecuta ese vecino.
- En ATM y banco, `listen.ip` debe ser la IP de su propia computadora y `gateway.ip` debe ser la IP de la computadora donde se ejecuta su gateway.
- En `attached_host`, usamos `127.0.0.1` si el host y su gateway se ejecutan en la misma computadora; de lo contrario usamos la IP de Tailscale del host.

Después levantamos los procesos con los mismos comandos de la prueba local, desde la raíz del repositorio en cada computadora que corresponda.
