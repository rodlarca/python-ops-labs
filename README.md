# Lab Scripts Python

Este repositorio contiene scripts de prueba para distintos servicios.

## Scripts

| Script | Descripción |
|--------|-------------|
| [slack_send_message.py](slack_send_message.py) | Envía un mensaje a un canal Slack mediante Webhook.|
| [openai_cost_estimator.py](openai_cost_estimator.py) | Este script ejecuta una llamada a la API de OpenAI y calcula el costo estimado de la consulta en base al uso de tokens.|
| [sftp_last_file.py](sftp_last_file.py) | Se conecta a un servidor SFTP usando variables de entorno y muestra en una sola línea el archivo más reciente, su fecha de modificación y la fecha del servidor donde se ejecuta el script.|
| [system_monitor.py](system_monitor.py) | Obtiene métricas del sistema (CPU, RAM, disco, red) y envía alertas a Slack si se superan umbrales.|
| [generate_fake_logs.py](generate_fake_logs.py) | Genera un archivo `app.log` con líneas sintéticas de INFO, WARNING y ERROR para pruebas de análisis. |
| [log_error_summary.py](log_error_summary.py) | Lee `app.log`, cuenta niveles (ERROR, WARNING, INFO) y genera un resumen en consola y un CSV. |
| [system_metrics_exporter.py](system_metrics_exporter.py) | Obtiene métricas del sistema (CPU, RAM, disco) y envía el resumen a Slack en una sola ejecución. |
| [remote_docker_status.py](remote_docker_status.py) | Se conecta por SSH a un servidor Linux remoto, lista contenedores Docker y envía el estado a Slack. |
| [remote_storage_health.py](remote_storage_health.py) | Monitorea el uso de almacenamiento en servidores remotos vía SSH desde un archivo YAML y envía alertas a Slack si se superan umbrales configurables. |
| [remote_log_error_summary.py](remote_log_error_summary.py) | Se conecta vía SSH a servidores Linux, analiza `/var/log/messages` buscando errores y envía alertas a Slack si hay problemas detectados. |



## Data science

| Script | Descripción |
|--------|-------------|
| [pandas_scikit.py](data_science/pandas_scikit.py) | Pipeline Pandas + Scikit-learn: imputación, ColumnTransformer, RandomForest y métricas MAE/MSE/R². [Artículo original en KDnuggets](https://www.kdnuggets.com/from-dataset-to-dataframe-to-deployed-your-first-project-with-pandas-scikit-learn)|
| [data_analysis_with_polars.py](data_science/data_analysis_with_polars.py) | Análisis con Polars: generación de dataset sintético, agregaciones, métricas de ventas, ranking de productos y resumen de negocio. [Artículo original en KDnuggets](https://www.kdnuggets.com/beginners-guide-to-data-analysis-with-polars)|


![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Status](https://img.shields.io/badge/status-active-success)