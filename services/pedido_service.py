from datetime import datetime
from services.estados import *
from services.database_service import conectar
from services.cliente_service import (
    buscar_cliente_por_telefono,
    crear_cliente,
    actualizar_cliente
)
from services.producto_service import obtener_productos
from services.stock_service import descontar_stock_pedido, revertir_stock_pedido
import services.caja_service as caja_service

# ======================================================
# GENERAR NÚMERO DE PEDIDO
# ======================================================
def generar_numero_pedido(cursor):

    cursor.execute("""
        SELECT COUNT(*)
        FROM pedidos
    """)

    cantidad = cursor.fetchone()[0]

    return f"PED-{cantidad + 1:06d}"

# ======================================================
# CALCULAR TOTALES
# ======================================================
def calcular_totales(carrito, delivery=0, descuento=0):

    subtotal = sum(
        item["precio"] * item["cantidad"]
        for item in carrito
    )

    total = subtotal + delivery - descuento

    return subtotal, total

# ======================================================
# CREAR PEDIDO
# ======================================================
def crear_pedido(datos_cliente, carrito):

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ============================================
        # CLIENTE
        # ============================================

        telefono = datos_cliente["telefono"]

        cliente = buscar_cliente_por_telefono(
            cursor,
            telefono
        )

        if cliente:

            actualizar_cliente(
                cursor,
                cliente["id"],
                datos_cliente["nombre"],
                datos_cliente["direccion"],
                datos_cliente["referencia"]
            )

            cliente_id = cliente["id"]

        else:

            cliente_id = crear_cliente(
                cursor,
                datos_cliente["nombre"],
                telefono,
                datos_cliente["direccion"],
                datos_cliente["referencia"]
            )

        # ============================================
        # TOTALES
        # ============================================

        delivery = datos_cliente.get("delivery", 0)
        descuento = datos_cliente.get("descuento", 0)

        subtotal, total = calcular_totales(
            carrito,
            delivery,
            descuento
        )

        # ============================================
        # PEDIDO
        # ============================================

        numero = generar_numero_pedido(cursor)

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO pedidos
            (
                numero,
                cliente_id,
                fecha,
                estado,
                subtotal,
                delivery,
                descuento,
                total,
                tipo_pago,
                observaciones,
                fecha_actualizacion,
                usuario
            )
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            numero,
            cliente_id,
            fecha,
            PENDIENTE,
            subtotal,
            delivery,
            descuento,
            total,
            datos_cliente["tipo_pago"],
            datos_cliente.get("observaciones", ""),
            fecha,
            "WEB"

        ))

        pedido_id = cursor.lastrowid

        # ============================================
        # DETALLE DEL PEDIDO
        # ============================================

        for item in carrito:

            subtotal_item = item["cantidad"] * item["precio"]

            cursor.execute("""
                INSERT INTO detalle_pedido
                (
                    pedido_id,
                    producto_codigo,
                    producto,
                    marca,
                    presentacion,
                    cantidad,
                    precio_unitario,
                    subtotal
                )
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?)
            """, (

                pedido_id,
                item["codigo"],
                item["producto"],
                item["marca"],
                item.get("presentacion", ""),
                item["cantidad"],
                item["precio"],
                subtotal_item

            ))

        # ============================================
        # CONFIRMAR TRANSACCIÓN
        # ============================================

        conn.commit()

        return pedido_id

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()




