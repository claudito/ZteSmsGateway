"""
API HTTP que envuelve uno o varios ZTE MF920V para enviar SMS desde
cualquier equipo de la red local.

Configuracion:
    .env          -> secretos (SMS_API_KEY, passwords de los routers)
    routers.json  -> lista de routers (id + ip), sin secretos

Ejecutar:
    python -m uvicorn api:app --host 0.0.0.0 --port 8000

Llamar desde otro equipo de la red:
    POST http://<ip_de_esta_pc>:8000/routers/<id_router>/sms/send
    Header: X-API-Key: <API_KEY>
    Body JSON: {"phone": "+51987654321", "message": "Hola"}
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from zte_sms import ZteApiError, ZteSms

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ROUTERS_FILE = BASE_DIR / "routers.json"

API_KEY = os.environ.get("SMS_API_KEY", "")
DEFAULT_PASSWORD = os.environ.get("ZTE_ROUTER_PASSWORD", "admin")


def _load_routers() -> dict:
    if not ROUTERS_FILE.exists():
        raise RuntimeError(
            f"No se encontro {ROUTERS_FILE}. Copia routers.json.example a "
            "routers.json y completa tus routers."
        )
    with open(ROUTERS_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)

    routers = {}
    for entry in entries:
        router_id = entry["id"]
        password_env = f"ZTE_PASSWORD_{router_id.upper()}"
        password = os.environ.get(password_env, DEFAULT_PASSWORD)
        routers[router_id] = {"ip": entry["ip"], "password": password}
    return routers


ROUTERS = _load_routers()

app = FastAPI(title="SMS Gateway (ZTE MF920V)")


class SendSmsRequest(BaseModel):
    phone: str = Field(..., description="Numero destino, con codigo de pais. Ej: +51987654321")
    message: str = Field(..., min_length=1, max_length=600)


def check_api_key(x_api_key: str | None):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key invalida")


def get_router(router_id: str) -> dict:
    router = ROUTERS.get(router_id)
    if not router:
        raise HTTPException(status_code=404, detail=f"Router '{router_id}' no esta en routers.json")
    return router


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/routers")
def list_routers():
    return [{"id": router_id, "ip": data["ip"]} for router_id, data in ROUTERS.items()]


@app.post("/routers/{router_id}/sms/send")
def send_sms(router_id: str, req: SendSmsRequest, x_api_key: str | None = Header(default=None)):
    check_api_key(x_api_key)
    router = get_router(router_id)

    zte = ZteSms(router_ip=router["ip"], password=router["password"])
    try:
        zte.send_sms(req.phone, req.message)
    except ZteApiError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de conexion con el modem: {e}")
    finally:
        zte.logout()

    return {"status": "sent", "router": router_id, "phone": req.phone}
