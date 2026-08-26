# Guia: usar un celular/tablet Android como gateway de SMS (Termux)

Alternativa a un router ZTE MF920V: un celular Android con SIM, conectado a
la misma WiFi, expone una API local para enviar SMS con su propia linea.
Evita por completo los problemas de USB/RNDIS de los routers ZTE — el
telefono se conecta por WiFi normal, cada uno con su propio MAC real, sin
conflictos.

## Paso 1 - Instalar F-Droid

Termux **ya no funciona bien desde Play Store** (version descontinuada).
Se instala desde F-Droid:

1. En el navegador del celular, entra a `https://f-droid.org/`.
2. Descarga el APK (boton "Download F-Droid").
3. Abre el APK descargado. Si Android bloquea la instalacion ("Origen
   desconocido"), sigue el aviso para permitirlo solo para el navegador.
4. Instala F-Droid.

## Paso 2 - Instalar Termux y Termux:API

Dentro de la app F-Droid (no en Play Store):

1. Busca **"Termux"** → Instalar.
2. Busca **"Termux:API"** → Instalar (es la app complementaria que da acceso
   a funciones del telefono, incluido SMS).

## Paso 3 - Dar permisos

1. Abre **Ajustes de Android → Apps → Termux:API → Permisos**.
2. Activa el permiso de **SMS** (y Contactos si lo pide).

## Paso 4 - Preparar Termux

Abre la app Termux (la terminal, no Termux:API) y corre:

```bash
pkg update && pkg upgrade -y
pkg install -y termux-api python
```

> **Si `pkg update` falla con errores tipo "Failed to fetch ... Unable to
> connect to mirrors.XXXXX.in":** el mirror que te asigno por defecto esta
> caido. Cambialo con:
> ```bash
> termux-change-repo
> ```
> Elige otro de la lista (con las flechas, Enter para confirmar — prueba
> con el que diga "Main repository (CDN, recommended)" o similar), y vuelve
> a correr `pkg update && pkg upgrade -y`.
>
> Durante el `upgrade`, si aparece un prompt tipo
> `*** sources.list (Y/I/N/O/D/Z) [default=N] ?` (pregunta que hacer con un
> archivo de configuracion que cambio), escribe **`Y`** y Enter — es
> esperado, corresponde al cambio de mirror que acabas de hacer.

## Paso 5 - Probar el envio de SMS por linea de comandos

```bash
termux-sms-send -n +51987654321 "Prueba desde Termux"
```

Si no habias abierto Termux:API antes, puede pedir el permiso de SMS en ese
momento — acepta. Si el SMS llega, todo esta listo para automatizarlo.

## Paso 6 - Crear el servidor HTTP local

Crea el archivo del servidor:

```bash
nano servidor_sms.py
```

Pega esto (Ctrl+O para guardar, Enter, Ctrl+X para salir):

```python
import json
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

API_KEY = "CAMBIA-ESTO-POR-UNA-CLAVE-SECRETA"

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/sms/send":
            self.send_response(404)
            self.end_headers()
            return

        if self.headers.get("X-API-Key") != API_KEY:
            self.send_response(401)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length))
        phone = data["phone"]
        message = data["message"]

        result = subprocess.run(
            ["termux-sms-send", "-n", phone, message],
            capture_output=True, text=True,
        )

        self.send_response(200 if result.returncode == 0 else 500)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "sent" if result.returncode == 0 else "error",
            "phone": phone,
            "detail": result.stderr.strip(),
        }).encode())

    def log_message(self, format, *args):
        pass  # silencia el log de cada peticion en pantalla

HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
```

Cambia `API_KEY` por una clave propia antes de guardar.

## Paso 7 - Evitar que Android mate el proceso

Antes de arrancar el servidor, evita que Android suspenda Termux en segundo
plano:

```bash
termux-wake-lock
```

## Paso 8 - Arrancar el servidor

```bash
python servidor_sms.py
```

Debe quedar corriendo sin salir de la terminal (minimiza la app, no la
cierres).

## Paso 9 - Averiguar la IP del celular

En otra sesion de Termux (desliza desde el borde izquierdo → "New session"),
o en Ajustes de Android → WiFi → toca la red conectada → IP:

```bash
ifconfig wlan0
```

Anota la IP (ej. `192.168.28.50`).

## Paso 10 - Probar desde otra PC en la misma WiFi

```bash
curl -X POST http://192.168.28.50:8080/sms/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: CAMBIA-ESTO-POR-UNA-CLAVE-SECRETA" \
  -d '{"phone": "+51987654321", "message": "Prueba desde la PC"}'
```

Respuesta esperada: `{"status": "sent", "phone": "+51987654321", "detail": ""}`.

## Notas

- Reservar la IP del celular en el router WiFi (DHCP fijo por MAC) evita que
  cambie y rompa la integracion — revisa el panel de administracion de esa
  red WiFi.
- Si el celular se reinicia o cierra Termux, hay que repetir los Pasos 7 y 8
  a mano (Termux no arranca solo con Android por defecto).
- Este servidor es standalone, separado del proyecto principal
  (`ZteSmsGateway`). Si despues quieres que el dashboard central tambien
  pueda mandar SMS a traves de este celular (ademas de los routers ZTE), es
  un cambio de codigo aparte en `api.py` — avisa cuando llegues a esa etapa.
