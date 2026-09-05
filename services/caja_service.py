from datetime import datetime
from services.database_service import conectar

TIPOS_PAGO = ["Efectivo", "Yape", "Visa"]

# ======================================================
# REGISTRAR INGRESO POR PAGO DE UN PEDIDO
# ======================================================
# Se llama cuando se marca un pedido como "pagado".
# No crea duplicados: si ya existe un ingreso para ese
# pedido, lo actualiza en vez de insertar uno nuevo
# (útil cuando se edita el pedido después de marcarlo pagado).
# ======================================================
def registrar_ingreso_pedido(cursor, pedido_id, tipo_pago, monto):

    cursor.execute("""
        SELECT id FROM caja_movimientos
        WHERE pedido_id = ? AND tipo_movimiento = 'INGRESO_PEDIDO'
    """, (pedido_id,))

    existente = cursor.fetchone()

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if existente:

        cursor.execute("""
            UPDATE caja_movimientos
            SET tipo_pago = ?, monto = ?, fecha = ?
            WHERE id = ?
        """, (tipo_pago, monto, fecha, existente["id"]))

    else:

        cursor.execute("""
            INSERT INTO caja_movimientos
            (fecha, tipo_pago, tipo_movimiento, monto, pedido_id, observacion)
            VALUES (?, ?, 'INGRESO_PEDIDO', ?, ?, ?)
        """, (fecha, tipo_pago, monto, pedido_id, "Pago de pedido"))


# ======================================================
# ANULAR EL INGRESO DE UN PEDIDO (se desmarca pagado
# o se cancela el pedido)
# ======================================================
def anular_ingreso_pedido(cursor, pedido_id):

    cursor.execute("""
        DELETE FROM caja_movimientos
        WHERE pedido_id = ? AND tipo_movimiento = 'INGRESO_PEDIDO'
    """, (pedido_id,))


# ======================================================
# MARCAR / DESMARCAR UN PEDIDO COMO PAGADO
# ======================================================
def marcar_pagado(pedido_id, pagado):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT total, tipo_pago, estado FROM pedidos WHERE id = ?
        """, (pedido_id,))

        row = cursor.fetchone()

        if row is None:
            raise ValueError("Pedido no encontrado")

        if row["estado"] == "CANCELADO":
            raise ValueError("Un pedido CANCELADO no puede marcarse como pagado")

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if pagado:

            cursor.execute("""
                UPDATE pedidos SET pagado = 1, fecha_pago = ? WHERE id = ?
            """, (fecha, pedido_id))

            registrar_ingreso_pedido(
                cursor, pedido_id, row["tipo_pago"], row["total"]
            )

        else:

            cursor.execute("""
                UPDATE pedidos SET pagado = 0, fecha_pago = NULL WHERE id = ?
            """, (pedido_id,))

            anular_ingreso_pedido(cursor, pedido_id)

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ======================================================
# REGISTRAR MOVIMIENTO MANUAL (GASTO O INGRESO MANUAL)
# ======================================================
def registrar_movimiento_manual(fecha, tipo_pago, tipo_movimiento, monto, observacion):

    if tipo_pago not in TIPOS_PAGO:
        raise ValueError(f"Tipo de pago inválido: {tipo_pago}")

    if tipo_movimiento not in ("INGRESO_MANUAL", "GASTO"):
        raise ValueError(f"Tipo de movimiento inválido: {tipo_movimiento}")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO caja_movimientos
        (fecha, tipo_pago, tipo_movimiento, monto, pedido_id, observacion)
        VALUES (?, ?, ?, ?, NULL, ?)
    """, (fecha, tipo_pago, tipo_movimiento, monto, observacion))

    conn.commit()
    conn.close()


# ======================================================
# ELIMINAR UN MOVIMIENTO MANUAL (para corregir un error
# de tipeo; nunca se usa sobre movimientos de pedidos)
# ======================================================
def eliminar_movimiento_manual(movimiento_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM caja_movimientos
        WHERE id = ? AND tipo_movimiento IN ('INGRESO_MANUAL', 'GASTO')
    """, (movimiento_id,))

    conn.commit()
    conn.close()


# ======================================================
# REPORTE DE CAJA (con filtros)
# ======================================================
def obtener_movimientos_caja(desde=None, hasta=None, tipo_pago=None):

    conn = conectar()
    cursor = conn.cursor()

    sql = """
        SELECT
            m.id, m.fecha, m.tipo_pago, m.tipo_movimiento,
            m.monto, m.pedido_id, m.observacion,
            p.numero AS pedido_numero
        FROM caja_movimientos m
        LEFT JOIN pedidos p ON p.id = m.pedido_id
        WHERE 1 = 1
    """

    parametros = []

    if desde:
        sql += " AND DATE(m.fecha) >= DATE(?)"
        parametros.append(desde)

    if hasta:
        sql += " AND DATE(m.fecha) <= DATE(?)"
        parametros.append(hasta)

    if tipo_pago:
        sql += " AND m.tipo_pago = ?"
        parametros.append(tipo_pago)

    sql += " ORDER BY m.id DESC"

    cursor.execute(sql, parametros)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return rows


# ======================================================
# SALDOS DE CAJA (todo lo acumulado, sin filtro de fecha)
# ======================================================
def obtener_saldos_caja():

    conn = conectar()
    cursor = conn.cursor()

    saldos = {}

    for tipo in TIPOS_PAGO:

        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE
                    WHEN tipo_movimiento = 'GASTO' THEN -monto
                    ELSE monto
                END
            ), 0) AS saldo
            FROM caja_movimientos
            WHERE tipo_pago = ?
        """, (tipo,))

        saldos[tipo] = cursor.fetchone()["saldo"]

    conn.close()

    return saldos
