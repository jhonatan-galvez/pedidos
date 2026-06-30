from services.database_service import conectar


# ======================================================
# GUARDAR LOG DE SINCRONIZACIÓN
# ======================================================
def guardar_log(
    productos_leidos,
    nuevos,
    actualizados,
    sin_cambios,
    desactivados,
    errores,
    duracion,
    fecha
):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sincronizaciones(

            fecha,

            productos_leidos,
            nuevos,
            actualizados,
            sin_cambios,
            desactivados,
            errores,
            duracion

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        fecha,

        productos_leidos,
        nuevos,
        actualizados,
        sin_cambios,
        desactivados,
        errores,
        duracion

    ))

    conn.commit()
    conn.close()


# ======================================================
# OBTENER ÚLTIMA SINCRONIZACIÓN
# ======================================================
def obtener_ultima_sincronizacion():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM sincronizaciones
        ORDER BY id DESC
        LIMIT 1
    """)

    resultado = cursor.fetchone()

    conn.close()

    return resultado


# ======================================================
# OBTENER HISTORIAL
# ======================================================
def obtener_historial(limit=20):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM sincronizaciones
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    historial = cursor.fetchall()

    conn.close()

    return historial