#!/usr/bin/env python3
"""
System Metrics One Shot

Obtiene el uso de CPU, RAM y disco,
lo muestra por consola y lo envía a Slack una sola vez.
"""

import os
import psutil
import requests
from dotenv import load_dotenv

load_dotenv()


SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def get_system_metrics():
    """Obtiene métricas básicas de CPU, RAM y disco."""
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent

    # Raíz del sistema (funciona en Windows y Linux)
    root_path = os.path.abspath(os.sep)
    disk = psutil.disk_usage(root_path).percent

    return cpu, mem, disk


def send_slack_message(message: str):
    """Envía un mensaje a Slack usando un webhook."""
    if not SLACK_WEBHOOK_URL:
        print("[ERROR] SLACK_WEBHOOK_URL no está configurado.")
        return

    payload = {"text": message}

    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            print("[OK] Mensaje enviado a Slack.")
        else:
            print(f"[ERROR] Slack respondió con status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar mensaje a Slack: {e}")


def main():
    cpu, mem, disk = get_system_metrics()

    message = f"CPU: {cpu:.1f}% | RAM: {mem:.1f}% | Disco: {disk:.1f}%"
    print(message)

    send_slack_message(message)


if __name__ == "__main__":
    main()
