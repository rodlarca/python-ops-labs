#!/usr/bin/env python3
"""
System Metrics Exporter + Slack Alerts

Expone métricas y envía alertas a Slack si se superan umbrales críticos.
"""

import os
import time
import psutil
import requests
from prometheus_client import Gauge, start_http_server

# Configuración por variables de entorno o valores por defecto
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", 85))
MEM_THRESHOLD = float(os.getenv("MEM_THRESHOLD", 90))

# Flags para evitar spam
cpu_alert_sent = False
mem_alert_sent = False

# Definición de métricas
CPU_USAGE = Gauge("system_cpu_usage_percent", "CPU usage percentage")
MEM_USAGE = Gauge("system_memory_usage_percent", "Memory usage percentage")
DISK_USAGE = Gauge("system_disk_usage_percent", "Disk usage percentage")
NET_SENT = Gauge("system_network_sent_bytes", "Network bytes sent")
NET_RECV = Gauge("system_network_received_bytes", "Network bytes received")

def send_slack_alert(message: str):
    """ Envía una alerta a Slack si hay Webhook configurado """
    if not SLACK_WEBHOOK_URL:
        print("[WARNING] No se encontró SLACK_WEBHOOK_URL")
        return

    payload = {"text": message}
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        print(f"[ALERTA ENVIADA] {message}")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar alerta a Slack: {e}")

def collect_metrics():
    global cpu_alert_sent, mem_alert_sent

    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    net = psutil.net_io_counters()

    CPU_USAGE.set(cpu)
    MEM_USAGE.set(mem)
    DISK_USAGE.set(disk)
    NET_SENT.set(net.bytes_sent)
    NET_RECV.set(net.bytes_recv)

    print(f"CPU: {cpu:.1f}% | RAM: {mem:.1f}% | Disco: {disk:.1f}%")

    # Alertas
    if cpu > CPU_THRESHOLD and not cpu_alert_sent:
        send_slack_alert(f"⚠️ ALERTA CPU: {cpu:.1f}% (umbral: {CPU_THRESHOLD}%)")
        cpu_alert_sent = True
    elif cpu <= CPU_THRESHOLD:
        cpu_alert_sent = False

    if mem > MEM_THRESHOLD and not mem_alert_sent:
        send_slack_alert(f"🚨 ALERTA RAM: {mem:.1f}% (umbral: {MEM_THRESHOLD}%)")
        mem_alert_sent = True
    elif mem <= MEM_THRESHOLD:
        mem_alert_sent = False

def main():
    print("🚀 Exportador corriendo en http://localhost:8000/metrics")
    print(f"🔔 Alertas Slack activas | CPU>{CPU_THRESHOLD}% RAM>{MEM_THRESHOLD}%")
    start_http_server(8000)

    while True:
        collect_metrics()
        time.sleep(2)

if __name__ == "__main__":
    main()
