import subprocess
import re
import os

UBI_CLOUDFLARE = r"C:\Cloudflared"
CARPETA = r"D:\Servidor"
ARCHIVO_LINK = os.path.join(CARPETA, "LINK_donaflori.txt")

proceso = subprocess.Popen(
    [
        os.path.join(UBI_CLOUDFLARE, "cloudflared.exe"),
        "tunnel",
        "--url",
        "http://localhost:5000"
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

for linea in proceso.stdout:
    print(linea)

    resultado = re.search(
        r"https://[a-zA-Z0-9-]+\.trycloudflare\.com",
        linea
    )

    if resultado:
        url = resultado.group(0)

        with open(ARCHIVO_LINK, "w", encoding="utf-8") as f:
            f.write(url)

        print("URL guardada:", url)