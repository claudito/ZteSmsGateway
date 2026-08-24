# Documentacion Tecnica - SMS Gateway ZTE MF920V

Este documento explica como funciona el proyecto por dentro: el protocolo real
del router (obtenido por ingenieria inversa del propio firmware), las
particularidades de Windows al conectar el modem por USB, y como resolver los
problemas que aparecen al usar varios routers en la misma PC.

Para la guia paso a paso de instalacion en una PC nueva, ver
[MANUAL_INSTALACION.md](MANUAL_INSTALACION.md).

## 1. Arquitectura

```
[Equipo de la red]  --HTTP + X-API-Key-->  [API FastAPI, esta PC]  --HTTP goform via USB (RNDIS)-->  [Router ZTE MF920V]  --SMS-->  [Red celular]
```

Cada router ZTE se conecta por USB a la PC que corre la API. La API traduce
peticiones HTTP simples (`POST /sms/send`) a llamadas al protocolo web interno
(`goform`) que el propio router expone en `http://192.168.0.1` (o la IP que se
le haya asignado).

## 2. Protocolo del router (ingenieria inversa)

Los routers ZTE (MF920V y similares) no tienen una API publica documentada:
su interfaz de administracion web hace llamadas AJAX a
`/goform/goform_get_cmd_process` (lecturas) y `/goform/goform_set_cmd_process`
(escrituras). El esquema de login **varia entre firmwares**: algunos usan un
hash SHA256 doble con un salt (`LD`) obtenido del propio router, otros un
token anti-CSRF (`AD`), otros simplemente Base64 del password.

### Como se determino el esquema para este equipo

1. `diagnostico.py` mostro que el comando `LD` devolvia siempre vacio
   (`{"LD":""}`), lo que indicaba que ese firmware no usa ese esquema.
2. Se descargo el JavaScript que el propio router sirve:
   ```
   http://192.168.0.1/js/service.js
   http://192.168.0.1/js/config/config.js
   ```
3. En `config.js` se encontro la bandera de configuracion:
   ```js
   DEVICE:"ufi/mf9xx", PASSWORD_ENCODE:true
   ```
4. En `service.js` se encontro la funcion de login (minificada):
   ```js
   function e(e,t){return{isTest:Vr,goformId:"LOGIN",
     password:n.PASSWORD_ENCODE?Base64.encode(e.password):e.password}}
   ```
   Es decir: con `PASSWORD_ENCODE=true`, el password va en **Base64 plano**,
   sin LD, sin SHA256, sin token `AD`.
5. Se confirmo con `curl` directo contra el router antes de tocar el codigo
   Python (ver seccion 10 para el mismo procedimiento aplicado a otro
   firmware).

### Firmware confirmado funcionando

- `wa_inner_version = BD_ENTELPEMF920VV1.0.0B03` (Entel Peru)
- `DEVICE = ufi/mf9xx`
- `PASSWORD_ENCODE = true`

### Esquema de login

```
POST /goform/goform_set_cmd_process
  isTest=false
  goformId=LOGIN
  password=<Base64(password_texto_plano)>
```

Respuesta exitosa: `{"result":"0"}` o `{"result":"4"}`. Cualquier otro valor
es error.

**No hay cookie de sesion.** El router identifica al cliente logueado por su
**IP de origen**, no por un token `stok` como otros firmwares ZTE. Por eso
`zte_sms.py` no maneja cookies especiales: basta con que las peticiones
salgan de la misma IP (la de la interfaz USB/RNDIS asignada a esta PC).

### Envio de SMS

```
POST /goform/goform_set_cmd_process
  isTest=false
  goformId=SEND_SMS
  notCallback=true
  Number=<numero con codigo de pais>
  sms_time=<yy;mm;dd;HH;MM;SS;+0>
  MessageBody=<mensaje codificado UTF-16BE (UCS2), en hexadecimal>
  ID=-1
  encode_type=UNICODE
```

Respuesta exitosa: `{"result":"success"}`.

## 3. Como adaptar el cliente a OTRO firmware

Si `python diagnostico.py <numero>` falla en el paso de login en un router
distinto (otro modelo, u otra version de firmware del mismo MF920V), repetir
este procedimiento:

1. Con el router conectado y accesible, abrir en el navegador (o con `curl`):
   - `http://<ip_router>/js/service.js`
   - `http://<ip_router>/js/config/config.js`
