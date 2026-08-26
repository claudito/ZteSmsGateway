# Manual de Instalacion - Bandeja de Notificaciones SMS DIRIS Lima Este (PC nueva, desde cero)

Guia paso a paso para instalar este SMS Gateway en una PC que **no tiene
Python, ni VSCode, ni ninguna herramienta de desarrollo instalada**, con
**un router ZTE MF920V** conectado por USB.

> Si necesitas mas de un router, cada uno va en su **propia PC** — no se
> pueden conectar 2+ routers ZTE por USB a la misma PC (limitacion de
> hardware, ver seccion 6 de
> [DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md)). Repite esta guia
> completa en cada PC.

Si algo falla en el camino y quieres entender el porque tecnico, revisa
[DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md).

## Lo que necesitas antes de empezar

- La carpeta completa de este proyecto (copiarla a la PC nueva, por ejemplo
  por USB).
- El router ZTE MF920V con su cable USB.
- Acceso a una cuenta de Windows con permisos de **Administrador** (o alguien
  que pueda hacer dos pasos puntuales por ti) - se explica exactamente donde
  hace falta.

Todos los comandos de esta guia estan escritos para **Git Bash** (la
terminal que instala Git para Windows). Los pasos 5 y 6 son la unica
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
3. **VS Code** (opcional, pero recomendado para editar `.env` mas comodo
   que con el Bloc de notas): ir a
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

> **Importante — esto se puede repetir despues, no es cosa de una sola vez:**
> si en cualquier momento el envio de SMS empieza a fallar con timeout y
> nadie toco la configuracion, lo mas probable es que el router haya vuelto
> a modo CD-ROM (por ejemplo si se desconecto el cable USB un momento, o la
> PC se suspendio). Repite el punto 3-5 de este paso: buscar la unidad
> `ZTEMODEM` en "Este equipo" y volver a correr `ResetCDROM.exe`. La
> metrica de red que configuras en el Paso 5 normalmente se mantiene sola
> despues de reconectar, no hace falta repetirla — pero si despues de
> reconectar perdes internet/intranet de nuevo, si hay que repetirla.

> **Cada PC solo maneja UN router.** Los MF920V no pueden convivir 2+ por
> USB en la misma PC (limitacion de hardware — mismo MAC de fabrica en
> todas las unidades, ver seccion 6 de
> [DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md)). Si necesitas mas
> de un router, repite esta guia completa en otra PC, una maquina por
> router — no lo intentes en la misma.

## Paso 4 - Asignar la IP fija al router

Todos los MF920V traen de fabrica la misma IP (`192.168.0.1`). Vamos a
cambiarla por una IP fija dentro del rango asignado:

> **Rango de IPs a usar:** el area de redes de DIRIS Lima Este asigno el
> rango `192.168.28.0/24` (VLAN-WIFI) para numerar estos routers. No uses
> `192.168.28.1` porque esa IP ya esta tomada como gateway de esa VLAN en la
> red real - usa `192.168.28.2` para el router de esta PC (si en otra PC ya
> usaste esa IP, usa la siguiente libre: `192.168.28.3`, `192.168.28.4`,
> etc. — cada PC es independiente, no hace falta que coincidan). Este rango
> no coincide con las subredes domesticas/de oficina mas comunes
> (`192.168.0.x`, `192.168.1.x`, `192.168.2.x`), asi que no deberia chocar
> con la red normal de la PC - igual puedes confirmarlo con `ipconfig` en
> Git Bash o PowerShell.

1. Abre el navegador y entra a `http://192.168.0.1`.
2. Inicia sesion (usuario `admin`, password de la etiqueta del equipo o
   `admin` por defecto).
3. Dentro de esa misma pagina web del router (no es configuracion de
   Windows/la PC), busca la seccion de configuracion de LAN del router
   (el menu exacto varia segun el modelo/idioma del equipo: algo como
   "Configuracion de red" > "LAN", "Network Settings" > "LAN Settings", o
   "Configuraciones avanzadas" > "Ajustes del Router", con el campo
   **Direccion IP**).
