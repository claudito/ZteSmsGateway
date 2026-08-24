"""
Cliente para enviar SMS a traves de la API web (goform) de routers/MiFi ZTE,
como el ZTE MF920V con firmware Entel Peru (ufi/mf9xx, PASSWORD_ENCODE=true):
login por Base64 del password, sin LD/SHA256, sin token AD y sin cookie de
sesion (el router identifica la sesion por IP de origen).

Protocolo obtenido leyendo js/service.js y js/config/config.js servidos por
el propio router (192.168.0.1).
"""
import base64
import codecs
import time

import requests


class ZteApiError(Exception):
    pass


class ZteSms:
    def __init__(self, router_ip: str = "192.168.0.1", password: str = "admin", timeout: int = 10):
        self.router_ip = router_ip
        self.password = password
        self.timeout = timeout
        self.session = requests.Session()
        self.base_url = f"http://{router_ip}"
        self.headers = {
            "Referer": f"{self.base_url}/index.html",
            "Origin": self.base_url,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        }
        self._wa_inner_version = None
        self._cr_version = None

    # ---------- bajo nivel ----------

    def _get(self, cmd: str, extra: dict | None = None) -> dict:
        params = {"isTest": "false", "cmd": cmd, "multi_data": "1"}
        if extra:
            params.update(extra)
        r = self.session.get(
            f"{self.base_url}/goform/goform_get_cmd_process",
            params=params,
            headers=self.headers,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def _set(self, goform_id: str, data: dict | None = None) -> dict:
        payload = {"isTest": "false", "goformId": goform_id}
        if data:
            payload.update(data)
        r = self.session.post(
            f"{self.base_url}/goform/goform_set_cmd_process",
            data=payload,
            headers=self.headers,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def _load_versions(self):
        if self._wa_inner_version is None:
            info = self._get("cr_version,wa_inner_version")
            self._wa_inner_version = info.get("wa_inner_version", "")
            self._cr_version = info.get("cr_version", "")

    @staticmethod
    def _encode_ucs2(message: str) -> str:
        return codecs.encode(message.encode("utf-16-be"), "hex").decode("ascii")

    # ---------- alto nivel ----------

    def login(self) -> dict:
        encoded = base64.b64encode(self.password.encode()).decode()
        result = self._set("LOGIN", {"password": encoded})
        if result.get("result") not in ("0", "4"):
            raise ZteApiError(f"Login fallido: {result}")
        return result

    def is_logged_in(self) -> bool:
        info = self._get("loginfo")
        return info.get("loginfo") == "ok"

    def send_sms(self, phone_number: str, message: str) -> dict:
        if not self.is_logged_in():
            self.login()

        data = {
            "notCallback": "true",
            "Number": phone_number,
            "sms_time": time.strftime("%y;%m;%d;%H;%M;%S;+0"),
            "MessageBody": self._encode_ucs2(message),
            "ID": "-1",
            "encode_type": "UNICODE",
        }
        result = self._set("SEND_SMS", data)
        if result.get("result") not in ("success", "0"):
            raise ZteApiError(f"Fallo al enviar SMS: {result}")
        return result

    def logout(self):
        try:
            self._set("LOGOUT")
        except Exception:
            pass
