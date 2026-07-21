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









