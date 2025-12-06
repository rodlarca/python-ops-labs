#!/usr/bin/env python3
"""
remote_storage_health.py

Se conecta a un servidor Linux remoto vía SSH, verifica el uso de disco
en los sistemas de archivos y envía una notificación a Slack si alguno
supera el 80% de uso.
"""

import os
import paramiko
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = os.getenv("STORAGE_CONFIG_FILE", "servers_storage.yaml")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
THRESHOLD = float(os.getenv("STORAGE_THRESHOLD", "80"))


def send_slack_alert(message: str):
    if not SLACK_WEBHOOK_URL:
        print("[ERROR] SLACK_WEBHOOK_URL no está configurado.")
        return

    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=5)
        print("[OK] Alerta enviada a Slack")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar alerta Slack: {e}")


def get_remote_storage_status(host: str, user: str, password: str, port: int = 22):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"[INFO] Conectando a {user}@{host}:{port}")
        client.connect(
            hostname=host,
            port=port,
            username=user,
            password=password,
            timeout=10,
        )

        stdin, stdout, stderr = client.exec_command("df -h --output=source,pcent,target")
        output = stdout.read().decode().strip()
        client.close()
    except Exception as e:
        print(f"[ERROR] Fallo al conectar o ejecutar comando en {host}: {e}")
        return []

    lines = output.splitlines()[1:]
    filesystems = []

    for line in lines:
        parts = line.split()
        if len(parts) == 3:
            fs, used, mount = parts
            used_percent = float(used.replace('%', ''))
            filesystems.append((fs, used_percent, mount))

    return filesystems

def load_servers_from_yaml():
    if not os.path.exists(CONFIG_FILE):
        print(f"[ERROR] No se encontró archivo de configuración: {CONFIG_FILE}")
        return []

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data.get("servers", [])

def main():
    servers = load_servers_from_yaml()

    if not servers:
        print("No hay servidores definidos en el archivo YAML.")
        return

    for server in servers:
        name = server.get("name", "Servidor sin nombre")
        host = server.get("host")
        user = server.get("user")
        password = server.get("password")
        port = int(server.get("port", 22))
        threshold = float(server.get("threshold", THRESHOLD))

        if not host or not user or not password:
            print(f"[WARNING] Servidor '{name}' tiene configuración incompleta, se omite.")
            continue

        print(f"\n===== Revisando storage en: {name} ({host}) =====")
        filesystems = get_remote_storage_status(host, user, password, port)

        if not filesystems:
            print(f"No se pudo obtener información de almacenamiento para {name}.")
            continue

        critical = []
        normal = []

        for fs, used, mount in filesystems:
            if any(excluded in fs for excluded in ["tmpfs", "udev", "overlay"]):
                continue

            entry = f"{mount}: {used}%"

            if used > threshold:
                critical.append(entry)
            else:
                normal.append(entry)

        host_info = f"📍 Servidor: `{host}` ({name})"
        header = "📦 *Estado de Storage*"

        details = "\n".join(
            [f"🔴 {e}" for e in critical] +
            [f"🟢 {e}" for e in normal]
        )

        message = f"{header}\n{host_info}\n\n{details}"
        print(message)

        if critical:
            send_slack_alert(
                f"⚠️ *Alerta de almacenamiento crítico*\n{host_info}\n\n" +
                "\n".join(f"🔴 {e}" for e in critical)
            )
        else:
            print("Sin alertas para este servidor. Todo OK 👍")


if __name__ == "__main__":
    main()
