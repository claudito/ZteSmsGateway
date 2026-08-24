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

## 7. Dashboard y base de datos

Un solo proceso de la API sirve **todos** los routers configurados, y guarda
tanto la configuracion de cada router como el historial de SMS en un
archivo SQLite local, `sms_gateway.db` (se crea solo al arrancar, no
versionado — ver `.gitignore`). El unico secreto que sigue viviendo en
`.env` es `SMS_API_KEY`, la clave compartida de la API.

`GET /` sirve un dashboard (`static/dashboard.html`, HTML+JS plano, sin
dependencias externas) donde se administra todo desde el navegador:

- Pide la `SMS_API_KEY` una vez (queda en `localStorage` del navegador) y la
  manda como header `X-API-Key` en cada llamada a la API — el dashboard no
  inventa un mecanismo de autenticacion propio, reusa el mismo que ya
  protege `/sms/send`.
- **Resumen:** total de SMS enviados/fallidos, y un total por router.
- **Routers:** tabla con id/ip/numero/enviados/fallidos, con alta (mismo
  formulario sirve para editar, hace upsert por id) y baja.
- **Mensajes:** historial completo, filtrable por router.

### Esquema de la base de datos (`db.py`)

```sql
routers (id TEXT PK, ip TEXT, password TEXT, numero TEXT, created_at TEXT)
messages (id INTEGER PK, router_id TEXT, phone TEXT, message TEXT,
          status TEXT CHECK IN ('sent','failed'), error TEXT, created_at TEXT)
```

Cada funcion de `db.py` abre y cierra su propia conexion `sqlite3` (una
conexion no es segura para compartir entre threads, y FastAPI corre los
endpoints `def` normales — no `async def` — en un threadpool).

### Migracion desde `routers.json` (version anterior del proyecto)

Antes de esto, los routers se configuraban a mano en `routers.json` +
variables `ZTE_PASSWORD_<ID>` en `.env` (ver commits/documentacion
anteriores). Para no romper esa configuracion ya hecha, `db.init_db()`
corre una migracion de una sola vez: si la tabla `routers` esta vacia y
existe un `routers.json` en la carpeta del proyecto, importa cada entrada
resolviendo su password de la misma forma que antes (`ZTE_PASSWORD_<ID>` o
`ZTE_ROUTER_PASSWORD` como default). Despues de esa primera vez, el archivo
`routers.json` ya no se vuelve a leer — toda la administracion pasa a ser
via dashboard/API contra la base de datos. `routers.json.example` se
mantiene solo como referencia de ese formato de migracion.

## 8. Endpoints de la API

Todos (salvo `/health` y `GET /`) requieren el header `X-API-Key` si
`SMS_API_KEY` esta definida en `.env`.

```
GET    /health
GET    /                          -> dashboard (HTML)

GET    /routers                   -> [{"id","ip","numero","created_at"}, ...]
PUT    /routers/{id}              Body: {"ip","password","numero"?}  -> crea o actualiza (upsert)
DELETE /routers/{id}               -> {"status":"deleted","router":"..."}

POST   /routers/{id}/sms/send     Body: {"phone","message"}
  -> {"status":"sent","router":"...","phone":"..."}
  -> 404 si el id no existe; 401 si falta/no coincide X-API-Key
  -> registra el intento en `messages` (sent o failed, con el error si aplica)
     independientemente del resultado

GET    /messages?router_id=&limit=200      -> historial (todos los routers o uno)
GET    /routers/{id}/messages?limit=200    -> historial de un router
GET    /stats                              -> [{"router_id","numero","sent","failed"}, ...]
```

Agregar un router nuevo es un `PUT /routers/{id}` (desde el dashboard o por
API) — no hace falta tocar codigo, archivos de configuracion, ni reiniciar
el proceso.

## 9. Archivos del proyecto

| Archivo | Rol |
|---|---|
| `zte_sms.py` | Cliente del protocolo del router (login, envio de SMS) |
| `db.py` | Acceso a `sms_gateway.db` (SQLite): CRUD de routers, historial de mensajes, stats, migracion desde `routers.json` |
| `api.py` | API HTTP (FastAPI); carga `.env`, inicializa la base, expone endpoints de routers/SMS/mensajes/stats y sirve el dashboard |
| `static/dashboard.html` | Dashboard web (HTML+JS plano, sin dependencias externas) — resumen, alta/baja de routers, historial de mensajes |
| `diagnostico.py` | Script paso a paso para validar el protocolo contra un router real (independiente de la base de datos, recibe ip/password por linea de comandos) |
| `requirements.txt` | Dependencias Python |
| `.env.example` | Plantilla versionada — copiar a `.env` y completar `SMS_API_KEY` |
| `routers.json.example` | Formato de migracion de una sola vez (ver seccion 7) — los routers se administran por el dashboard de ahi en mas |
| `configurar_vscode_gitbash.ps1` | Script opcional: configura Git Bash como terminal por defecto en VS Code (ver [MANUAL_INSTALACION.md](MANUAL_INSTALACION.md)) |

## 10. Troubleshooting rapido

| Sintoma | Causa probable | Ver |
|---|---|---|
| Login falla, `LD` vacio | Firmware distinto al documentado | Seccion 3 |
| "Acceso denegado" en PowerShell | Falta abrir PowerShell como administrador manualmente | Seccion 5 |
| El router no aparece como adaptador de red | Sigue en modo CD-ROM | Seccion 4 |
| Se pierde internet/intranet al conectar el modem | Conflicto de ruta por defecto | Seccion 5 |
| Con varios routers, solo uno responde o hay timeouts intermitentes | Subred duplicada (todos en 192.168.0.1) | Seccion 6 |
| El dashboard (`/`) queda pidiendo la API key y no carga nada | La clave pegada no coincide con `SMS_API_KEY` de `.env` (el navegador recibe 401) | Seccion 7 |