# ======================================================
# ADM/ OBTENER PEDIDO
# ====================================================== 
def obtener_pedidos(
        buscar=None,
        estado=None,
        desde=None,
        hasta=None):

    conn = conectar()
    cursor = conn.cursor()

    sql = """
        SELECT

            p.id,
            p.numero,
            p.fecha,
            p.estado,
            p.subtotal,
            p.delivery,
            p.descuento,
            p.total,
            p.tipo_pago,
            p.pagado,

            c.nombre,
            c.telefono

        FROM pedidos p

        INNER JOIN clientes c
            ON c.id = p.cliente_id

        WHERE 1 = 1
    """

    parametros = []

    # ==========================================
    # BUSCAR
    # ==========================================
    if buscar:

        sql += """
            AND (
                p.numero LIKE ?
                OR c.nombre LIKE ?
                OR REPLACE(c.telefono, ' ', '') LIKE REPLACE(?, ' ', '')
            )
        """

        texto = f"%{buscar}%"

        parametros.extend([
            texto,
            texto,
            texto
        ])

    # ==========================================
    # ESTADO
    # ==========================================
    if estado:

        sql += """
            AND p.estado = ?
        """

        parametros.append(estado)

    # ==========================================
    # FECHA DESDE
    # ==========================================
    if desde:

        sql += """
            AND DATE(p.fecha) >= DATE(?)
        """

        parametros.append(desde)

    # ==========================================
    # FECHA HASTA
    # ==========================================
    if hasta:

        sql += """
            AND DATE(p.fecha) <= DATE(?)
        """

        parametros.append(hasta)

    # ==========================================
    # ORDEN
    # ==========================================
    sql += """
        ORDER BY p.id DESC
    """

    cursor.execute(sql, parametros)

    rows = cursor.fetchall()

    conn.close()

    pedidos = []

    for row in rows:

        pedidos.append({

            "id": row["id"],
            "numero": row["numero"],
            "fecha": row["fecha"],
            "estado": row["estado"],
            "subtotal": row["subtotal"],
            "delivery": row["delivery"],
            "descuento": row["descuento"],
            "total": row["total"],
            "tipo_pago": row["tipo_pago"],
            "pagado": bool(row["pagado"]),

            "cliente": row["nombre"],
            "telefono": row["telefono"]

        })

    return pedidos

# ======================================================
# ADM/ OBTENER PEDIDO_DETALLE
# ======================================================
def obtener_pedido_detalle(pedido_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT

            id,
            producto_codigo,
            producto,
            marca,
            presentacion,
            cantidad,
            precio_unitario,
            subtotal

        FROM detalle_pedido

        WHERE pedido_id = ?

        ORDER BY id
    """, (pedido_id,))

    rows = cursor.fetchall()

    conn.close()

    detalle = []

    for row in rows:

        detalle.append({

            "id": row["id"],
            "codigo": row["producto_codigo"],
            "producto": row["producto"],
            "marca": row["marca"],
            "presentacion": row["presentacion"],
            "cantidad": row["cantidad"],
            "precio_unitario": row["precio_unitario"],
            "subtotal": row["subtotal"]

        })

    return detalle

# ======================================================
# ADM/ OBTENER PEDIDO_COMPLETO
# ======================================================
def obtener_pedido_completo(pedido_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT

            p.id,
            p.numero,
            p.cliente_id,
            p.fecha,
            p.estado,
            p.subtotal,
            p.delivery,
            p.descuento,
            p.total,
            p.tipo_pago,
            p.observaciones,
            p.pagado,
            c.nombre,
            c.telefono,
            c.direccion,
            c.referencia

        FROM pedidos p

        INNER JOIN clientes c
            ON c.id = p.cliente_id

        WHERE p.id = ?

    """, (pedido_id,))

    row = cursor.fetchone()

    if row is None:

        conn.close()
        return None

    pedido = {
        "id": row["id"],
        "numero": row["numero"],
        "cliente_id": row["cliente_id"],
        "fecha": row["fecha"],
        "estado": row["estado"],
        "subtotal": row["subtotal"],
        "delivery": row["delivery"],
        "descuento": row["descuento"],
        "total": row["total"],
        "observaciones": row["observaciones"],

        "tipo_pago": row["tipo_pago"],
        "pagado": bool(row["pagado"]),

        "cliente": {
            "nombre": row["nombre"],
            "telefono": row["telefono"],
            "direccion": row["direccion"],
            "referencia": row["referencia"]
        }

    }

    conn.close()

    pedido["detalle"] = obtener_pedido_detalle(pedido_id)
    pedido["productos_catalogo"] = obtener_productos()
    
    return pedido