4. Si el campo aparece bloqueado con un aviso tipo "Las configuraciones
   solo pueden ser cambiadas cuando el modem esta desconectado", vuelve a
   la pantalla principal (flecha `<` junto al titulo, o el logo arriba a
   la izquierda) y en el bloque **"Mi equipo"** apaga el switch
   **"Datos"** (ON -> OFF). Eso corta solo la conexion de datos movil.
   Vuelve luego a "Ajustes del Router" y el campo ya deberia estar
   editable.
   > **Cuidado:** el enlace **"Apagar"** (arriba a la derecha, junto a
   > "Modificar contrasena") es distinto del switch "Datos": ese apaga el
   > equipo por completo. Si lo tocas por error, el router se apaga: para
   > volver a encenderlo, desconecta el cable USB y vuelve a conectarlo -
   > va a reaparecer como unidad `ZTEMODEM`, asi que hay que repetir el
   > Paso 3 (`ResetCDROM.exe`) para volver a acceder a el.
5. Cambia el campo de **Direccion IP** de `192.168.0.1` a la IP que le toca
   dentro del rango asignado (`192.168.28.0/24`, ver nota de arriba, ej.
   `192.168.28.2`). Actualiza tambien el **Pool IP para el servidor DHCP**
   para que caiga dentro de esa misma subred (por ejemplo, si la IP es
   `192.168.28.2`, el pool debe ir de `192.168.28.100` a `192.168.28.200`)
   - si lo dejas con el rango viejo (`192.168.0.x`), el DHCP queda
   apuntando a una subred que ya no existe. Deja igual la **Mascara de
   Subred** (`255.255.255.0`) y el resto de campos (MTU, MSS, etc).
6. Guarda los cambios (boton "Aplicar"). El router se reinicia (1-2
   minutos).
7. **Pega una etiqueta fisica en el router** con la IP que le asignaste - la
   vas a necesitar mas adelante.
8. Como es un solo router en esta PC, puedes precargarlo para que aparezca
   solo en el dashboard sin tener que agregarlo a mano despues. En la
   carpeta del proyecto, copia la plantilla y edita la IP:
   ```bash
   cp routers.json.example routers.json
   ```
   Deja una sola entrada, con la IP que le asignaste:
   ```json
   [
     {"id": "router1", "ip": "192.168.28.2"}
   ]
   ```
   Esto solo funciona **antes** de arrancar la API por primera vez (Paso 8)
   — es una importacion de un solo uso.

> **Si esa IP choca con otro equipo de tu red** (por ejemplo, al entrar a
> esa IP te aparece el login de otra cosa - una impresora, otro router,
> etc. - en vez del router ZTE): desconecta temporalmente el Wifi/cable de
> red de la PC dejando solo el router conectado por USB, entra de nuevo a
> esa misma IP (ahora si deberia ser el router, sin competencia de la otra
> red), y repite el punto 5 con una IP que no choque. Reconecta el
> Wifi/cable de red al terminar.

## Paso 5 - Arreglar el conflicto de ruta de red (requiere Administrador + PowerShell)

Al conectarse, los routers intentan volverse la puerta de enlace principal
de internet de la PC, lo que puede hacerte perder acceso a internet o a la
red interna de tu institucion. Para evitarlo, **esto lo tiene que hacer
alguien con permisos de administrador, y en PowerShell** (los comandos de
este paso no existen en Git Bash porque son cmdlets nativos de Windows).
No funciona intentarlo desde un script sin interaccion humana, porque
Windows pide confirmar con un clic:

1. Busca "PowerShell" en el menu Inicio, clic derecho > **"Ejecutar como
   administrador"**.
2. Lista el adaptador del router conectado:
   ```powershell
   Get-NetAdapter | Where-Object { $_.InterfaceDescription -match "RNDIS" } | Select-Object Name
   ```
3. Con el nombre que te devuelva (cambia `"Ethernet X"` por el real):
   ```powershell
   Set-NetIPInterface -InterfaceAlias "Ethernet X" -InterfaceMetric 6000
   ```
4. Verifica que sigues teniendo internet/intranet normal, y que llegas al
   router por su IP:
   ```powershell
   curl http://192.168.28.2/
   ```

## Paso 6 - Abrir el firewall (requiere Administrador)

En la misma PowerShell de administrador del paso anterior:

```powershell
netsh advfirewall firewall add rule name="SMS Gateway API" dir=in action=allow protocol=TCP localport=8000
```

