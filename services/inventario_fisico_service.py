from datetime import datetime
from services.database_service import conectar
from services.stock_service import ajustar_stock_manual


# ======================================================
# GENERAR NÚMERO DE INVENTARIO (INV-001, INV-002, ...)
# ======================================================
def generar_numero_inventario(cursor):

    cursor.execute("SELECT COUNT(*) AS n FROM inventarios_fisicos")
    total = cursor.fetchone()["n"]

    return f"INV-{total + 1:03d}"


# ======================================================
# CREAR UN NUEVO INVENTARIO FÍSICO
# ======================================================
# Toma una "foto" del stock teórico actual de todos los
# productos activos y arma el detalle vacío (stock_real
# en NULL) para que se vaya llenando durante el conteo.
# ======================================================
def crear_inventario(observacion="", usuario=None):

    conn = conectar()
    cursor = conn.cursor()

    try:
        numero = generar_numero_inventario(cursor)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO inventarios_fisicos
            (numero, fecha_inicio, estado, observacion, usuario)
            VALUES (?, ?, 'ABIERTO', ?, ?)
        """, (numero, fecha, observacion, usuario))

        inventario_id = cursor.lastrowid

        cursor.execute("""
            SELECT codigo, producto, marca, tipo, presentacion, stock
            FROM productos
            WHERE activo = 1
            ORDER BY codigo
        """)

        productos = cursor.fetchall()

        for p in productos:
            cursor.execute("""
                INSERT INTO inventario_fisico_detalle
                (inventario_id, producto_codigo, producto, marca, tipo,
                 presentacion, stock_teorico, stock_real, diferencia)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL)
            """, (
                # La columna "tipo" de esta tabla se usa solo como
                # etiqueta de agrupación visual; ahora guarda el valor
                # de "producto" (la familia real), no el campo "tipo"
                # de la tabla productos.
                inventario_id, p["codigo"], p["producto"], p["marca"],
                p["producto"], p["presentacion"], p["stock"]
            ))

        conn.commit()

        return {"id": inventario_id, "numero": numero}

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ======================================================
# GUARDAR EL CONTEO REAL DE UN PRODUCTO
# ======================================================
def guardar_conteo(inventario_id, producto_codigo, stock_real):

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT stock_teorico FROM inventario_fisico_detalle
            WHERE inventario_id = ? AND producto_codigo = ?
        """, (inventario_id, producto_codigo))

        row = cursor.fetchone()

        if row is None:
            raise ValueError("Ese producto no pertenece a este inventario")

        stock_teorico = row["stock_teorico"] or 0
        diferencia = stock_real - stock_teorico
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            UPDATE inventario_fisico_detalle
            SET stock_real = ?, diferencia = ?, fecha_conteo = ?
            WHERE inventario_id = ? AND producto_codigo = ?
        """, (stock_real, diferencia, fecha, inventario_id, producto_codigo))

        conn.commit()

        return {"stock_teorico": stock_teorico, "diferencia": diferencia}

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ======================================================
# LISTAR INVENTARIOS (historial)
# ======================================================
def listar_inventarios():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            i.id, i.numero, i.fecha_inicio, i.fecha_cierre,
            i.estado, i.observacion, i.usuario,
            COUNT(d.id) AS total_productos,
            SUM(CASE WHEN d.stock_real IS NOT NULL THEN 1 ELSE 0 END) AS contados,
            SUM(CASE WHEN d.diferencia != 0 THEN 1 ELSE 0 END) AS con_diferencia
        FROM inventarios_fisicos i
        LEFT JOIN inventario_fisico_detalle d ON d.inventario_id = i.id
        GROUP BY i.id
        ORDER BY i.id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


# ======================================================
# OBTENER UN INVENTARIO CON SU DETALLE (para la pantalla
# de conteo, agrupado luego por familia en el template)
# ======================================================
def obtener_inventario(inventario_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM inventarios_fisicos WHERE id = ?
    """, (inventario_id,))

    cabecera = cursor.fetchone()

    if cabecera is None:
        conn.close()
        return None

    cursor.execute("""
        SELECT * FROM inventario_fisico_detalle
        WHERE inventario_id = ?
        ORDER BY tipo, producto
    """, (inventario_id,))

    detalle = cursor.fetchall()
    conn.close()

    return {
        "cabecera": dict(cabecera),
        "detalle": [dict(d) for d in detalle]
    }


# ======================================================
# CERRAR INVENTARIO: aplica el stock real como el nuevo
# stock teórico de cada producto contado (REGULARIZACION),
# dejando trazabilidad en movimientos_stock igual que un
# ajuste manual normal.
# ======================================================
def cerrar_inventario(inventario_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT numero, estado FROM inventarios_fisicos WHERE id = ?
    """, (inventario_id,))

    inv = cursor.fetchone()

    if inv is None:
        conn.close()
        raise ValueError("Inventario no encontrado")

    if inv["estado"] == "CERRADO":
        conn.close()
        raise ValueError("Este inventario ya está cerrado")

    numero = inv["numero"]

    cursor.execute("""
        SELECT producto_codigo, stock_real, diferencia
        FROM inventario_fisico_detalle
        WHERE inventario_id = ? AND stock_real IS NOT NULL
    """, (inventario_id,))

    items = cursor.fetchall()
    conn.close()

    ajustados = 0

    for item in items:

        if item["diferencia"] == 0:
            continue  # sin diferencia, no hace falta tocar el stock

        ajustar_stock_manual(
            codigo=item["producto_codigo"],
            tipo="REGULARIZACION",
            cantidad=item["stock_real"],
            observacion=f"Cierre de inventario físico {numero}"
        )

        ajustados += 1

    conn2 = conectar()
    cursor2 = conn2.cursor()

    fecha_cierre = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor2.execute("""
        UPDATE inventarios_fisicos
        SET estado = 'CERRADO', fecha_cierre = ?
        WHERE id = ?
    """, (fecha_cierre, inventario_id))

    conn2.commit()
    conn2.close()

    return {"ajustados": ajustados, "numero": numero}