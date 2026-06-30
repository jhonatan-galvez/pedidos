from datetime import datetime
from services.estados import *
from services.database_service import conectar
from services.cliente_service import (
    buscar_cliente_por_telefono,
    crear_cliente,
    actualizar_cliente
)


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
                observaciones,
                fecha_actualizacion,
                usuario
            )
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            numero,
            cliente_id,
            fecha,
            PENDIENTE,
            subtotal,
            delivery,
            descuento,
            total,
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
            p.fecha,
            p.estado,
            p.subtotal,
            p.delivery,
            p.descuento,
            p.total,
            p.observaciones,

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
        "fecha": row["fecha"],
        "estado": row["estado"],
        "subtotal": row["subtotal"],
        "delivery": row["delivery"],
        "descuento": row["descuento"],
        "total": row["total"],
        "observaciones": row["observaciones"],

        "cliente": {
            "nombre": row["nombre"],
            "telefono": row["telefono"],
            "direccion": row["direccion"],
            "referencia": row["referencia"]
        }

    }

    conn.close()

    pedido["detalle"] = obtener_pedido_detalle(pedido_id)

    return pedido

# ======================================================
# ACTUALIZAR ESTADO DEL PEDIDO
# ======================================================
def actualizar_estado_pedido(pedido_id, estado):

    conn = conectar()
    cursor = conn.cursor()

    try:

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








