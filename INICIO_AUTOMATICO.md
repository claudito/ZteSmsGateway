# Arranque automático al iniciar Windows

Ya existe `iniciar_api.bat` en la raíz del proyecto (`D:\Proyectos\Python\ZteSmsGateway`):

```bat
@echo off
cd /d D:\Proyectos\Python\ZteSmsGateway
python -m uvicorn api:app --host 0.0.0.0 --port 8000 >> log.txt 2>&1
```

## Registrar la tarea

Abrir **PowerShell como Administrador** y ejecutar:

```powershell
schtasks /create /tn "SMS Gateway API" /tr "D:\Proyectos\Python\ZteSmsGateway\iniciar_api.bat" /sc onlogon /rl highest /f
```

Esto crea una tarea que arranca `iniciar_api.bat` apenas esa cuenta de Windows
inicia sesión.

> Para que quede listo sin depender de que alguien desbloquee la PC, configurar
> **inicio de sesión automático** de esa cuenta (o dejar la sesión siempre
> iniciada y solo bloqueada, nunca cerrada).

## Probar

Antes de probar, cerrar cualquier `uvicorn` corriendo a mano en el puerto 8000
(si no, la tarea fallará por puerto ocupado):

```powershell
schtasks /run /tn "SMS Gateway API"
```

Luego entrar a `http://localhost:8000/` — debería responder. También se puede
reiniciar la PC y verificar que arranca solo al llegar al escritorio.

## Ver logs / errores

La salida (incluidos errores) queda en `log.txt`, en la raíz del proyecto.

## Detener el proceso que quedó corriendo

Si la tarea ya arrancó la API y quieres pararla (sin desactivar la tarea, o
sea que puede volver a arrancar en el próximo logon):

```powershell
schtasks /end /tn "SMS Gateway API"
```

Si eso no la corta (por ejemplo porque la iniciaste a mano, no por la tarea),
mata el proceso que tiene el puerto 8000 abierto:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

## Desactivar / quitar la tarea

```powershell
schtasks /delete /tn "SMS Gateway API" /f
```

Esto solo quita el registro en el Programador de tareas — no mata un proceso
que ya esté corriendo (usar la sección anterior para eso).

## Alternativa más robusta (opcional)

`schtasks /sc onlogon` depende de que haya una sesión de Windows iniciada. Si
más adelante se necesita que la API se reinicie sola si se cae, sin depender
de una sesión abierta, correrla como **servicio de Windows** con una
herramienta como [`nssm`](https://nssm.cc/) — es un paso aparte, no cubierto
aquí.
