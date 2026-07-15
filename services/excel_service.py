import pandas as pd
import os
from config import EXCEL_PATH

def leer_excel():

    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError("No existe el Excel subido aún")

    df = pd.read_excel(
        EXCEL_PATH,
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