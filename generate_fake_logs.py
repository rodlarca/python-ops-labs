#!/usr/bin/env python3
"""
generate_fake_logs.py

Genera un archivo app.log con líneas sintéticas de logs
para pruebas de análisis.
"""

import random
import datetime

LEVELS = ["INFO", "WARNING", "ERROR"]

MESSAGES = {
    "INFO": [
        "Usuario autenticado correctamente",
        "Petición procesada",
        "Conexión establecida",
    ],
    "WARNING": [
        "Latencia elevada detectada",
        "Reintento de conexión",
        "Uso de memoria sobre el 70%",
    ],
    "ERROR": [
        "No se pudo conectar al servidor",
        "Tiempo de espera agotado",
        "Fallo en lectura de archivo",
    ],
}

def generate_line():
    level = random.choice(LEVELS)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = random.choice(MESSAGES[level])
    return f"{timestamp} [{level}] {message}"

def main():
    with open("app.log", "w", encoding="utf-8") as f:
        for _ in range(200):  # 200 líneas para tener variedad
            f.write(generate_line() + "\n")

    print("Archivo app.log generado con logs sintéticos.")

if __name__ == "__main__":
    main()
