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
from dotenv import load_dotenv

load_dotenv()

SSH_HOST = os.getenv("SSH_MARCHIGUE_HOST")
SSH_USER = os.getenv("SSH_MARCHIGUE_USER")
SSH_PASSWORD = os.getenv("SSH_MARCHIGUE_PASSWORD")
SSH_PORT = int(os.getenv("SSH_MARCHIGUE_PORT", "22"))

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


def get_remote_storage_status():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"[INFO] Conectando a {SSH_USER}@{SSH_HOST}:{SSH_PORT}")
        client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USER,
            password=SSH_PASSWORD,
            timeout=10,
        )

        stdin, stdout, stderr = client.exec_command("df -h --output=source,pcent,target")
        output = stdout.read().decode().strip()
        client.close()
    except Exception as e:
        print(f"[ERROR] Fallo al conectar o ejecutar comando: {e}")
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


def main():
    filesystems = get_remote_storage_status()

    if not filesystems:
        print("No se pudo obtener información del almacenamiento.")
        return

    critical = []
    normal = []

    for fs, used, mount in filesystems:
        if any(excluded in fs for excluded in ["tmpfs", "udev", "overlay"]):
            continue  # Saltar sistemas temporales o virtuales

        entry = f"{mount}: {used}%"

        if used > THRESHOLD:
            critical.append(entry)
        else:
            normal.append(entry)

    # Construcción del mensaje corporativo
    host_info = f"📍 Servidor: `{SSH_HOST}`"
    header = "📦 *Estado de Storage*"
    
    details = "\n".join(
        [f"🔴 {e}" for e in critical] + 
        [f"🟢 {e}" for e in normal]
    )

    message = f"{header}\n{host_info}\n\n{details}"

    print(message)

    # Alertar solo si hay problemas
    if critical:
        send_slack_alert(
            f"⚠️ *Alerta de almacenamiento crítico*\n{host_info}\n\n" +
            "\n".join(f"🔴 {e}" for e in critical)
        )
    else:
        print("Sin alertas. Todo OK 👍")

if __name__ == "__main__":
    main()
