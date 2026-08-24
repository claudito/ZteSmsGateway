# SMS Gateway con ZTE MF920V

API HTTP que corre en una PC y usa el router MiFi ZTE MF920V (conectado por
USB o WiFi) para enviar SMS. Otros equipos de la red llaman a esta API en
vez de hablar directo con el modem.

> Para instalar esto en una PC nueva sin Python ni herramientas de
> desarrollo (incluye el caso de varios routers ZTE a la vez), ver
> [MANUAL_INSTALACION.md](MANUAL_INSTALACION.md). Para el detalle tecnico
> del protocolo del router y por que el codigo esta hecho asi, ver
> [DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md).

Datos del equipo (de la etiqueta):
- Modelo: ZTE MF920V
- IP de administracion: 192.168.0.1
- Password web por defecto: admin

## 1. Conectar el ZTE a la PC

Conecta el MF920V por USB. En Windows deberia instalarse como adaptador de
red (RNDIS) ademas de cargar la bateria — con eso la PC ya puede llegar a
`192.168.0.1` sin pasar por WiFi. Verifica con:

```
ping 192.168.0.1
```

Si no responde, revisa en "Adaptadores de red" (`ncpa.cpl`) que aparezca un
adaptador tipo "ZTE ... Mobile Broadband" o similar, o conecta la PC al
WiFi que emite el propio MF920V (SSID de la etiqueta) como alternativa.

## 2. Instalar dependencias

```bash
cd /d/Proyectos/Python/ZteSmsGateway
pip install -r requirements.txt
```

## 3. Probar la conexion con diagnostico.py

Antes de levantar la API, valida que el protocolo funcione contra tu
firmware real (puede variar la forma de hashear el password entre modelos
ZTE):

```bash
python diagnostico.py +51987654321 admin
```

Esto imprime la respuesta cruda de cada paso (versiones, LD, login,
envio). Si algo falla, el mensaje de error trae la respuesta JSON del
router — compartela para ajustar el algoritmo de login si hace falta
(por ejemplo si tu firmware usa MD5 simple en vez de SHA256 doble).

## 4. Configurar y levantar la API

La API soporta varios routers a la vez, guarda su configuracion y el
historial de SMS en un archivo SQLite local (`sms_gateway.db`, se crea
solo), y se administra desde un dashboard web — no hace falta editar
ningun JSON a mano. El unico secreto que va en `.env` es la clave de la
API:

```bash
cd /d/Proyectos/Python/ZteSmsGateway
cp .env.example .env
```

Edita `.env` y pon una `SMS_API_KEY` propia (todo request a la API, y al
dashboard, debe incluir esa clave, ya que la API queda expuesta a toda la
red local). Y levanta la API:

```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

Abre `http://localhost:8000/` en el navegador, pega tu `SMS_API_KEY` arriba
a la derecha, y agrega tus routers desde ahi (id, ip, password, y
opcionalmente el numero de la linea). El mismo dashboard muestra el total
de SMS enviados por router y el historial de mensajes. Ver mas detalle en
la seccion "Dashboard y base de datos" de
[DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md).

## 5. Permitir el puerto en el firewall de Windows

Para que otros equipos de la red puedan llegar al puerto 8000, hay que
crear una regla de entrada. Esto requiere **PowerShell como administrador**
(no funciona desde Git Bash sin privilegios, ni de forma automatizada — hay
que abrir PowerShell manualmente y aprobar el UAC):

```powershell
netsh advfirewall firewall add rule name="SMS Gateway API" dir=in action=allow protocol=TCP localport=8000
```

## 6. Enviar un SMS desde otro equipo de la red

La URL incluye el id del router (el mismo que le pusiste en el dashboard).
Desde Git Bash (`\` para continuar linea, comillas simples para el JSON):

```bash
curl -X POST http://<ip_de_esta_pc>:8000/routers/router1/sms/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: pon-aqui-una-clave-secreta" \
  -d '{"phone": "+51987654321", "message": "Hola desde la API"}'
```

Respuesta esperada:

```json
{"status": "sent", "router": "router1", "phone": "+51987654321"}
```

Otros endpoints utiles (todos requieren `X-API-Key`):
- `GET /routers` — routers configurados.
- `PUT /routers/<id>` / `DELETE /routers/<id>` — crear, actualizar o borrar un router (lo mismo que hace el dashboard).
- `GET /messages` o `GET /routers/<id>/messages` — historial de SMS enviados.
- `GET /stats` — totales enviados/fallidos por router (lo que muestra el dashboard).

## Notas

- El mensaje se codifica en UCS2/Unicode, soporta tildes y enye sin
  problema. Mensajes largos (>70 caracteres aprox.) pueden llegar
  partidos en varios SMS segun el operador.
- `zte_sms.py` reintenta login solo si detecta que la sesion no esta
  activa (`is_logged_in`), asi que llamadas seguidas no vuelven a
  loguearse cada vez.
- Si vas a dejar esto corriendo permanentemente, conviene correrlo como
  tarea programada de Windows o con `nssm`/`pm2` en vez de una consola
  abierta.
