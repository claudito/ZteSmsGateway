# Guia: VM con passthrough USB para varios routers ZTE por USB a la vez

Contexto: los routers ZTE MF920V no pueden convivir 2+ por USB en la misma
PC (mismo MAC de fabrica, sin puerto AT para desactivarlo de forma
permanente — ver seccion 6 de
[DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md)). Esta guia arma una
maquina virtual con **passthrough USB real** para el segundo router (y una
VM adicional por cada router extra que necesites), de forma que cada uno
tenga su propio stack de USB/red aislado y no choquen entre si.

Router 1 se queda conectado directo a la PC (host), como siempre. Solo los
routers adicionales van dentro de su propia VM.

## Paso 1 - Instalar VMware Workstation Pro

Desde 2024, VMware Workstation Pro es gratuito para cualquier uso (personal
y comercial/institucional) — a diferencia de VirtualBox, cuyo soporte de
USB 2.0/3.0 requiere el "Extension Pack" con licencia paga para uso no
personal.

1. Entra a `https://www.vmware.com/products/workstation-pro.html` y
   descarga el instalador para Windows.
2. Instala con las opciones por defecto (no requiere permisos especiales
   mas alla de la instalacion misma).
3. Abre VMware Workstation Pro una vez instalado para confirmar que arranca
   bien.

## Paso 2 - Crear la VM

1. "Create a New Virtual Machine" (o `Ctrl+N`).
2. Tipo: **Typical**.
3. Fuente del sistema operativo: un ISO de Windows (misma edicion que
   tengas licencia para usar - si no tienes una licencia de Windows extra
   disponible, puedes usar una VM Linux liviana en su lugar, pero los pasos
   de esta guia asumen Windows para reusar `ResetCDROM.exe` tal cual).
4. Asigna: 2 GB RAM, 1 CPU, 40 GB disco - de sobra para esta tarea, no corre
   nada pesado.
5. Nombra la VM de forma clara, ej. `Router2-USB`.
6. Termina el asistente e instala Windows dentro de la VM normalmente.

## Paso 3 - Configurar el controlador USB de la VM

1. Con la VM apagada, click derecho -> **Settings** (Configuracion).
2. Agrega un **USB Controller** si no existe uno, tipo **USB 2.0** o
   **3.0** (el router funciona bien con 2.0).
3. Guarda y enciende la VM.

## Paso 4 - Pasar el router2 a la VM (passthrough)

1. Conecta el router2 por USB a la PC fisica (host) como siempre.
2. Con la VM encendida, en la barra de VMware: **VM -> Removable Devices**
   -> busca el nombre del router (aparecera como `ZTE... CD-ROM` mientras
   este en modo CD-ROM) -> **Connect (Disconnect from Host)**.
3. Esto hace que el dispositivo **desaparezca del host** y aparezca dentro
   de la VM como si estuviera conectado directo a ella.

## Paso 5 - Dentro de la VM: lo de siempre

Repite exactamente el mismo proceso que ya conoces del host, pero adentro
de la VM:

1. Busca la unidad `ZTEMODEM` en "Este equipo" (dentro de la VM).
2. Corre `ResetCDROM.exe`.
3. Confirma que aparece el adaptador **RNDIS** con
   `Get-NetAdapter | Where-Object { $_.InterfaceDescription -match "RNDIS" }`
   (todo esto corriendo dentro de la VM, no en el host).
4. Ajusta la metrica de esa interfaz igual que en la seccion 5 de
   `DOCUMENTACION_TECNICA.md`:
   ```powershell
   Set-NetIPInterface -InterfaceAlias "Ethernet X" -InterfaceMetric 6000
   ```
5. Confirma que `http://192.168.28.10/` (o la IP que le hayas asignado a
   ese router) carga **desde el navegador de la VM**.

En este punto el router2 esta 100% aislado en su propia VM, sin pelear con
el router1 del host.

## Paso 6 - Reenviar el puerto del router hacia el host

El proceso de la API corre en el **host**, no en la VM, asi que necesita
poder llegar al router2 a traves de la VM. Se hace con reenvio de puertos:

1. Dentro de la VM, abre PowerShell como Administrador y crea el reenvio
   local (de un puerto de la VM hacia la IP del router):
   ```powershell
   netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8080 connectaddress=192.168.28.10 connectport=80
   ```
2. En VMware, con la VM apagada o encendida: **VM -> Settings -> Network
   Adapter** -> confirma que esta en modo **NAT** (deberia estarlo por
   defecto).
3. Abre **Edit -> Virtual Network Editor** (puede pedir "Change Settings"
   con permisos de administrador) -> selecciona la red NAT que usa la VM
   (usualmente `VMnet8`) -> **NAT Settings** -> **Add** un reenvio de
   puertos:
   - Host port: `8082` (el que quieras, libre en el host)
   - Type: TCP
   - VM IP address: la IP interna de la VM dentro de esa red NAT (verla con
     `ipconfig` dentro de la VM, adaptador que no sea el RNDIS)
   - VM port: `8080` (el mismo que usaste en el `portproxy` del paso 1)
4. Guarda. Desde el **host**, prueba:
   ```powershell
   curl http://localhost:8082/
   ```
   Deberia devolver la misma respuesta que `http://192.168.28.10/` dentro
   de la VM.

## Paso 7 - Actualizar el dashboard

En la seccion "Routers" del dashboard (`http://localhost:8000/`), edita
router2 y cambia su IP de `192.168.28.10` a `localhost:8082` (o la IP del
host + puerto si el dashboard corre en otra maquina). La API le sigue
hablando por HTTP normal, no necesita saber que hay una VM de por medio.

## Paso 8 - Dejar la VM siempre encendida

Como el reenvio de puertos solo funciona con la VM prendida:

1. En VMware, VM -> Settings -> Options -> **Power** -> marca que la VM se
   inicie automaticamente al abrir VMware (o usa `vmrun` para arrancarla
   por script al iniciar Windows).
2. Considera dejar VMware Workstation configurado para arrancar con
   Windows (Programador de tareas -> accion "Iniciar programa" ->
   `vmware.exe`, o usar `vmrun start "<ruta-al-.vmx>" nogui` para que la VM
   arranque sin abrir la ventana grafica).

## Si agregas un router3

Repite desde el Paso 2 con una VM nueva (`Router3-USB`), otro puerto de
reenvio distinto (ej. `8083`), y actualiza el dashboard con esa nueva IP
(`localhost:8083`).
