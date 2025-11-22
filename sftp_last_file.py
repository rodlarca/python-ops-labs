import os
import paramiko
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

host = os.getenv("VG_HOST")
port = int(os.getenv("VG_PORT"))
username = os.getenv("VG_USER")
password = os.getenv("VG_PASS")

def show_last_file():
    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password)

        sftp = paramiko.SFTPClient.from_transport(transport)

        files = sftp.listdir_attr(".")

        last_file = sorted(files, key=lambda f: f.st_mtime, reverse=True)[0]

        file_date = datetime.fromtimestamp(last_file.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        server_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"{last_file.filename} | file_date={file_date} | server_date={server_date}")

        sftp.close()
        transport.close()

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    show_last_file()