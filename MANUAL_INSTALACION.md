# Manual de Instalacion - SMS Gateway ZTE MF920V (PC nueva, desde cero)

Guia paso a paso para instalar este SMS Gateway en una PC que **no tiene
Python, ni VSCode, ni ninguna herramienta de desarrollo instalada**, y que
va a manejar **uno o varios routers ZTE MF920V** conectados por USB al mismo
tiempo.

Si algo falla en el camino y quieres entender el porque tecnico, revisa
[DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md).

## Lo que necesitas antes de empezar

- La carpeta completa de este proyecto (copiarla a la PC nueva, por ejemplo
  por USB).
- El o los routers ZTE MF920V, cada uno con su cable USB.
- Acceso a una cuenta de Windows con permisos de **Administrador** (o alguien
  que pueda hacer dos pasos puntuales por ti) - se explica exactamente donde
  hace falta.

Todos los comandos de esta guia estan escritos para **Git Bash** (la
terminal que instala Git para Windows). Los pasos 6 y 7 son la unica
excepcion: usan comandos de red que solo existen en PowerShell.

---

## Paso 1 - Instalar Python, Git Bash y VS Code

1. **Python:** ir a https://www.python.org/downloads/, descargar la version
   mas reciente para Windows y ejecutar el instalador.
   **Importante:** en la primera pantalla del instalador, marcar la casilla
   **"Add python.exe to PATH"** antes de darle a "Install Now".
2. **Git Bash:** ir a https://git-scm.com/downloads/win, descargar e
   instalar "Git for Windows" (dejar las opciones por defecto esta bien).
   Esto instala la terminal **Git Bash** que se usa en el resto de esta
   guia (y trae `curl` incluido).
3. **VS Code** (opcional, pero recomendado para editar `.env` /
   `routers.json` mas comodo que con el Bloc de notas): ir a
   https://code.visualstudio.com/download, descargar e instalar "VS Code"
   para Windows (dejar las opciones por defecto esta bien).
4. Al terminar, busca "Git Bash" en el menu Inicio, abrelo, y verifica:
   ```bash
   python --version
   ```
   Debe mostrar algo como `Python 3.13.x`. Si dice que no reconoce el
   comando, reinicia la PC y vuelve a probar (a veces hace falta para que
   tome el cambio del PATH).

### Configurar Git Bash como terminal por defecto en VS Code

Si instalaste VS Code, su terminal integrada abre PowerShell por defecto.
Para que abra Git Bash en su lugar (y no tengas que cambiarla a mano cada
vez), este proyecto trae un script que lo configura solo:

```bash
powershell -ExecutionPolicy Bypass -File configurar_vscode_gitbash.ps1
```

Esto edita el `settings.json` de VS Code agregando Git Bash como terminal
por defecto, sin tocar el resto de tu configuracion (guarda un backup
`settings.json.bak` antes de escribir). Si tu `settings.json` ya tenia
comentarios y el script no pudo editarlo solo, te va a mostrar en pantalla
el fragmento exacto para pegar a mano (Ctrl+, en VS Code, luego el icono de
"Abrir configuracion (JSON)" arriba a la derecha). Reinicia VS Code despues
para que tome el cambio.

## Paso 2 - Copiar el proyecto e instalar dependencias

1. Copia la carpeta del proyecto a, por ejemplo, `C:\SMSGateway`.
2. Abre Git Bash dentro de esa carpeta (clic derecho sobre la carpeta en el
   Explorador de archivos > **"Git Bash Here"**; si no aparece esa opcion,
   abre Git Bash normal y usa `cd /c/SMSGateway`).
3. Instala las dependencias (no hace falta entorno virtual):
   ```bash
   pip install -r requirements.txt
   ```

## Paso 3 - Conectar el primer router ZTE

1. Conecta el MF920V a un puerto USB.
2. Espera unos segundos. **Es normal** que Windows lo detecte primero como
   una unidad de CD-ROM (aparece en "Este equipo" con el nombre
   `ZTEMODEM`), no como un adaptador de red todavia.
