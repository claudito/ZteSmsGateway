# Manual de Instalacion - Bandeja de Notificaciones SMS DIRIS Lima Este (PC nueva, desde cero)

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
> metrica de red que configuras en el Paso 6 normalmente se mantiene sola
> despues de reconectar, no hace falta repetirla — pero si despues de
> reconectar perdes internet/intranet de nuevo, si hay que repetirla.

> Si vas a usar **un solo router**, salta directo al **Paso 6**.

## Paso 4 - Si vas a usar VARIOS routers: asignar una IP distinta a cada uno

Todos los MF920V traen de fabrica la misma IP (`192.168.0.1`). Si conectas
varios a la vez sin cambiar esto, van a chocar entre si. Hazlo de a **uno por
vez**, con los demas routers desconectados:

1. Con solo ese router conectado (repite el Paso 3 si es un equipo nuevo),
   abre el navegador y entra a `http://192.168.0.1`.
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
5. Cambia el campo de **Direccion IP** de `192.168.0.1` a una IP unica.
   Sugerencia de numeracion:
   - Router 1 -> `192.168.1.1`
   - Router 2 -> `192.168.2.1`
   - Router 3 -> `192.168.3.1`
   - (y asi sucesivamente)
   Actualiza tambien el **Pool IP para el servidor DHCP** para que caiga
   dentro de esa misma subred (por ejemplo, si la IP es `192.168.2.1`, el
   pool debe ir de `192.168.2.100` a `192.168.2.200`) - si lo dejas con el
   rango viejo (`192.168.0.x`), el DHCP queda apuntando a una subred que ya
   no existe. Deja igual la **Mascara de Subred** (`255.255.255.0`) y el
   resto de campos (MTU, MSS, etc).
6. Guarda los cambios (boton "Aplicar"). El router se reinicia (1-2
   minutos).
7. **Pega una etiqueta fisica en el router** con la IP que le asignaste - la
   vas a necesitar en el Paso 7.
8. Desconecta ese router, conecta el siguiente y repite desde el punto 1 con
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

## Paso 8 - Configurar `.env`

De vuelta en Git Bash, en la carpeta del proyecto (`C:\SMSGateway`), copia
la plantilla:

```bash
cp .env.example .env
```

Abre `.env` con el Bloc de notas (o VS Code) y completa:

```
SMS_API_KEY=CAMBIA-ESTO-POR-UNA-CLAVE-SECRETA
DASHBOARD_USER=elige-un-usuario
DASHBOARD_PASSWORD=elige-una-password
```

> `SMS_API_KEY` es la clave que usan las aplicaciones que llaman a la API
> directamente (el header `X-API-Key`). `DASHBOARD_USER` /
> `DASHBOARD_PASSWORD` son las credenciales para entrar al dashboard web
> con usuario y password — al iniciar sesion ahi, el dashboard obtiene la
> `SMS_API_KEY` solo internamente, no hace falta que la tipees a mano. Los
> routers en si (ip, password, numero) **no se configuran aca**: se agregan
> desde el dashboard en el siguiente paso.

## Paso 9 - Arrancar la API

Desde Git Bash, dentro de `C:\SMSGateway`:

```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

Debe quedar la ventana abierta mostrando `Uvicorn running on
http://0.0.0.0:8000` (no la cierres mientras quieras usar la API).

## Paso 10 - Agregar tus routers desde el dashboard y probar

1. Abre un navegador en esta misma PC y entra a `http://localhost:8000/`.
2. Ingresa con el `DASHBOARD_USER` / `DASHBOARD_PASSWORD` que pusiste en
   `.env`.
3. En la seccion "Routers", dale a "Agregar router" (abre un formulario en
   una ventana modal) por cada router: id, ip — la que le asignaste en el
   Paso 4 —, password, y opcionalmente el numero de la linea. Al guardar
   deberia aparecer en la tabla. El lapiz de cada fila permite editarlo
   despues (dejar la password en blanco al editar la conserva tal cual
   esta); el tacho lo elimina, pidiendo confirmacion.
4. Envia un SMS de prueba. La forma mas simple es desde el propio
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
5. El dashboard se actualiza solo cada 30s (indicador arriba a la derecha),
   asi que en unos segundos deberias ver el mensaje reflejado en "Resumen"
   y en la tabla de "Mensajes" sin necesidad de recargar la pagina. Repite
   el punto 4 para cada router que hayas configurado.

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
