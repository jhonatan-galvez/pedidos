from services.database_service import conectar


def buscar_cliente_por_telefono(cursor, telefono):
    """
    Busca un cliente usando el cursor recibido.
    No abre ni cierra conexiones.
    """

    cursor.execute("""
        SELECT *
        FROM clientes
        WHERE telefono = ?
    """, (telefono,))

    return cursor.fetchone()


def crear_cliente(cursor, nombre, telefono, direccion, referencia):
    """
    Inserta un cliente y devuelve su ID.
    """

    cursor.execute("""
        INSERT INTO clientes
        (
            nombre,
            telefono,
            direccion,
            referencia
        )
        VALUES (?, ?, ?, ?)
    """, (
        nombre,
        telefono,
        direccion,
        referencia
    ))

    return cursor.lastrowid


def actualizar_cliente(cursor, id_cliente, nombre, direccion, referencia):
    """
    Actualiza los datos del cliente.
    """

    cursor.execute("""
        UPDATE clientes
        SET
            nombre = ?,
            direccion = ?,
            referencia = ?
        WHERE id = ?
    """, (
        nombre,
        direccion,
        referencia,
        id_cliente
    ))


# -------------------------------------------------------------------
# Estas funciones siguen siendo útiles cuando solamente quieres consultar
# un cliente desde otra parte del sistema.
# -------------------------------------------------------------------

def obtener_cliente(id_cliente):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM clientes
        WHERE id = ?
    """, (id_cliente,))

    cliente = cursor.fetchone()

    conn.close()

    return cliente


def obtener_cliente_por_telefono(telefono):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM clientes
        WHERE telefono = ?
    """, (telefono,))

    cliente = cursor.fetchone()

    conn.close()

    return cliente

from services.database_service import conectar


def obtener_clientes():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.id,
            c.nombre,
            c.telefono,
            c.direccion,
            c.referencia,

            COUNT(p.id) AS pedidos

        FROM clientes c

        LEFT JOIN pedidos p
            ON p.cliente_id = c.id

        GROUP BY c.id

        ORDER BY c.id DESC

    """)

    rows = cursor.fetchall()

    conn.close()


    clientes = []

    for r in rows:

        clientes.append({

            "id": r["id"],
            "nombre": r["nombre"],
            "telefono": r["telefono"],
            "direccion": r["direccion"],
            "referencia": r["referencia"],
            "pedidos": r["pedidos"]

        })


    return clientes

def obtener_cliente_por_id(id):

    conn = conectar()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            id,
            nombre,
            telefono,
            direccion,
            referencia

        FROM clientes

        WHERE id = ?

    """, (id,))


    row = cursor.fetchone()

    conn.close()


    if row:

        return dict(row)

    return None

def actualizar_cliente_admin(
        id,
        nombre,
        telefono,
        direccion,
        referencia):

    conn = conectar()
    cursor = conn.cursor()


    cursor.execute("""
        UPDATE clientes

        SET
            nombre=?,
            telefono=?,
            direccion=?,
            referencia=?

        WHERE id=?

    """,
    (
        nombre,
        telefono,
        direccion,
        referencia,
        id
    ))


    conn.commit()
    conn.close()