# ======================================================
# ACTUALIZAR ESTADO DEL PEDIDO
# ======================================================
def actualizar_estado_pedido(pedido_id, estado):

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ============================================
        # ESTADO ANTERIOR (para saber si ya se
        # había descontado stock antes)
        # ============================================
        cursor.execute("""
            SELECT estado FROM pedidos WHERE id = ?
        """, (pedido_id,))

        row = cursor.fetchone()

        if row is None:
            return False

        estado_anterior = row["estado"]

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            UPDATE pedidos
            SET
                estado = ?,
                fecha_actualizacion = ?
            WHERE id = ?
        """, (

            estado,
            fecha,
            pedido_id

        ))

        # ============================================
        # DESCONTAR STOCK
        # Solo si pasa a ENTREGADO y antes NO estaba
        # ENTREGADO (evita descuento doble)
        # ============================================
        if estado == ENTREGADO and estado_anterior != ENTREGADO:

            descontar_stock_pedido(cursor, pedido_id)

        # ============================================
        # CANCELAR PEDIDO
        # No debe dejar rastro en stock ni en caja:
        # - si ya estaba ENTREGADO, se revierte el stock
        # - si ya estaba pagado, se anula el ingreso de caja
        # ============================================
        elif estado == CANCELADO and estado_anterior != CANCELADO:

            if estado_anterior == ENTREGADO:

                revertir_stock_pedido(
                    cursor, pedido_id,
                    observacion="Reversión por cancelación de pedido"
                )

            cursor.execute("""
                SELECT pagado FROM pedidos WHERE id = ?
            """, (pedido_id,))

            row_pago = cursor.fetchone()

            if row_pago and row_pago["pagado"]:

                caja_service.anular_ingreso_pedido(cursor, pedido_id)

                cursor.execute("""
                    UPDATE pedidos SET pagado = 0, fecha_pago = NULL WHERE id = ?
                """, (pedido_id,))

        conn.commit()

        return cursor.rowcount > 0

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()

# ======================================================
# DASHBOARD
# ======================================================
def obtener_dashboard():

    conn = conectar()
    cursor = conn.cursor()

    # =========================
    # PEDIDOS POR ESTADO
    # =========================
    cursor.execute("""
        SELECT estado, COUNT(*) as total
        FROM pedidos
        GROUP BY estado
    """)

    estados = {row["estado"]: row["total"] for row in cursor.fetchall()}

    # =========================
    # VENTAS HOY
    # =========================
    cursor.execute("""
        SELECT IFNULL(SUM(total), 0)
        FROM pedidos
        WHERE DATE(fecha) = DATE('now')
    """)

    ventas_hoy = cursor.fetchone()[0]

    # =========================
    # ÚLTIMOS PEDIDOS
    # =========================
    cursor.execute("""
        SELECT
            p.id,
            p.numero,
            p.fecha,
            p.estado,
            p.total,
            c.nombre
        FROM pedidos p
        INNER JOIN clientes c ON c.id = p.cliente_id
        ORDER BY p.id DESC
        LIMIT 5
    """)

    ultimos = cursor.fetchall()

    conn.close()

    return {
        "estados": estados,
        "ventas_hoy": ventas_hoy,
        "ultimos": ultimos
    }

def obtener_pedidos_cliente(cliente_id):

    conn = conectar()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT

            id,
            numero,
            fecha,
            estado,
            total

        FROM pedidos

        WHERE cliente_id = ?

        ORDER BY id DESC


    """,(cliente_id,))


    rows = cursor.fetchall()

    conn.close()


    pedidos=[]


    for r in rows:

        pedidos.append({

            "id": r["id"],
            "numero": r["numero"],
            "fecha": r["fecha"],
            "estado": r["estado"],
            "total": r["total"]

        })


    return pedidos

# ======================================================
# EDITAR PEDIDO
# ======================================================

