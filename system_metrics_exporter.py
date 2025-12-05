#!/usr/bin/env python3
"""
System Metrics Exporter

Expone métricas de CPU, memoria, disco y red para Prometheus.
"""

import time
import psutil
from prometheus_client import Gauge, start_http_server

# Definición de métricas
CPU_USAGE = Gauge("system_cpu_usage_percent", "CPU usage percentage")
MEM_USAGE = Gauge("system_memory_usage_percent", "Memory usage percentage")
DISK_USAGE = Gauge("system_disk_usage_percent", "Disk usage percentage")
NET_SENT = Gauge("system_network_sent_bytes", "Network bytes sent")
NET_RECV = Gauge("system_network_received_bytes", "Network bytes received")

def collect_metrics():
    """Recoge métricas del sistema y actualiza los gauges."""
    CPU_USAGE.set(psutil.cpu_percent(interval=1))
    MEM_USAGE.set(psutil.virtual_memory().percent)
    DISK_USAGE.set(psutil.disk_usage("/").percent)

    net = psutil.net_io_counters()
    NET_SENT.set(net.bytes_sent)
    NET_RECV.set(net.bytes_recv)

def main():
    print("🚀 Exportador de métricas iniciado en http://localhost:8000/metrics")
    start_http_server(8000)

    while True:
        collect_metrics()
        time.sleep(2)

if __name__ == "__main__":
    main()
