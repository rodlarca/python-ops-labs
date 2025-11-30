#!/usr/bin/env python3
"""
log_error_summary.py

Lee un archivo llamado app.log, cuenta ocurrencias de niveles
(ERROR, WARNING, INFO) y genera un archivo CSV con el resumen.
"""

import csv
import os
from collections import Counter


LOG_FILE = "app.log"            # <-- nombre fijo del log
OUTPUT_FILE = "log_summary.csv" # <-- nombre fijo del output


def analyze_log_file(log_path: str) -> Counter:
    if not os.path.exists(log_path):
        print(f"[ERROR] El archivo {log_path} no existe.")
        return Counter()

    if os.stat(log_path).st_size == 0:
        print(f"[WARNING] El archivo {log_path} está vacío.")
        return Counter()

    levels = Counter({"ERROR": 0, "WARNING": 0, "INFO": 0})

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            upper_line = line.upper()
            if "ERROR" in upper_line:
                levels["ERROR"] += 1
            if "WARNING" in upper_line or "WARN" in upper_line:
                levels["WARNING"] += 1
            if "INFO" in upper_line:
                levels["INFO"] += 1

    if all(count == 0 for count in levels.values()):
        print("[INFO] No se detectaron registros de ERROR, WARNING ni INFO.")

    return levels


def save_to_csv(counts: Counter, output_path: str) -> None:
    """
    Guarda el resumen de niveles en un archivo CSV.
    """
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["level", "count"])
        for level, count in counts.items():
            writer.writerow([level, count])

def color(text, level):
    if level == "ERROR":
        return f"\033[91m{text}\033[0m"   # rojo
    if level == "WARNING":
        return f"\033[93m{text}\033[0m"  # amarillo
    if level == "INFO":
        return f"\033[92m{text}\033[0m"  # verde
    return text

def main():
    print(f"[INFO] Analizando archivo de log: {LOG_FILE}")
    counts = analyze_log_file(LOG_FILE)

    print("\n=== Resumen de niveles detectados ===")
    for level, count in counts.items():
        print(color(f"{level}: {count}", level))

    save_to_csv(counts, OUTPUT_FILE)
    print(f"\n[INFO] Resumen guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
