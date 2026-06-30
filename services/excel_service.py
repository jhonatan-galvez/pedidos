import pandas as pd
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_DIR = os.path.join(BASE_DIR, "upload")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ARCHIVO = os.path.join(UPLOAD_DIR, "productos.xlsx")

def leer_excel():

    if not os.path.exists(ARCHIVO):
        raise FileNotFoundError("No existe el Excel subido aún")

    df = pd.read_excel(
        ARCHIVO,
        header=None,
        skiprows=4,
        dtype={1: str}      # La columna Código se lee como texto
    )

    df = df.iloc[:, 1:8]

    df.columns = [
        "codigo",
        "producto",
        "marca",
        "tipo",
        "presentacion",
        "stock",
        "precio"
    ]

    df["producto"] = df["producto"].ffill()     # Rellenar productos de celdas combinadas

    # fillna("") -> convierte celda vacia en "" || astype(str) -> convierte a texto || strip() -> elimina espacios 
    df["codigo"] = df["codigo"].fillna("").astype(str).str.strip()
    df["producto"] = df["producto"].fillna("").astype(str)
    df["marca"] = df["marca"].fillna("").astype(str)
    df["tipo"] = df["tipo"].fillna("").astype(str)
    df["presentacion"] = df["presentacion"].fillna("").astype(str)
    df["stock"] = df["stock"].fillna(0).astype(int)
    df["precio"] = df["precio"].fillna(0).astype(float)

    return df


if __name__ == "__main__":      # El código se ejecutará solo si se ejecuta directamente
    df = leer_excel()
    print(df.head())