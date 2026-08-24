"""
API HTTP que envuelve uno o varios ZTE MF920V para enviar SMS desde
cualquier equipo de la red local, con historial en SQLite y un dashboard
web para configurar routers y ver los mensajes enviados.

Configuracion:
    .env         -> SMS_API_KEY (secreto compartido de la API)
    sms_gateway.db -> routers (id, ip, password, numero) y mensajes enviados,
                      administrados desde el dashboard web (GET /)

Ejecutar:
    python -m uvicorn api:app --host 0.0.0.0 --port 8000

Llamar desde otro equipo de la red:
    POST http://<ip_de_esta_pc>:8000/routers/<id_router>/sms/send
    Header: X-API-Key: <API_KEY>
    Body JSON: {"phone": "+51987654321", "message": "Hola"}
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import db
from zte_sms import ZteApiError, ZteSms

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
API_KEY = os.environ.get("SMS_API_KEY", "")

db.init_db()

app = FastAPI(title="SMS Gateway (ZTE MF920V)")


class SendSmsRequest(BaseModel):
    phone: str = Field(..., description="Numero destino, con codigo de pais. Ej: +51987654321")
    message: str = Field(..., min_length=1, max_length=600)


class RouterIn(BaseModel):
    ip: str
    password: str
    numero: str | None = None


def check_api_key(x_api_key: str | None):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key invalida")


def get_router_or_404(router_id: str) -> dict:
    router = db.get_router(router_id)
    if not router:
        raise HTTPException(status_code=404, detail=f"Router '{router_id}' no existe")
    return router


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def dashboard():
    return FileResponse(BASE_DIR / "static" / "dashboard.html")


# ---------- routers ----------

@app.get("/routers")
def list_routers(x_api_key: str | None = Header(default=None)):
    check_api_key(x_api_key)
    return db.list_routers()


@app.put("/routers/{router_id}")
def upsert_router(router_id: str, req: RouterIn, x_api_key: str | None = Header(default=None)):
    check_api_key(x_api_key)
    return db.upsert_router(router_id, req.ip, req.password, req.numero)


@app.delete("/routers/{router_id}")
def remove_router(router_id: str, x_api_key: str | None = Header(default=None)):
    check_api_key(x_api_key)
    if not db.delete_router(router_id):
        raise HTTPException(status_code=404, detail=f"Router '{router_id}' no existe")
    return {"status": "deleted", "router": router_id}


# ---------- SMS ----------

@app.post("/routers/{router_id}/sms/send")
def send_sms(router_id: str, req: SendSmsRequest, x_api_key: str | None = Header(default=None)):
    check_api_key(x_api_key)
    router = get_router_or_404(router_id)

    zte = ZteSms(router_ip=router["ip"], password=router["password"])
    try:
        zte.send_sms(req.phone, req.message)
    except ZteApiError as e:
        db.log_message(router_id, req.phone, req.message, "failed", str(e))
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        error = f"Error de conexion con el modem: {e}"
        db.log_message(router_id, req.phone, req.message, "failed", error)
        raise HTTPException(status_code=500, detail=error)
    finally:
        zte.logout()

    db.log_message(router_id, req.phone, req.message, "sent")
    return {"status": "sent", "router": router_id, "phone": req.phone}


# ---------- historial y estadisticas ----------

@app.get("/messages")
def list_messages(router_id: str | None = None, limit: int = 200, x_api_key: str | None = Header(default=None)):
    check_api_key(x_api_key)
    return db.list_messages(router_id, limit)


@app.get("/routers/{router_id}/messages")
def list_router_messages(router_id: str, limit: int = 200, x_api_key: str | None = Header(default=None)):
    check_api_key(x_api_key)
    get_router_or_404(router_id)
    return db.list_messages(router_id, limit)


@app.get("/stats")
def get_stats(x_api_key: str | None = Header(default=None)):
    check_api_key(x_api_key)
    return db.stats()
