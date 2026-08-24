"""
Script de diagnóstico: prueba paso a paso la conexión con el router ZTE MF920V
y muestra las respuestas crudas del dispositivo, para poder ajustar el
protocolo si tu firmware se comporta distinto al esperado.

Uso:
    python diagnostico.py <numero_destino> [password]

Ejemplo:
    python diagnostico.py +51987654321 admin
"""
import sys

from zte_sms import ZteSms


def main():
    if len(sys.argv) < 2:
        print("Uso: python diagnostico.py <numero_destino> [password] [ip]")
        sys.exit(1)

    numero = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else "admin"
    ip = sys.argv[3] if len(sys.argv) > 3 else "192.168.0.1"

    zte = ZteSms(router_ip=ip, password=password)

    print(f"1) Conectando a {zte.base_url} ...")
    try:
        zte._load_versions()
        print(f"   wa_inner_version={zte._wa_inner_version!r} cr_version={zte._cr_version!r}")
    except Exception as e:
        print(f"   ERROR al obtener versiones: {e}")
        print("   -> Revisa que el router esté conectado (USB o WiFi) y la IP sea correcta.")
        sys.exit(1)

    print("2) Consultando estado de login (loginfo) ...")
    try:
        print(f"   is_logged_in() = {zte.is_logged_in()}")
    except Exception as e:
        print(f"   ERROR: {e}")

    print("3) Intentando login ...")
    try:
        result = zte.login()
        print(f"   Respuesta LOGIN: {result}")
        print(f"   is_logged_in() tras login = {zte.is_logged_in()}")
    except Exception as e:
        print(f"   ERROR en login: {e}")
        print("   -> Si el error menciona password/pwd, prueba con la password real")
        print("      de acceso web (la de 192.168.0.1, usuario admin).")
        sys.exit(1)

    print(f"4) Enviando SMS de prueba a {numero} ...")
    try:
        result = zte.send_sms(numero, "Prueba API ZTE MF920V")
        print(f"   Respuesta SEND_SMS: {result}")
        print("   OK - revisa si llegó el SMS al celular destino.")
    except Exception as e:
        print(f"   ERROR al enviar SMS: {e}")
        sys.exit(1)

    zte.logout()
    print("Listo.")


if __name__ == "__main__":
    main()
