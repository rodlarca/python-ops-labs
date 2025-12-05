#!/usr/bin/env python3
"""
remote_docker_status.py

Se conecta por SSH a un servidor Linux remoto,
ejecuta `docker ps` y muestra el estado de los contenedores.
Opcionalmente envía el resumen a Slack.
"""

import os
import paramiko
import requests
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

SSH_MARCHIGUE_HOST = os.getenv("SSH_MARCHIGUE_HOST")
SSH_MARCHIGUE_USER = os.getenv("SSH_MARCHIGUE_USER")
SSH_MARCHIGUE_PASSWORD = os.getenv("SSH_MARCHIGUE_PASSWORD")
SSH_MARCHIGUE_PORT = int(os.getenv("SSH_MARCHIGUE_PORT", "22"))

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_message(message: str) -> None:
    """Envía un mensaje a Slack usando un Webhook."""
    if not SLACK_WEBHOOK_URL:
        print("[WARNING] SLACK_WEBHOOK_URL no está configurado, no se enviará a Slack.")
        return

    payload = {"text": message}

    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            print("[OK] Resumen enviado a Slack.")
        else:
            print(f"[ERROR] Slack respondió con status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar mensaje a Slack: {e}")


def get_remote_docker_status():
    """Se conecta por SSH y ejecuta `docker ps` en el servidor remoto."""
    if not SSH_MARCHIGUE_HOST or not SSH_MARCHIGUE_USER or not SSH_MARCHIGUE_PASSWORD:
        print("[ERROR] Faltan SSH_HOST, SSH_USER o SSH_PASSWORD en las variables de entorno.")
        return []

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"[INFO] Conectando a {SSH_MARCHIGUE_USER}@{SSH_MARCHIGUE_HOST}:{SSH_MARCHIGUE_PORT} ...")
        client.connect(
            hostname=SSH_MARCHIGUE_HOST,
            port=SSH_MARCHIGUE_PORT,
            username=SSH_MARCHIGUE_USER,
            password=SSH_MARCHIGUE_PASSWORD,
            timeout=10,
        )

        cmd = 'docker ps --format "{{.Names}}|{{.Status}}|{{.Image}}"'
        stdin, stdout, stderr = client.exec_command(cmd)

        output = stdout.read().decode().strip()
        error_output = stderr.read().decode().strip()
    except Exception as e:
        print(f"[ERROR] No se pudo conectar o ejecutar el comando: {e}")
        return []
    finally:
        client.close()

    if error_output:
        print(f"[ERROR] Error desde docker ps: {error_output}")
        return []

    containers = []
    if output:
        for line in output.splitlines():
            parts = line.split("|")
            if len(parts) == 3:
                name, status, image = parts
                containers.append(
                    {"name": name.strip(), "status": status.strip(), "image": image.strip()}
                )

    return containers


def main():
    containers = get_remote_docker_status()

    if not containers:
        print("No se encontraron contenedores o hubo un error.")
        return

    print("\nContenedores en el servidor remoto:")
    for c in containers:
        print(f"- {c['name']} | {c['status']} | {c['image']}")

    # Crear mensaje para Slack
    lines = [f"Estado de Docker en {SSH_MARCHIGUE_HOST}:"]
    for c in containers:
        lines.append(f"- {c['name']}: {c['status']} ({c['image']})")

    message = "\n".join(lines)
    send_slack_message(message)


if __name__ == "__main__":
    main()