def actualizar_pedido(pedido_id, datos, items):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT estado, pagado, cliente_id FROM pedidos WHERE id = ?
        """, (pedido_id,))

        row = cursor.fetchone()

        if row is None:
            raise ValueError("Pedido no encontrado")

        # Un pedido CANCELADO no tiene sentido editarlo (para
        # corregirlo hay que reactivarlo primero cambiando el estado)
        if row["estado"] == "CANCELADO":
            raise ValueError(
                "Este pedido está CANCELADO. Cambia el estado antes de editarlo."
            )

        estaba_entregado = row["estado"] == ENTREGADO
        estaba_pagado = bool(row["pagado"])
        cliente_id_anterior = row["cliente_id"]

        # ============================================
        # Si ya estaba ENTREGADO, revertimos el
        # descuento de stock ANTES de tocar el detalle.
        # Al final se vuelve a descontar con los datos
        # ya corregidos (dueño puede editar libremente,
        # el sistema mantiene el stock consistente solo).
        # ============================================
        if estaba_entregado:

            revertir_stock_pedido(
                cursor, pedido_id,
                observacion="Reversión por edición de pedido ya entregado"
            )

        # ============================================
        # CLIENTE: existente distinto, o uno nuevo
        # ============================================
        cliente_id = cliente_id_anterior

        if datos.get("cliente_nuevo"):

            telefono_nuevo = datos["cliente_nuevo"]["telefono"].strip() or None

            existente = None

            # Solo buscamos coincidencia si hay un teléfono real.
            # Un teléfono vacío/None nunca debe "fusionar" con otro
            # cliente que también lo tenga vacío.
            if telefono_nuevo:
                existente = buscar_cliente_por_telefono(cursor, telefono_nuevo)

            if existente:

                cliente_id = existente["id"]

                cursor.execute("""
                    UPDATE pedidos SET cliente_id = ? WHERE id = ?
                """, (cliente_id, pedido_id))

            else:

                cursor.execute("""
                    INSERT INTO clientes (nombre, telefono, direccion, referencia)
                    VALUES (?, ?, ?, ?)
                """, (
                    datos["cliente_nuevo"]["nombre"],
                    telefono_nuevo,
                    datos["cliente_nuevo"]["direccion"],
                    datos["cliente_nuevo"]["referencia"]
                ))

                cliente_id = cursor.lastrowid

                cursor.execute("""
                    UPDATE pedidos SET cliente_id = ? WHERE id = ?
                """, (cliente_id, pedido_id))

        elif datos.get("cliente_id") and int(datos["cliente_id"]) != cliente_id_anterior:

            cliente_id = int(datos["cliente_id"])

            cursor.execute("""
                UPDATE pedidos SET cliente_id = ? WHERE id = ?
            """, (cliente_id, pedido_id))

        # ============================================
        # DATOS GENERALES
        # ============================================
        cursor.execute("""
            UPDATE pedidos
            SET
                tipo_pago = ?,
                observaciones = ?
            WHERE id = ?
        """,
        (

            datos["tipo_pago"],
            datos["observaciones"],
            pedido_id

        ))

        # La dirección se guarda sobre el cliente que haya
        # quedado asignado al pedido (el nuevo, el reasignado,
        # o el mismo de siempre)
        cursor.execute("""
            UPDATE clientes
            SET direccion = ?
            WHERE id = ?
        """,
        (
            datos["direccion"],
            cliente_id
        ))

        # ============================================
        # PRODUCTOS DEL PEDIDO
        # ============================================
        for item in items:

            # Fila marcada para eliminar, o cantidad en 0
            if item["eliminar"] or item["cantidad"] <= 0:

                if item["id"]:
                    cursor.execute("""
                        DELETE FROM detalle_pedido WHERE id = ?
                    """, (item["id"],))

                continue

            cursor.execute("""
                SELECT producto, marca, presentacion, precio
                FROM productos
                WHERE codigo = ?
            """, (item["codigo"],))

            prod = cursor.fetchone()

            if prod is None:
                # Código inválido/inexistente: se ignora la fila
                continue

            subtotal = prod["precio"] * item["cantidad"]

            if item["id"]:

                cursor.execute("""
                    UPDATE detalle_pedido
                    SET
                        producto_codigo = ?,
                        producto = ?,
                        marca = ?,
                        presentacion = ?,
                        cantidad = ?,
                        precio_unitario = ?,
                        subtotal = ?
                    WHERE id = ?
                """, (
                    item["codigo"],
                    prod["producto"],
                    prod["marca"],
                    prod["presentacion"],
                    item["cantidad"],
                    prod["precio"],
                    subtotal,
                    item["id"]
                ))

            else:

                cursor.execute("""
                    INSERT INTO detalle_pedido
                    (
                        pedido_id, producto_codigo, producto, marca,
                        presentacion, cantidad, precio_unitario, subtotal
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pedido_id,
                    item["codigo"],
                    prod["producto"],
                    prod["marca"],
                    prod["presentacion"],
                    item["cantidad"],
                    prod["precio"],
                    subtotal
                ))

        # ============================================
        # RECALCULAR SUBTOTAL Y TOTAL DEL PEDIDO
        # ============================================
        cursor.execute("""
            SELECT COALESCE(SUM(subtotal), 0) AS s
            FROM detalle_pedido
            WHERE pedido_id = ?
        """, (pedido_id,))

        subtotal_pedido = cursor.fetchone()["s"]

        cursor.execute("""
            SELECT delivery, descuento FROM pedidos WHERE id = ?
        """, (pedido_id,))

        row2 = cursor.fetchone()
        delivery = row2["delivery"] or 0
        descuento = row2["descuento"] or 0

        total_pedido = subtotal_pedido + delivery - descuento

        cursor.execute("""
            UPDATE pedidos
            SET subtotal = ?, total = ?
            WHERE id = ?
        """, (subtotal_pedido, total_pedido, pedido_id))

        # ============================================
        # Si ya estaba ENTREGADO, volvemos a descontar
        # stock, esta vez con el detalle ya corregido
        # ============================================
        if estaba_entregado:

            descontar_stock_pedido(cursor, pedido_id)

        # ============================================
        # Si ya estaba PAGADO, el ingreso de caja se
        # actualiza al nuevo total / tipo de pago
        # ============================================
        if estaba_pagado:

            caja_service.registrar_ingreso_pedido(
                cursor, pedido_id, datos["tipo_pago"], total_pedido
            )

        conn.commit()


    except Exception:

        conn.rollback()
        raise


    finally:

        conn.close()

