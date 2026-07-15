import os
from dotenv import load_dotenv

load_dotenv()

# ==========================
# RUTAS DEL PROYECTO
# ==========================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "upload")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EXCEL_NAME = "productos.xlsx"

EXCEL_PATH = os.path.join(UPLOAD_FOLDER, EXCEL_NAME)

PRODUCT_IMAGE_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "img",
    "productos"
)

os.makedirs(
    PRODUCT_IMAGE_FOLDER,
    exist_ok=True
)


# ==========================
# CONFIGURACIÓN
# ==========================

class Config:

    SECRET_KEY = os.getenv("SECRET_KEY", "chiquilina")

    WPP_URL = os.getenv(
        "WPP_URL",
        "http://localhost:21465"
    )

    WPP_SESSION = os.getenv(
        "WPP_SESSION",
        "pedidos"
    )

    WPP_TOKEN = os.getenv(
        "WPP_TOKEN",
        ""
    )