## Paso 7 - Configurar `.env`

De vuelta en Git Bash, en la carpeta del proyecto (`C:\SMSGateway`), copia
la plantilla:

```bash
cp .env.example .env
```

Abre `.env` con el Bloc de notas (o VS Code) y completa:

```
SMS_API_KEY=CAMBIA-ESTO-POR-UNA-CLAVE-SECRETA
ZTE_ROUTER_PASSWORD=la-password-del-router
```

> `SMS_API_KEY` es la clave que usan las aplicaciones que llaman a la API
> directamente (el header `X-API-Key`) — el dashboard tambien la usa por
> detras. `ZTE_ROUTER_PASSWORD` es la password del router (la de la
> etiqueta del equipo, o `admin` por defecto) — la usa la importacion de
> `routers.json` del Paso 4.8 para poder loguearse a ese router.
>
> Como es una sola PC con un solo router de uso interno, **deja
> `DASHBOARD_USER` y `DASHBOARD_PASSWORD` vacios o bórralos** de `.env` (o
> de la plantilla, si no los copiaste) — asi el dashboard no pide login al
> abrirlo. Si mas adelante quieres que si pida usuario/password, solo
> agrega esas dos lineas con los valores que quieras.

## Paso 8 - Arrancar la API

Desde Git Bash, dentro de `C:\SMSGateway`:

```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

Debe quedar la ventana abierta mostrando `Uvicorn running on
http://0.0.0.0:8000` (no la cierres mientras quieras usar la API).

## Paso 9 - Verificar el router en el dashboard y probar

1. Abre un navegador en esta misma PC y entra a `http://localhost:8000/`.
   Si dejaste `DASHBOARD_USER`/`DASHBOARD_PASSWORD` vacios en el Paso 7,
   entra directo sin pedir login.
2. En la seccion "Routers" deberia aparecer ya el router (viene de la
   importacion de `routers.json` del Paso 4.8). Si no aparece, dale a
   "Agregar router" y complétalo a mano: id, ip, password, y opcionalmente
   el numero de la linea. El lapiz de la fila permite editarlo despues
   (dejar la password en blanco al editar la conserva tal cual esta); el
   tacho lo elimina, pidiendo confirmacion.
3. Envia un SMS de prueba. La forma mas simple es desde el propio
   dashboard: boton **"Enviar SMS"** (junto a "Agregar router") — abre un
   modal donde eliges el router, el numero de celular y el mensaje. Si
   falla, el modal muestra el error tal cual lo devuelve el router (por
   ejemplo timeout de conexion — ver la nota del Paso 3 sobre el modo
   CD-ROM). Tambien se puede probar por linea de comandos, desde otra
   terminal Git Bash (cambia `router1` por el id que hayas usado):
   ```bash
   curl -X POST http://<ip_de_esta_pc>:8000/routers/router1/sms/send \
     -H "Content-Type: application/json" \
     -H "X-API-Key: CAMBIA-ESTO-POR-UNA-CLAVE-SECRETA" \
     -d '{"phone": "+51987654321", "message": "Prueba"}'
   ```
   Respuesta esperada: `{"status":"sent","router":"router1","phone":"+51987654321"}`.
4. El dashboard se actualiza solo cada 30s (indicador arriba a la derecha),
   asi que en unos segundos deberias ver el mensaje reflejado en "Resumen"
   y en la tabla de "Mensajes" sin necesidad de recargar la pagina.

## Paso 10 - Si algo falla: diagnostico

Corre esto para ver, paso a paso, en que falla la comunicacion con un router
en particular (cambia el numero, password e IP segun corresponda):

```bash
python diagnostico.py +51987654321 admin 192.168.28.2
```

El mensaje de error, si lo hay, indica exactamente en que paso se rompio
(conexion, login o envio) y trae la respuesta cruda del router para poder
ajustar el protocolo si ese equipo tiene un firmware distinto (ver la
seccion 3 de [DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md)).

## Paso 11 (opcional) - Dejarlo corriendo siempre

La ventana de `uvicorn` hay que dejarla abierta manualmente, o programar que
inicie sola con Windows (Programador de tareas) o correrla como servicio con
una herramienta como `nssm`. Si lo necesitas, es un paso aparte - pide que
te lo documenten cuando llegues a esa etapa.
