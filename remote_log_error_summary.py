#!/usr/bin/env python3
"""
remote_log_error_summary.py

Se conecta por SSH a uno o varios servidores definidos en un archivo YAML,
lee las últimas líneas de un archivo de log y genera un resumen de niveles
(ERROR, WARNING, INFO). Muestra el resultado en consola y envía alertas a Slack.
"""

import os
import paramiko
import requests
import yaml
import csv
from datetime import datetime
from dotenv import load_dotenv

OUTPUT_DIR = "archivos"

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
CONFIG_FILE = os.getenv("LOGS_CONFIG_FILE", "logs_monitor.yaml")
TAIL_LINES = int(os.getenv("LOG_TAIL_LINES", "200"))
LOG_TIME_RANGE = os.getenv("LOG_TIME_RANGE", "").strip()  # "", "1h", "24h"

def save_errors_to_csv(host: str, log_content: str):
    """Guarda solo las líneas con ERROR en un archivo CSV dentro de OUTPUT_DIR."""

    if not log_content:
        return

    # Asegura que el directorio exista
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    rows = []
    for line in log_content.splitlines():
        if "ERROR" in line.upper():
            rows.append([datetime.now().isoformat(), line.strip()])

    if not rows:
        return

    filename = f"error_logs_{host.replace('.', '_')}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        file_exists = os.path.isfile(filepath)

        with open(filepath, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            if not file_exists:
                writer.writerow(["timestamp", "message"])

            writer.writerows(rows)

        print(f"[OK] {len(rows)} errores guardados en {filepath}")

    except Exception as e:
        print(f"[ERROR] No se pudo guardar el archivo CSV: {e}")



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
    """Lee la lista de servidores y logs desde un archivo YAML."""
    if not os.path.exists(CONFIG_FILE):
        print(f"[ERROR] No se encontró archivo de configuración: {CONFIG_FILE}")
        return []

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    servers = data.get("servers", [])
    if not servers:
        print("[WARNING] No se encontraron servidores en el YAML.")
    return servers


def fetch_log_tail(host: str, user: str, password: str, log_path: str, port: int = 22) -> str:
    """
    Se conecta por SSH y obtiene el contenido del log remoto.
    Si LOG_TIME_RANGE está definido (por ejemplo '1h' o '24h'), intenta usar journalctl
    para filtrar por rango de tiempo. En caso contrario, usa `tail -n` sobre el archivo.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"[INFO] Conectando a {user}@{host}:{port} ...")
        client.connect(
            hostname=host,
            port=port,
            username=user,
            password=password,
            timeout=10,
        )

        # Elegir comando según rango de tiempo
        if LOG_TIME_RANGE == "1h":
            print("[INFO] Analizando logs de la última hora usando journalctl.")
            cmd = "journalctl --since '1 hour ago'"
        elif LOG_TIME_RANGE == "24h":
            print("[INFO] Analizando logs del último día usando journalctl.")
            cmd = "journalctl --since '1 day ago'"
        else:
            # Comportamiento original: leer últimas N líneas del archivo
            cmd = f"tail -n {TAIL_LINES} {log_path}"

        stdin, stdout, stderr = client.exec_command(cmd)

        output = stdout.read().decode(errors="ignore")
        error_output = stderr.read().decode().strip()

        if error_output:
            print(f"[WARNING] Error al leer log en {host}: {error_output}")

        return output

    except Exception as e:
        print(f"[ERROR] Fallo al conectar o ejecutar comando en {host}: {e}")
        return ""
    finally:
        client.close()

def summarize_log_content(log_content: str) -> dict[str, int]:
    """
    Cuenta ocurrencias de niveles típicos en el contenido del log.
    Se basa en coincidencias de texto simples.
    """
    summary = {
        "ERROR": 0,
        "WARNING": 0,
        "INFO": 0,
        "TOTAL_LINES": 0,
    }

    if not log_content:
        return summary

    for line in log_content.splitlines():
        line_upper = line.upper()
        summary["TOTAL_LINES"] += 1

        if "ERROR" in line_upper:
            summary["ERROR"] += 1
        elif "WARNING" in line_upper or "WARN" in line_upper:
            summary["WARNING"] += 1
        elif "INFO" in line_upper:
            summary["INFO"] += 1

    return summary


def build_console_report(server_name: str, host: str, log_label: str, log_path: str, summary: dict[str, int]) -> str:
    """Construye un reporte legible para consola, usando colores según severidad."""
    RED = "\033[31m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    RESET = "\033[0m"

    header = f"{CYAN}===== Resumen de log remoto: {server_name} ({host}) ====={RESET}"
    log_info = f"Log: {log_label} ({log_path})"
    lines_count = f"Líneas analizadas: {summary['TOTAL_LINES']}"

    error_line = f"{RED}ERROR:   {summary['ERROR']}{RESET}"
    warning_line = f"{YELLOW}WARNING: {summary['WARNING']}{RESET}"
    info_line = f"{GREEN}INFO:    {summary['INFO']}{RESET}"

    report = [
        header,
        log_info,
        lines_count,
        error_line,
        warning_line,
        info_line,
    ]
    return "\n".join(report)



def build_slack_message(server_name: str, host: str, log_label: str, log_path: str, summary: dict[str, int]) -> str:
    """Construye un mensaje corporativo para Slack."""
    header = "🧾 *Resumen de log remoto*"
    host_info = f"📍 Servidor: `{host}` ({server_name})"
    log_info = f"📄 Log: `{log_label}` (`{log_path}`)"

    counts = (
        f"- *Líneas analizadas*: {summary['TOTAL_LINES']}\n"
        f"- *ERROR*: {summary['ERROR']}\n"
        f"- *WARNING*: {summary['WARNING']}\n"
        f"- *INFO*: {summary['INFO']}"
    )

    return f"{header}\n{host_info}\n{log_info}\n\n{counts}"


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
        log_path = server.get("log_path")
        log_label = server.get("log_label", "log")

        if not host or not user or not password or not log_path:
            print(f"[WARNING] Servidor '{name}' tiene configuración incompleta, se omite.")
            continue

        log_content = fetch_log_tail(host, user, password, log_path, port)

        summary = summarize_log_content(log_content)
        save_errors_to_csv(host, log_content)

        # Consola
        report = build_console_report(name, host, log_label, log_path, summary)
        print(report)

        # Slack: solo si hay errores o warnings
        if summary["ERROR"] > 0 or summary["WARNING"] > 0:
            slack_msg = build_slack_message(name, host, log_label, log_path, summary)
            send_slack_message(slack_msg)
        else:
            print("Sin errores ni warnings en el tramo analizado. ✅")


if __name__ == "__main__":
    main()
