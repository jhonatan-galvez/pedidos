from datetime import datetime
from services.database_service import conectar

# Tipos de movimiento manual permitidos (además de "VENTA",
# que se genera automáticamente al entregar un pedido)
TIPOS_MANUALES = {
    "COMPRA": "Entrada por compra",
    "REGULARIZACION": "Regularización de inventario",
    "MERMA": "Salida por merma / pérdida"
}

# ======================================================
# DESCONTAR STOCK AL ENTREGAR UN PEDIDO
# ======================================================
# Recorre el detalle del pedido y, por cada producto,
# descuenta la cantidad del stock actual y registra el
# movimiento en movimientos_stock (auditoría / trazabilidad).
#
# IMPORTANTE: recibe un cursor ya abierto (misma transacción
# que actualizar_estado_pedido) para que si algo falla aquí,
# el cambio de estado tampoco se guarde (todo o nada).
# ======================================================
def descontar_stock_pedido(cursor, pedido_id):

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        SELECT producto_codigo, cantidad
        FROM detalle_pedido
        WHERE pedido_id = ?
    """, (pedido_id,))

    items = cursor.fetchall()

    for item in items:

        codigo = item["producto_codigo"]
        cantidad = item["cantidad"]

        cursor.execute("""
            SELECT stock FROM productos
            WHERE codigo = ?
        """, (codigo,))

        row = cursor.fetchone()

        if row is None:
            # Producto ya no existe en el catálogo (desactivado o
            # eliminado en una sincronización posterior). No se
            # puede descontar, pero no debe romper la entrega.
            continue

        stock_anterior = row["stock"]
        stock_nuevo = stock_anterior - cantidad

        cursor.execute("""
            UPDATE productos
            SET stock = ?
            WHERE codigo = ?
        """, (
            stock_nuevo,
            codigo
        ))

        cursor.execute("""
            INSERT INTO movimientos_stock
            (
                producto_codigo,
                fecha,
                tipo,
                cantidad,
                stock_anterior,
                stock_nuevo,
                pedido_id,
                observacion
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            codigo,
            fecha,
            "VENTA",
            -cantidad,
            stock_anterior,
            stock_nuevo,
            pedido_id,
            f"Descuento por entrega de pedido"
        ))


# ======================================================
# REVERTIR EL DESCUENTO DE STOCK DE UN PEDIDO
# ======================================================
# Se usa cuando un pedido ENTREGADO se cancela, o cuando
# se edita un pedido ya entregado (se revierte todo y
# luego se vuelve a descontar con los datos corregidos).
# ======================================================
def revertir_stock_pedido(cursor, pedido_id, observacion="Reversión de descuento de stock"):

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        SELECT producto_codigo, cantidad
        FROM detalle_pedido
        WHERE pedido_id = ?
    """, (pedido_id,))

    items = cursor.fetchall()

    for item in items:

        codigo = item["producto_codigo"]
        cantidad = item["cantidad"]

        cursor.execute("""
            SELECT stock FROM productos WHERE codigo = ?
        """, (codigo,))

        row = cursor.fetchone()

        if row is None:
            continue

        stock_anterior = row["stock"]
        stock_nuevo = stock_anterior + cantidad

        cursor.execute("""
            UPDATE productos SET stock = ? WHERE codigo = ?
        """, (stock_nuevo, codigo))

        cursor.execute("""
            INSERT INTO movimientos_stock
            (
                producto_codigo, fecha, tipo, cantidad,
                stock_anterior, stock_nuevo, pedido_id, observacion
            )
            VALUES (?, ?, 'AJUSTE', ?, ?, ?, ?, ?)
        """, (
            codigo, fecha, cantidad, stock_anterior,
            stock_nuevo, pedido_id, observacion
        ))

# ======================================================
# AJUSTE MANUAL DE STOCK
# ======================================================
# tipo: "COMPRA" (suma), "MERMA" (resta),
#       "REGULARIZACION" (fija el stock a un valor exacto)
# cantidad:
#   - COMPRA / MERMA: cantidad a sumar/restar (siempre positiva)
#   - REGULARIZACION: el nuevo valor de stock final
# ======================================================
def ajustar_stock_manual(codigo, tipo, cantidad, observacion=""):

    if tipo not in TIPOS_MANUALES:
        raise ValueError(f"Tipo de movimiento inválido: {tipo}")

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT stock FROM productos WHERE codigo = ?
        """, (codigo,))

        row = cursor.fetchone()

        if row is None:
            raise ValueError(f"Producto no encontrado: {codigo}")

        stock_anterior = row["stock"] or 0

        if tipo == "COMPRA":
            stock_nuevo = stock_anterior + cantidad
            cantidad_movimiento = cantidad

        elif tipo == "MERMA":
            stock_nuevo = stock_anterior - cantidad
            cantidad_movimiento = -cantidad

        else:  # REGULARIZACION
            stock_nuevo = cantidad
            cantidad_movimiento = stock_nuevo - stock_anterior

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            UPDATE productos
            SET stock = ?
            WHERE codigo = ?
        """, (
            stock_nuevo,
            codigo
        ))

        cursor.execute("""
            INSERT INTO movimientos_stock
            (
                producto_codigo,
                fecha,
                tipo,
                cantidad,
                stock_anterior,
                stock_nuevo,
                pedido_id,
                observacion
            )
            VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
        """, (
            codigo,
            fecha,
            tipo,
            cantidad_movimiento,
            stock_anterior,
            stock_nuevo,
            observacion
        ))

        conn.commit()

        return stock_nuevo

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ======================================================
# HISTORIAL DE MOVIMIENTOS DE UN PRODUCTO
# ======================================================
def obtener_movimientos_producto(codigo, limite=30):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id, fecha, tipo, cantidad,
            stock_anterior, stock_nuevo,
            pedido_id, observacion
        FROM movimientos_stock
        WHERE producto_codigo = ?
        ORDER BY id DESC
        LIMIT ?
    """, (codigo, limite))

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


# ======================================================
# REPORTE GENERAL DE MOVIMIENTOS DE STOCK
# ======================================================
def obtener_reporte_movimientos(desde=None, hasta=None, tipo=None):

    conn = conectar()
    cursor = conn.cursor()

    sql = """
        SELECT
            m.id,
            m.fecha,
            m.tipo,
            m.cantidad,
            m.stock_anterior,
            m.stock_nuevo,
            m.pedido_id,
            m.observacion,
            m.producto_codigo,
            p.producto,
            p.marca
        FROM movimientos_stock m
        LEFT JOIN productos p
            ON p.codigo = m.producto_codigo
        WHERE 1 = 1
    """

    parametros = []

    if desde:
        sql += " AND DATE(m.fecha) >= DATE(?)"
        parametros.append(desde)

    if hasta:
        sql += " AND DATE(m.fecha) <= DATE(?)"
        parametros.append(hasta)

    if tipo:
        sql += " AND m.tipo = ?"
        parametros.append(tipo)

    sql += " ORDER BY m.id DESC"

    cursor.execute(sql, parametros)

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]
