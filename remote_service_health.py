#!/usr/bin/env python3
"""
remote_service_health.py

Verifica el estado de servicios systemd en uno o varios servidores remotos
definidos en un archivo YAML, usando SSH, y envía un resumen/alerta a Slack.
"""

import os
import paramiko
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
CONFIG_FILE = os.getenv("SERVICES_CONFIG_FILE", "servers_storage.yaml")


def send_slack_message(message: str) -> None:
    """Envía un mensaje a Slack usando un Webhook."""
    if not SLACK_WEBHOOK_URL:
        print("[WARNING] SLACK_WEBHOOK_URL no está configurado. No se enviará a Slack.")
        return

    try:
        resp = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": message},
            timeout=5,
        )
        if resp.status_code == 200:
            print("[OK] Resumen enviado a Slack.")
        else:
            print(f"[ERROR] Slack respondió con status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar mensaje a Slack: {e}")


def load_servers_from_yaml():
    """Lee la lista de servidores y servicios desde un archivo YAML."""
    if not os.path.exists(CONFIG_FILE):
        print(f"[ERROR] No se encontró archivo de configuración: {CONFIG_FILE}")
        return []

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    servers = data.get("servers", [])
    if not servers:
        print("[WARNING] No se encontraron servidores en el YAML.")
    return servers


def check_services_status_auto(host: str, user: str, password: str, port: int = 22) -> dict[str, str]:
    """
    Descubre servicios activos (systemctl) y monitorea su estado.
    Filtra servicios irrelevantes o del sistema.
    """

    excluded_prefixes = [
        "systemd", "dbus", "polkit", "NetworkManager", "snapd", "accounts-daemon",
        "cron", "ssh", "haveged", "rngd", "user@", "avahi", "syslog"
    ]

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"[INFO] Conectando a {user}@{host}:{port} ...")
        client.connect(hostname=host, port=port, username=user,
                       password=password, timeout=10)

        # Auto-descubrimiento de servicios activos
        discover_cmd = "systemctl list-units --type=service --state=active"
        stdin, stdout, stderr = client.exec_command(discover_cmd)
        output = stdout.read().decode().strip()

        services = []
        for line in output.splitlines():
            if ".service" not in line:
                continue

            svc = line.split()[0].replace(".service", "")

            # Filtrar servicios irrelevantes del sistema
            if any(svc.startswith(prefix) for prefix in excluded_prefixes):
                continue

            services.append(svc)

        print(f"[INFO] {len(services)} servicios detectados en {host}")

        results = {}

        # Ahora consulta estado uno por uno (si en el futuro queremos saber si falla)
        for svc in services:
            cmd = f"systemctl is-active {svc}"
            stdin, stdout, stderr = client.exec_command(cmd)
            status = stdout.read().decode().strip() or "unknown"
            results[svc] = status

        return results

    except Exception as e:
        print(f"[ERROR] Fallo en {host}: {e}")
        return {}
    finally:
        client.close()



def main():
    servers = load_servers_from_yaml()
    if not servers:
        return

    for server in servers:
        name = server.get("name", "Servidor sin nombre")
        host = server.get("host")
        user = server.get("user")
        password = server.get("password")
        port = int(server.get("port", 22))

        if not host or not user or not password:
            print(f"[WARNING] Servidor '{name}' tiene configuración incompleta, se omite.")
            continue

        print(f"\n===== Revisando servicios en: {name} ({host}) =====")

        status_map = check_services_status_auto(host, user, password, port)

        if not status_map:
            print(f"No se obtuvieron estados de servicios para {name}.")
            continue

        ok_services: list[tuple[str, str]] = []
        bad_services: list[tuple[str, str]] = []

        for service, status in status_map.items():
            if status == "active":
                ok_services.append((service, status))
            else:
                bad_services.append((service, status))

        header = "🖥️ *Estado de servicios remotos*"
        host_info = f"📍 Servidor: `{host}` ({name})"

        lines: list[str] = []

        if bad_services:
            lines.append("\n🔴 *Servicios con problemas:*")
            for svc, st in bad_services:
                lines.append(f"- {svc}: `{st}`")

        if ok_services:
            lines.append("\n🟢 *Servicios OK:*")
            for svc, st in ok_services:
                lines.append(f"- {svc}: `{st}`")

        message = f"{header}\n{host_info}\n" + "\n".join(lines)

        # Consola
        print(message)

        # Slack: solo si hay problemas
        if bad_services:
            alert_msg = (
                f"⚠️ *Alerta de servicios con problemas*\n{host_info}\n" +
                "\n".join(f"- {svc}: `{st}`" for svc, st in bad_services)
            )
            send_slack_message(alert_msg)
        else:
            print("Todos los servicios están activos en este servidor. ✅")



if __name__ == "__main__":
    main()