3. Abre esa unidad en el Explorador de archivos (por ejemplo `E:\`), entra a
   la carpeta `Data`, y haz doble clic en `ResetCDROM.exe`.
   - No deberia pedir permisos de administrador.
   - Puede que no aparezca ninguna ventana visible - es normal, no es un
     error.
4. Espera 5-10 segundos y verifica: busca "Ver adaptadores de red" en el
   buscador de Windows (o Panel de Control > Redes). Debe aparecer uno
   nuevo, con un nombre parecido a **"Remote NDIS based Internet Sharing
   Device"**, en estado conectado.
5. Confirma que respondes al router desde Git Bash:
   ```bash
   curl http://192.168.0.1/
   ```
   Si devuelve algo (aunque sea HTML de error), el router ya es accesible.

> Si vas a usar **un solo router**, salta directo al **Paso 6**.

## Paso 4 - Si vas a usar VARIOS routers: asignar una IP distinta a cada uno

Todos los MF920V traen de fabrica la misma IP (`192.168.0.1`). Si conectas
varios a la vez sin cambiar esto, van a chocar entre si. Hazlo de a **uno por
vez**, con los demas routers desconectados:

1. Con solo ese router conectado (repite el Paso 3 si es un equipo nuevo),
   abre el navegador y entra a `http://192.168.0.1`.
2. Inicia sesion (usuario `admin`, password de la etiqueta del equipo o
   `admin` por defecto).
3. Busca la seccion de configuracion de LAN (el menu exacto varia segun el
   idioma del equipo: algo como "Configuracion de red" > "LAN", o
   "Network Settings" > "LAN Settings").
4. Cambia el campo de **Direccion IP** de `192.168.0.1` a una IP unica.
   Sugerencia de numeracion:
   - Router 1 -> `192.168.1.1`
   - Router 2 -> `192.168.2.1`
   - Router 3 -> `192.168.3.1`
   - (y asi sucesivamente)
5. Guarda los cambios. El router se reinicia (1-2 minutos).
6. **Pega una etiqueta fisica en el router** con la IP que le asignaste - la
   vas a necesitar en el Paso 7.
7. Desconecta ese router, conecta el siguiente y repite desde el punto 1 con
   la IP que le corresponda.

## Paso 5 - Conectar todos los routers a la vez

Con cada router ya en su propia IP, puedes conectarlos todos por USB al
mismo tiempo. La primera vez que cada uno se conecta a **esta** PC, hay que
repetir el Paso 3.2-3.3 (`ResetCDROM.exe`) para ese router - despues de
eso queda "recordado" mientras uses ese mismo puerto/router.

## Paso 6 - Arreglar el conflicto de ruta de red (requiere Administrador + PowerShell)

Al conectarse, los routers intentan volverse la puerta de enlace principal
de internet de la PC, lo que puede hacerte perder acceso a internet o a la
red interna de tu institucion. Para evitarlo, **esto lo tiene que hacer
alguien con permisos de administrador, y en PowerShell** (los comandos de
este paso no existen en Git Bash porque son cmdlets nativos de Windows).
No funciona intentarlo desde un script sin interaccion humana, porque
Windows pide confirmar con un clic:

1. Busca "PowerShell" en el menu Inicio, clic derecho > **"Ejecutar como
   administrador"**.
2. Lista los adaptadores de los routers conectados:
   ```powershell
   Get-NetAdapter | Where-Object { $_.InterfaceDescription -match "RNDIS" } | Select-Object Name
   ```
3. Para **cada** adaptador que aparezca en la lista (uno por router
   conectado), ejecuta (cambiando `"Ethernet X"` por el nombre real):
   ```powershell
   Set-NetIPInterface -InterfaceAlias "Ethernet X" -InterfaceMetric 6000
   ```
4. Verifica que sigues teniendo internet/intranet normal, y que llegas a
   cada router por su IP:
   ```powershell
   curl http://192.168.1.1/
   curl http://192.168.2.1/
   ```

## Paso 7 - Abrir el firewall (requiere Administrador)

Un solo proceso de la API atiende a todos los routers en un solo puerto, asi
que solo hace falta **una** regla de firewall (en la misma PowerShell de
administrador del paso anterior):

```powershell
netsh advfirewall firewall add rule name="SMS Gateway API" dir=in action=allow protocol=TCP localport=8000
```

## Paso 8 - Configurar `.env` y `routers.json`

De vuelta en Git Bash, en la carpeta del proyecto (`C:\SMSGateway`), copia
las dos plantillas:

```bash
cp .env.example .env
cp routers.json.example routers.json
```

Abre `.env` con el Bloc de notas y completa:

```
SMS_API_KEY=CAMBIA-ESTO-POR-UNA-CLAVE-SECRETA
ZTE_ROUTER_PASSWORD=admin
```

> `SMS_API_KEY` es la clave que va a tener que mandar cualquiera que use la
> API — es lo unico que evita que cualquiera en la red envie SMS con tus
> routers. `ZTE_ROUTER_PASSWORD` es la password web que usan tus routers
> (la de la etiqueta, `admin` si no la cambiaste).

Abre `routers.json` y pon un id + la IP de cada router que configuraste en
el Paso 4 (o `192.168.0.1` si es uno solo):

```json
[
  {"id": "router1", "ip": "192.168.1.1"},
  {"id": "router2", "ip": "192.168.2.1"}
]
```

> Si alguno de tus routers tiene una password web distinta a la de
> `ZTE_ROUTER_PASSWORD`, agrega en `.env` una linea
> `ZTE_PASSWORD_<ID EN MAYUSCULAS>=esa-password` (por ejemplo
> `ZTE_PASSWORD_ROUTER2=otra-clave` para el router con id `router2`).

Para agregar un router mas adelante, solo hay que sumar una linea a
`routers.json` (y, si hace falta, una variable a `.env`) — no hay que crear
nada mas ni reinstalar nada.

## Paso 9 - Arrancar la API

Desde Git Bash, dentro de `C:\SMSGateway`:

```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

Debe quedar la ventana abierta mostrando `Uvicorn running on
http://0.0.0.0:8000` (no la cierres mientras quieras usar la API).

## Paso 10 - Probar

1. Abre otra ventana de Git Bash y confirma que la API reconocio tus
   routers:
   ```bash
   curl http://localhost:8000/routers
   ```
   Debe listar los ids e IPs que pusiste en `routers.json`.
2. Envia un SMS de prueba (cambia `router1` por el id que quieras usar):
   ```bash
   curl -X POST http://<ip_de_esta_pc>:8000/routers/router1/sms/send \
     -H "Content-Type: application/json" \
     -H "X-API-Key: CAMBIA-ESTO-POR-UNA-CLAVE-SECRETA" \
     -d '{"phone": "+51987654321", "message": "Prueba"}'
   ```
   Respuesta esperada: `{"status":"sent","router":"router1","phone":"+51987654321"}`.
3. Repite cambiando `router1` por cada id que hayas configurado.

## Paso 11 - Si algo falla: diagnostico

Corre esto para ver, paso a paso, en que falla la comunicacion con un router
en particular (cambia el numero, password e IP segun corresponda):

```bash
python diagnostico.py +51987654321 admin 192.168.1.1
```

El mensaje de error, si lo hay, indica exactamente en que paso se rompio
(conexion, login o envio) y trae la respuesta cruda del router para poder
ajustar el protocolo si ese equipo tiene un firmware distinto (ver la
seccion 3 de [DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md)).

## Paso 12 (opcional) - Dejarlo corriendo siempre

La ventana de `uvicorn` hay que dejarla abierta manualmente, o programar que
inicie sola con Windows (Programador de tareas) o correrla como servicio con
una herramienta como `nssm`. Si lo necesitas, es un paso aparte - pide que
te lo documenten cuando llegues a esa etapa.
