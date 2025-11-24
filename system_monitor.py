import psutil
import json
import os
import requests
from datetime import datetime, UTC
from dotenv import load_dotenv

# ================================
# CARGAR VARIABLES DEL ENTORNO
# ================================
load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


# ================================
# OBTENER MÉTRICAS DEL SISTEMA
# ================================
def get_metrics():
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "load_avg": psutil.getloadavg() if hasattr(psutil, "getloadavg") else "N/A",
        "net": {
            "bytes_sent": psutil.net_io_counters().bytes_sent,
            "bytes_recv": psutil.net_io_counters().bytes_recv,
        }
    }


# ================================
# ENVIAR ALERTA A SLACK
# ================================
def send_slack_alert(metrics):
    if not SLACK_WEBHOOK_URL:
        print("SLACK_WEBHOOK_URL no configurado en .env")
        return

    message = (
        "*⚠️ ALERTA DE SISTEMA*\n\n"
        f"*CPU:* {metrics['cpu_percent']}%\n"
        f"*RAM:* {metrics['memory_percent']}%\n"
        f"*Disco:* {metrics['disk_percent']}%\n"
        f"*Load Avg:* {metrics['load_avg']}\n"
        "\nRevisa el servidor, los valores superan los umbrales definidos."
    )

    payload = {"text": message}

    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
        print("Alerta enviada a Slack.")
    except Exception as e:
        print(f"Error enviando alerta a Slack: {e}")


# ================================
# LÓGICA PRINCIPAL
# ================================
def main():
    metrics = get_metrics()

    # Imprimir métricas como JSON
    print(json.dumps(metrics, indent=2))

    # Evaluar si se debe enviar alerta
    alert_triggered = (
        metrics["cpu_percent"] > 85 or
        metrics["memory_percent"] > 90 or
        metrics["disk_percent"] > 85
    )

    if alert_triggered:
        send_slack_alert(metrics)


# ================================
# PUNTO DE ENTRADA
# ================================
if __name__ == "__main__":
    main()
