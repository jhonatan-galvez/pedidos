from datetime import datetime
from services.database_service import conectar


def obtener_perfiles():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.*, COUNT(u.id) AS usuarios
        FROM perfiles p
        LEFT JOIN usuarios u ON u.perfil_id = p.id
        GROUP BY p.id
        ORDER BY p.es_admin DESC, p.nombre
    """)

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return rows


def obtener_perfil_por_id(perfil_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM perfiles WHERE id = ?", (perfil_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def crear_perfil(nombre, puede_crear, puede_editar):

    conn = conectar()
    cursor = conn.cursor()

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:

        cursor.execute("""
            INSERT INTO perfiles (nombre, puede_crear, puede_editar, es_admin, sistema, fecha_creacion)
            VALUES (?, ?, ?, 0, 0, ?)
        """, (nombre, int(puede_crear), int(puede_editar), fecha))

        conn.commit()

    except Exception as e:

        conn.rollback()
        raise ValueError("Ya existe un perfil con ese nombre") from e

    finally:

        conn.close()


def actualizar_perfil(perfil_id, nombre, puede_crear, puede_editar):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT sistema FROM perfiles WHERE id = ?", (perfil_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        raise ValueError("Perfil no encontrado")

    if row["sistema"]:
        conn.close()
        raise ValueError("Este perfil es del sistema y no se puede modificar")

    cursor.execute("""
        UPDATE perfiles
        SET nombre = ?, puede_crear = ?, puede_editar = ?
        WHERE id = ?
    """, (nombre, int(puede_crear), int(puede_editar), perfil_id))

    conn.commit()
    conn.close()


def eliminar_perfil(perfil_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT sistema FROM perfiles WHERE id = ?", (perfil_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        raise ValueError("Perfil no encontrado")

    if row["sistema"]:
        conn.close()
        raise ValueError("Este perfil es del sistema y no se puede eliminar")

    cursor.execute("SELECT COUNT(*) AS n FROM usuarios WHERE perfil_id = ?", (perfil_id,))

    if cursor.fetchone()["n"] > 0:
        conn.close()
        raise ValueError("No se puede eliminar: hay usuarios con este perfil")

    cursor.execute("DELETE FROM perfiles WHERE id = ?", (perfil_id,))
    conn.commit()
    conn.close()
