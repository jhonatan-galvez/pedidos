import os

UPLOAD_FOLDER = "uploads"
ARCHIVO_BASE = "productos.xlsx"

def guardar_excel(archivo):

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    ruta = os.path.join(UPLOAD_FOLDER, ARCHIVO_BASE)

    archivo.save(ruta)

    return ruta