from datetime import datetime
from services.database_service import conectar
from services.stock_service import ajustar_stock_manual


# ======================================================
# GENERAR NÚMERO DE COMPRA (COM-001, COM-002, ...)
# ======================================================
def generar_numero_compra(cursor):
    cursor.execute("SELECT COUNT(*) AS n FROM compras")
    total = cursor.fetchone()["n"]
    return f"COM-{total + 1:03d}"


# ======================================================
# REGISTRAR UNA COMPRA
# ======================================================
# items: lista de {"codigo": ..., "cantidad": ..., "precio_unitario": ...}
#
# Por cada producto:
# 1. Suma el stock (reutiliza el movimiento "COMPRA" que ya
#    existía en stock_service, con su misma trazabilidad).
# 2. Recalcula el costo promedio ponderado en productos.precio_compra,
#    para que el margen de ganancia sea preciso aunque compres el
#    mismo producto varias veces a precios distintos.
# ======================================================
def registrar_compra(proveedor, items, observacion="", usuario=None):

    if not items:
        raise ValueError("La compra debe tener al menos un producto")

    conn = conectar()
    cursor = conn.cursor()

    try:
        numero = generar_numero_compra(cursor)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO compras (numero, proveedor, fecha, total, observacion, usuario)
            VALUES (?, ?, ?, 0, ?, ?)
        """, (numero, proveedor, fecha, observacion, usuario))

        compra_id = cursor.lastrowid
        total_compra = 0

        for item in items:

            codigo = item["codigo"]
            cantidad = int(item["cantidad"])
            precio_unitario = float(item["precio_unitario"])

            cursor.execute("""
                SELECT producto, marca, stock, precio_compra
                FROM productos WHERE codigo = ?
            """, (codigo,))

            producto = cursor.fetchone()

            if producto is None:
                raise ValueError(f"Producto no encontrado: {codigo}")

            stock_anterior = producto["stock"] or 0
            costo_anterior = producto["precio_compra"] or 0

            # Costo promedio ponderado: mezcla lo que ya tenías en
            # stock (a su costo anterior) con lo nuevo que compras.
            stock_total = stock_anterior + cantidad
            if stock_total > 0:
                costo_nuevo = (
                    (stock_anterior * costo_anterior) + (cantidad * precio_unitario)
                ) / stock_total
            else:
                costo_nuevo = precio_unitario

            cursor.execute("""
                UPDATE productos SET precio_compra = ? WHERE codigo = ?
            """, (costo_nuevo, codigo))

            subtotal = cantidad * precio_unitario
            total_compra += subtotal

            cursor.execute("""
                INSERT INTO detalle_compra
                (compra_id, producto_codigo, producto, marca, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                compra_id, codigo, producto["producto"], producto["marca"],
                cantidad, precio_unitario, subtotal
            ))

        cursor.execute("""
            UPDATE compras SET total = ? WHERE id = ?
        """, (total_compra, compra_id))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    # El movimiento de stock se registra en su propia conexión,
    # reutilizando la función que ya existía y tiene su propia
    # trazabilidad en movimientos_stock.
    for item in items:
        ajustar_stock_manual(
            codigo=item["codigo"],
            tipo="COMPRA",
            cantidad=int(item["cantidad"]),
            observacion=f"Compra {numero}" + (f" - {proveedor}" if proveedor else "")
        )

    return {"id": compra_id, "numero": numero, "total": total_compra}


# ======================================================
# LISTAR COMPRAS (historial)
# ======================================================
def listar_compras():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, numero, proveedor, fecha, total, observacion, usuario
        FROM compras
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


# ======================================================
# OBTENER UNA COMPRA CON SU DETALLE
# ======================================================
def obtener_compra(compra_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM compras WHERE id = ?", (compra_id,))
    cabecera = cursor.fetchone()

    if cabecera is None:
        conn.close()
        return None

    cursor.execute("""
        SELECT * FROM detalle_compra WHERE compra_id = ?
    """, (compra_id,))

    detalle = cursor.fetchall()
    conn.close()

    return {
        "cabecera": dict(cabecera),
        "detalle": [dict(d) for d in detalle]
    }


# ======================================================
# MÁRGENES DE GANANCIA (precio venta vs costo promedio)
# ======================================================
def obtener_margenes():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT codigo, producto, marca, presentacion, stock, precio, precio_compra
        FROM productos
        WHERE activo = 1
        ORDER BY producto
    """)

    productos = cursor.fetchall()
    conn.close()

    resultado = []

    for p in productos:

        precio = p["precio"] or 0
        costo = p["precio_compra"] or 0

        margen_soles = precio - costo
        margen_pct = (margen_soles / costo * 100) if costo > 0 else None

        resultado.append({
            "codigo": p["codigo"],
            "producto": p["producto"],
            "marca": p["marca"],
            "presentacion": p["presentacion"],
            "stock": p["stock"],
            "precio": precio,
            "costo": costo,
            "margen_soles": margen_soles,
            "margen_pct": margen_pct,
            "valor_potencial_ganancia": margen_soles * (p["stock"] or 0)
        })

    return resultado