# ======================================================
# REPORTE DE VENTAS
# ======================================================

def obtener_reporte_ventas(desde=None, hasta=None):

    conn = conectar()
    cursor = conn.cursor()

    try:

        sql = """
            SELECT
                p.id AS pedido_id,
                p.numero AS numero_pedido,
                p.fecha,
                p.estado,
                p.tipo_pago,

                c.nombre AS cliente,
                c.telefono,

                d.producto_codigo AS codigo,
                d.producto,
                d.marca,
                d.presentacion,
                d.cantidad,
                d.precio_unitario,
                d.subtotal AS importe

            FROM pedidos p

            INNER JOIN clientes c
                ON c.id = p.cliente_id

            INNER JOIN detalle_pedido d
                ON d.pedido_id = p.id

            WHERE p.estado = 'ENTREGADO'
        """

        parametros = []

        # =========================
        # FECHA DESDE
        # =========================

        if desde:

            sql += """
                AND DATE(p.fecha) >= DATE(?)
            """

            parametros.append(desde)

        # =========================
        # FECHA HASTA
        # =========================

        if hasta:

            sql += """
                AND DATE(p.fecha) <= DATE(?)
            """

            parametros.append(hasta)

        # =========================
        # ORDEN
        # =========================

        sql += """
            ORDER BY
                p.id DESC,
                d.id ASC
        """

        cursor.execute(
            sql,
            parametros
        )

        rows = cursor.fetchall()

        reporte = []

        for row in rows:

            reporte.append({

                "pedido_id": row["pedido_id"],
                "numero_pedido": row["numero_pedido"],
                "fecha": row["fecha"],
                "estado": row["estado"],
                "tipo_pago": row["tipo_pago"],

                "cliente": row["cliente"],
                "telefono": row["telefono"],

                "codigo": row["codigo"],
                "producto": row["producto"],
                "marca": row["marca"],
                "presentacion": row["presentacion"],

                "cantidad": row["cantidad"],
                "precio_unitario": row["precio_unitario"],
                "importe": row["importe"]

            })

        return reporte

    finally:

        conn.close()

# ======================================================
# REPORTE - VENTAS POR PRODUCTO
# ======================================================

def obtener_ventas_por_producto(desde=None, hasta=None):

    conn = conectar()
    cursor = conn.cursor()

    sql = """
        SELECT

            dp.producto_codigo,
            dp.producto,
            dp.marca,
            dp.presentacion,

            SUM(dp.cantidad) AS cantidad_vendida,

            SUM(dp.subtotal) AS importe_vendido

        FROM detalle_pedido dp

        INNER JOIN pedidos p
            ON p.id = dp.pedido_id

        WHERE p.estado = 'ENTREGADO'
    """

    parametros = []

    # ============================================
    # FECHA DESDE
    # ============================================

    if desde:

        sql += """
            AND DATE(p.fecha) >= DATE(?)
        """

        parametros.append(desde)

    # ============================================
    # FECHA HASTA
    # ============================================

    if hasta:

        sql += """
            AND DATE(p.fecha) <= DATE(?)
        """

        parametros.append(hasta)

    # ============================================
    # AGRUPAR
    # ============================================

    sql += """
        GROUP BY
            dp.producto_codigo,
            dp.producto,
            dp.marca,
            dp.presentacion

        ORDER BY
            cantidad_vendida DESC
    """

    cursor.execute(sql, parametros)

    rows = cursor.fetchall()

    conn.close()

    ventas = []

    for row in rows:

        ventas.append({

            "codigo": row["producto_codigo"],

            "producto": row["producto"],

            "marca": row["marca"],

            "presentacion": row["presentacion"],

            "cantidad": row["cantidad_vendida"],

            "importe": row["importe_vendido"]

        })

    return ventas