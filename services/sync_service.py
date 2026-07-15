import os
from services.excel_service import leer_excel
from services.database_service import conectar
from services.sync_log_service import guardar_log
import time
from datetime import datetime

# Carpeta donde estarán las imágenes
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CARPETA_IMAGENES = os.path.join(
    BASE_DIR,
    "static",
    "img",
    "productos"
)

# Extensiones permitidas
EXTENSIONES = [".jpg", ".jpeg", ".png", ".webp"]


def obtener_imagen_producto(codigo):
    """
    Busca automáticamente la imagen del producto
    según su código.
    """

    codigo = str(codigo).strip()

    for extension in EXTENSIONES:

        nombre_archivo = codigo + extension

        ruta = os.path.join(
            CARPETA_IMAGENES,
            nombre_archivo
        )
        #print("Buscando:", ruta)
        #print("Existe:", os.path.exists(ruta))
        if os.path.exists(ruta):
            return nombre_archivo

    return "SIN_IMAGEN.jpg"

def sincronizar_productos():
    inicio = time.perf_counter()
    df = leer_excel()
    conn = conectar()
    cursor = conn.cursor()

    productos_leidos = 0
    nuevos = 0
    actualizados = 0
    sin_cambios = 0
    errores = 0

    codigos_excel = set()
    desactivados = 0

    for _, row in df.iterrows():
        productos_leidos += 1
        codigo = str(row["codigo"]).strip()
        imagen = obtener_imagen_producto(codigo)
        print(f"{codigo} -> {imagen}")
        codigos_excel.add(codigo)
        cursor.execute("""
            SELECT
                producto,
                marca,
                tipo,
                presentacion,
                stock,
                precio,
                imagen
            FROM productos
            WHERE codigo = ?
        """, (codigo,))

        resultado = cursor.fetchone()

        # 🚀 CASO 1: NO EXISTE → INSERTAR
        if not resultado:
            cursor.execute("""
                INSERT INTO productos
                (codigo, producto, marca, tipo, presentacion, stock, precio, imagen, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                codigo,
                row["producto"],
                row["marca"],
                row["tipo"],
                row["presentacion"],
                int(row["stock"]),
                float(row["precio"]),
                imagen
            ))
            nuevos += 1

        # 🔄 CASO 2: EXISTE → ACTUALIZAR
        else:

            if (
                resultado["producto"] == row["producto"] and
                resultado["marca"] == row["marca"] and
                resultado["tipo"] == row["tipo"] and
                resultado["presentacion"] == row["presentacion"] and
                resultado["stock"] == int(row["stock"]) and
                resultado["precio"] == float(row["precio"])
            ):
                sin_cambios += 1

            else:

                cursor.execute("""
                    UPDATE productos
                    SET
                        producto = ?,
                        marca = ?,
                        tipo = ?,
                        presentacion = ?,
                        stock = ?,
                        precio = ?,
                        activo = 1
                    WHERE codigo = ?
                """, (
                    row["producto"],
                    row["marca"],
                    row["tipo"],
                    row["presentacion"],
                    int(row["stock"]),
                    float(row["precio"]),
                    codigo

                ))

                actualizados += 1

    # ==========================================
    # DESACTIVAR PRODUCTOS QUE YA NO EXISTEN
    # ==========================================

    cursor.execute("""
        SELECT codigo
        FROM productos
        WHERE activo = 1
    """)

    for row in cursor.fetchall():

        codigo_db = row["codigo"]

        if codigo_db not in codigos_excel:

            cursor.execute("""
                UPDATE productos
                SET activo = 0
                WHERE codigo = ?
            """, (codigo_db,))

            desactivados += 1

    conn.commit()

    duracion = round(time.perf_counter() - inicio, 3)
    guardar_log(

        productos_leidos,
        nuevos,
        actualizados,
        sin_cambios,
        desactivados,
        errores,
        duracion,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    )

    conn.close()

    resultado = {
        "productos_leidos": productos_leidos,
        "nuevos": nuevos,
        "actualizados": actualizados,
        "sin_cambios": sin_cambios,
        "desactivados": desactivados,
        "errores": errores,
        "duracion": duracion
    }

    return resultado


    