2. Buscar `PASSWORD_ENCODE` en `config.js` (`true`/`false`) y `DEVICE`.
3. Buscar `goformId:"LOGIN"` en `service.js` y ver que campos arma esa
   funcion (puede incluir `AD`, un hash con `LD`, etc.).
4. Buscar tambien `cmd:"LD"` o `cmd:"RD"` para confirmar si ese firmware los
   usa.
5. Ajustar `login()` en `zte_sms.py` segun lo encontrado.

## 4. Particularidad: el router se conecta como CD-ROM, no como red

Al conectar el MF920V por USB por primera vez en una PC, Windows lo detecta
como una **unidad de CD-ROM virtual** (aparece en "Este equipo" con volumen
`ZTEMODEM`), no como adaptador de red. Esa unidad trae un instalador de
drivers (`AutoRun.exe`) pensado para Windows Vista/7/WNET que en Windows
10/11 puede fallar silenciosamente (se ejecuta y se cierra sin instalar
nada, sin mostrar error).

**Solucion que funciono:** dentro de esa misma unidad, en `Data\ResetCDROM.exe`,
hay una herramienta especifica para forzar el cambio de modo
CD-ROM -> red, sin pasar por el instalador completo. Al ejecutarla:

- No requiere permisos de administrador (es equivalente a "expulsar" un
  medio extraible, una operacion permitida a cualquier usuario estandar).
- No siempre muestra una ventana visible; puede terminar sin feedback
  aparente.
- A los pocos segundos aparece un adaptador de red nuevo, tipo
  **"Remote NDIS based Internet Sharing Device"**, con una IP asignada por
  DHCP en la subred `192.168.0.0/24` (o la que tenga configurada ese router).

Hay que repetirlo una vez por router, la primera vez que se conecta a una PC
en particular (el "modo red" no queda recordado por el router en abstracto,
sino que depende de la negociacion USB con cada PC/puerto).

## 5. Particularidad: conflicto de ruta de red por defecto

El router entrega, via DHCP sobre USB, una puerta de enlace por defecto
(su propia IP) con una metrica de ruta muy baja. Esto hace que Windows
prefiera enrutar **todo** el trafico de salida (incluida la intranet
corporativa e internet normal) a traves del modem USB en vez de la red
habitual de la PC.

**Sintoma:** al conectar el ZTE, sitios internos o internet dejan de cargar
(`ERR_CONNECTION_TIMED_OUT`), aunque el resto de la red seguia funcionando
antes de conectarlo.

**Causa exacta:** Windows elige la ruta `0.0.0.0/0` con menor metrica
efectiva (`metrica de interfaz + metrica de ruta`). La interfaz RNDIS del
ZTE suele quedar con metrica efectiva mucho mas baja que la red cableada o
WiFi normal de la oficina.

**Solucion:** subir la metrica de la interfaz del ZTE (esto **no** afecta el
acceso al propio router: la ruta especifica a su subred `/24` es mas
especifica que `0.0.0.0/0` y se sigue usando sin importar la metrica de la
ruta por defecto). Requiere PowerShell **como administrador**:

```powershell
Get-NetAdapter | Where-Object { $_.InterfaceDescription -match "RNDIS" } | Select-Object Name
Set-NetIPInterface -InterfaceAlias "Ethernet 2" -InterfaceMetric 6000
```

(Cambiar `"Ethernet 2"` por el nombre real que devuelva el primer comando.)

**Nota sobre permisos:** en una PC administrada donde el usuario no es
administrador local, los intentos de elevar el proceso automaticamente
(`Start-Process -Verb RunAs`) desde una sesion no interactiva **no
funcionan**, porque el cuadro de dialogo de UAC necesita que una persona lo
apruebe con clic. La solucion es que la persona misma abra PowerShell como
administrador manualmente (clic derecho > "Ejecutar como administrador") y
pegue el comando ahi.

## 6. Particularidad: varios routers ZTE en la misma PC

Todos los MF920V (mismo modelo) salen de fabrica con la **misma IP LAN**
(`192.168.0.1`) y la misma subred (`192.168.0.0/24`) para su interfaz USB.
Conectar dos o mas simultaneamente sin cambiar esto genera un conflicto de
subred duplicada: Windows no puede distinguir de forma confiable a que
interfaz enviar el trafico dirigido a `192.168.0.1`, y el comportamiento es
indeterminado (a veces responde el router equivocado, a veces timeout).

