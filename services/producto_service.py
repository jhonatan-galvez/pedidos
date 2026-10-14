import sqlite3
from datetime import datetime
from services.database_service import conectar


def _map_productos(rows):
    return [
        {
            "codigo": r["codigo"],
            "producto": r["producto"],
            "marca": r["marca"],
            "tipo": r["tipo"],
            "presentacion": r["presentacion"],
            "stock": r["stock"],
            "precio": r["precio"],
            "imagen": r["imagen"],
        }
        for r in rows
    ]


def obtener_productos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT codigo, producto, marca, tipo, presentacion, stock, precio, imagen
        FROM productos
        WHERE activo = 1
    """)

    rows = cursor.fetchall()
    conn.close()

    return _map_productos(rows)


def buscar_por_codigo(codigo):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT codigo, producto, marca, tipo, presentacion, stock, precio, imagen
        FROM productos
        WHERE codigo = ? AND activo = 1
    """, (codigo,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def buscar_por_nombre(nombre):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT codigo, producto, marca, tipo, presentacion, stock, precio, imagen
        FROM productos
        WHERE producto LIKE ? AND activo = 1
    """, (f"%{nombre}%",))

    rows = cursor.fetchall()
    conn.close()

    return _map_productos(rows)


def buscar_por_marca(marca):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT codigo, producto, marca, tipo, presentacion, stock, precio, imagen
        FROM productos
        WHERE marca LIKE ? AND activo = 1
    """, (f"%{marca}%",))

    rows = cursor.fetchall()
    conn.close()

    return _map_productos(rows)


def productos_sin_stock():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT codigo, producto, marca, tipo, presentacion, stock, precio, imagen
        FROM productos
        WHERE stock <= 0 AND activo = 1
    """)

    rows = cursor.fetchall()
    conn.close()

    return _map_productos(rows)


def productos_bajo_stock(minimo=5):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT codigo, producto, marca, tipo, presentacion, stock, precio, imagen
        FROM productos
        WHERE stock <= ? AND activo = 1
    """, (minimo,))

    rows = cursor.fetchall()
    conn.close()

    return _map_productos(rows)

def actualizar_imagen_producto(producto_id, nombre_imagen):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE productos
        SET imagen = ?
        WHERE id = ?
    """, (
        nombre_imagen,
        producto_id
    ))

    conn.commit()
    conn.close()    

# =========================
# OBTENER PRODUCTOS
# =========================
def obtener_admproductos(activo=None):

    conn = conectar()
    cursor = conn.cursor()

    sql = """
        SELECT *
        FROM productos
        WHERE 1=1
    """

    params = []

    if activo is not None:
        sql += " AND activo = ?"
        params.append(activo)

    sql += " ORDER BY id"

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    conn.close()

    productos = []

    for r in rows:
        productos.append({
            "id": r["id"],
            "codigo": r["codigo"],
            "producto": r["producto"],
            "marca": r["marca"],
            "tipo": r["tipo"],
            "presentacion": r["presentacion"],
            "stock": r["stock"],
            "precio": r["precio"],
            "imagen": r["imagen"],
            "activo": r["activo"]
        })

    return productos

# ======================================================
# REPORTE DE INVENTARIO ACTUAL
# ======================================================
def obtener_reporte_inventario():
 
    conn = conectar()
    cursor = conn.cursor()
 
    cursor.execute("""
        SELECT codigo, producto, marca, tipo, presentacion, stock, precio
        FROM productos
        WHERE activo = 1
        ORDER BY producto
    """)
 
    rows = cursor.fetchall()
    conn.close()
 
    inventario = []
 
    for r in rows:
 
        stock = r["stock"] or 0
        precio = r["precio"] or 0
 
        inventario.append({
            "codigo": r["codigo"],
            "producto": r["producto"],
            "marca": r["marca"],
            "tipo": r["tipo"],
            "presentacion": r["presentacion"],
            "stock": stock,
            "precio": precio,
            "valor_stock": stock * precio
        })
 
    return inventario
 
 
def actualizar_producto(
        producto_id,
        producto,
        marca,
        tipo,
        presentacion,
        stock,
        precio
):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE productos
            SET
                producto = ?,
                marca = ?,
                tipo = ?,
                presentacion = ?,
                stock = ?,
                precio = ?
            WHERE id = ?
        """, (
            producto,
            marca,
            tipo,
            presentacion,
            stock,
            precio,
            producto_id
        ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ======================================================
# CREAR UN PRODUCTO NUEVO (alta manual)
# ======================================================
# - Verifica que el código no exista (sin distinguir mayúsculas,
#   y avisando si existe pero está desactivado).
# - Guarda el producto con su stock inicial.
# - Si el stock inicial es mayor que 0, deja el movimiento en
#   movimientos_stock (tipo REGULARIZACION) dentro de la MISMA
#   transacción: o se guarda todo, o no se guarda nada.
# Lanza ValueError con un mensaje listo para mostrar al usuario.
# ======================================================
def crear_producto(codigo, producto, marca, tipo, presentacion,
                   stock_inicial, precio, imagen="SIN_IMAGEN.jpg"):

    codigo = (codigo or "").strip()
    producto = (producto or "").strip()

    if not codigo:
        raise ValueError("El código es obligatorio.")

    if not producto:
        raise ValueError("El nombre del producto es obligatorio.")

    if stock_inicial < 0:
        raise ValueError("El stock inicial no puede ser negativo.")

    if precio < 0:
        raise ValueError("El precio no puede ser negativo.")

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT producto, activo
            FROM productos
            WHERE codigo = ? COLLATE NOCASE
        """, (codigo,))

        existente = cursor.fetchone()

        if existente is not None:
            estado = "" if existente["activo"] == 1 else " (está desactivado)"
            raise ValueError(
                f"El código {codigo} ya existe: {existente['producto']}{estado}. "
                "Usa otro código."
            )

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO productos
            (codigo, producto, marca, tipo, presentacion, stock, precio,
             imagen, activo, fecha_creacion, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (
            codigo, producto, marca, tipo, presentacion,
            stock_inicial, precio, imagen, ahora, ahora
        ))

        if stock_inicial > 0:
            cursor.execute("""
                INSERT INTO movimientos_stock
                (producto_codigo, fecha, tipo, cantidad, stock_anterior,
                 stock_nuevo, pedido_id, observacion)
                VALUES (?, ?, 'REGULARIZACION', ?, 0, ?, NULL, ?)
            """, (
                codigo, ahora, stock_inicial, stock_inicial,
                "Stock inicial al crear el producto"
            ))

        conn.commit()

    except sqlite3.IntegrityError:
        # Red de seguridad: la base también exige código único
        conn.rollback()
        raise ValueError(f"El código {codigo} ya existe. Usa otro código.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ======================================================
# NOMBRES DE PRODUCTO YA USADOS (para sugerir al escribir)
# ======================================================
# El campo "producto" funciona como familia en el catálogo; sugerir
# los nombres existentes evita crear familias duplicadas por typos.
def obtener_nombres_producto():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT producto FROM productos
        WHERE producto IS NOT NULL AND producto != ''
        ORDER BY producto
    """)

    nombres = [fila["producto"] for fila in cursor.fetchall()]
    conn.close()

    return nombres
