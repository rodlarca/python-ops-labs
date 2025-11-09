import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

payload = {
    "text": "*ALERTA:* prueba automática desde Python",
}

resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
resp.raise_for_status()
print("Enviado a Slack:", resp.status_code)