**Solucion:** antes de usarlos juntos, cambiar la IP LAN de cada router a un
valor distinto, conectando **un router a la vez**:

1. Conectar solo ese router.
2. Entrar por navegador a `http://192.168.0.1` (password de la etiqueta o
   `admin` por defecto).
3. Ir a la seccion de configuracion de LAN (nombre exacto varia segun idioma
   del firmware: "Network Settings" / "LAN Settings" / "Configuracion LAN").
4. Cambiar la "Direccion IP" del router (ej. router 1 -> `192.168.1.1`,
   router 2 -> `192.168.2.1`, etc.) y guardar. El router se reinicia.
5. Etiquetar fisicamente el equipo con la IP asignada.
6. Repetir con el siguiente router.

Con IPs distintas, cada router aparece como una interfaz de red separada sin
conflicto de subred, y cada uno necesita tambien el ajuste de metrica de la
seccion 5 (uno por interfaz).

## 7. Configuracion: `.env` + `routers.json`

Un solo proceso de la API sirve **todos** los routers configurados. La
configuracion se separa en dos archivos, ninguno de los dos versionado en
git (ver `.gitignore`), cada uno con su plantilla `*.example` si versionada:

- **`.env`** (secretos): `SMS_API_KEY` y las passwords de los routers.
- **`routers.json`** (no-secreto): lista de `{"id", "ip"}` por router.

```json
// routers.json
[
  {"id": "router1", "ip": "192.168.1.1"},
  {"id": "router2", "ip": "192.168.2.1"}
]
```

```env
# .env
SMS_API_KEY=clave-secreta-compartida
ZTE_ROUTER_PASSWORD=admin
# password especifica de un router (opcional, sobreescribe la de arriba):
ZTE_PASSWORD_ROUTER2=otra-password
```

### Password por router

Al arrancar, `api.py` calcula la password de cada router en `routers.json`
buscando la variable de entorno `ZTE_PASSWORD_<ID EN MAYUSCULAS>` (donde
`<ID>` es el campo `"id"` de ese router). Si no existe esa variable, usa
`ZTE_ROUTER_PASSWORD` como default para todos. Esto permite que la mayoria
de los routers compartan la misma password (`admin` o la que sea) y solo
haga falta una entrada extra en `.env` para los que sean distintos.

Agregar un router nuevo es agregar una linea a `routers.json` (y, si su
password difiere del default, una variable a `.env`) — no hace falta tocar
codigo, ni abrir un puerto nuevo, ni un `.bat` nuevo.

## 8. Endpoints de la API

```
GET  /health
GET  /routers
  -> [{"id": "router1", "ip": "192.168.1.1"}, ...]

POST /routers/{router_id}/sms/send
  Header: X-API-Key: <clave>
  Body:   {"phone": "+51987654321", "message": "texto"}
  -> {"status": "sent", "router": "router1", "phone": "..."}
  -> 404 si router_id no esta en routers.json
  -> 401 si falta o no coincide X-API-Key (cuando SMS_API_KEY esta definida)
```

## 9. Archivos del proyecto

| Archivo | Rol |
|---|---|
| `zte_sms.py` | Cliente del protocolo del router (login, envio de SMS) |
| `api.py` | API HTTP (FastAPI); carga `.env` y `routers.json`, expone un endpoint por router |
| `diagnostico.py` | Script paso a paso para validar el protocolo contra un router real (independiente de `routers.json`, recibe ip/password por linea de comandos) |
| `requirements.txt` | Dependencias Python |
| `.env.example`, `routers.json.example` | Plantillas versionadas — copiar a `.env` / `routers.json` y completar |

## 10. Troubleshooting rapido

| Sintoma | Causa probable | Ver |
|---|---|---|
| Login falla, `LD` vacio | Firmware distinto al documentado | Seccion 3 |
| "Acceso denegado" en PowerShell | Falta abrir PowerShell como administrador manualmente | Seccion 5 |
| El router no aparece como adaptador de red | Sigue en modo CD-ROM | Seccion 4 |
| Se pierde internet/intranet al conectar el modem | Conflicto de ruta por defecto | Seccion 5 |
| Con varios routers, solo uno responde o hay timeouts intermitentes | Subred duplicada (todos en 192.168.0.1) | Seccion 6 |
