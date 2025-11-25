import os
from datetime import datetime
import paramiko
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("CG_HOST")
port = int(os.getenv("CG_PORT"))
username = os.getenv("CG_USER")
password = os.getenv("CG_PASS")

def show_last_file():
    """
    Se conecta al SFTP, obtiene el archivo más reciente y lo muestra.
    Además envía esa línea a Slack.
    Si ocurre cualquier error -> manda alerta a Slack.
    """
    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password)

        sftp = paramiko.SFTPClient.from_transport(transport)

        files = sftp.listdir_attr(".")

        if not files:
            msg = ":warning: *ALERTA VTR Guía:* No hay archivos en el SFTP."
            print(msg)
            raise ValueError("No hay archivos en el SFTP.")

        # Archivo más reciente
        last_file = sorted(files, key=lambda f: f.st_mtime, reverse=True)[0]

        file_date = datetime.fromtimestamp(last_file.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        server_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Línea exacta que quieres enviar
        line = f"{last_file.filename} | file_date={file_date} | server_date={server_date}"

        print(line)

        # Cerrar conexiones
        sftp.close()
        transport.close()

    except Exception as e:
        msg = f":rotating_light: *ERROR VTR Guía:* Falló la conexión o ejecución del DAG.\nError: `{str(e)}`"
        print(msg)
        raise  # obliga a que el task quede en estado FAILED

show_last_file()