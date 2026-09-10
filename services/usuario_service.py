from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from services.database_service import conectar


def obtener_usuarios():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.id, u.nombre_completo, u.usuario, u.activo,
               u.fecha_creacion, u.ultimo_acceso,
               p.id AS perfil_id, p.nombre AS perfil_nombre, p.es_admin
        FROM usuarios u
        LEFT JOIN perfiles p ON p.id = u.perfil_id
        ORDER BY u.id
    """)

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return rows


def obtener_usuario_por_id(usuario_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.*, p.nombre AS perfil_nombre, p.es_admin
        FROM usuarios u
        LEFT JOIN perfiles p ON p.id = u.perfil_id
        WHERE u.id = ?
    """, (usuario_id,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def obtener_usuario_por_login(usuario):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.*, p.nombre AS perfil_nombre, p.es_admin,
               p.puede_crear, p.puede_editar
        FROM usuarios u
        LEFT JOIN perfiles p ON p.id = u.perfil_id
        WHERE u.usuario = ?
    """, (usuario,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def verificar_login(usuario, password):

    user = obtener_usuario_por_login(usuario)

    if user is None:
        return None

    if not user["activo"]:
        return None

    if not check_password_hash(user["password_hash"], password):
        return None

    conn = conectar()
    cursor = conn.cursor()

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE usuarios SET ultimo_acceso = ? WHERE id = ?
    """, (fecha, user["id"]))

    conn.commit()
    conn.close()

    return user


def crear_usuario(nombre_completo, usuario, password, perfil_id,
                   pregunta_seguridad, respuesta_seguridad):

    conn = conectar()
    cursor = conn.cursor()

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:

        cursor.execute("""
            INSERT INTO usuarios
            (nombre_completo, usuario, password_hash, perfil_id,
             pregunta_seguridad, respuesta_seguridad_hash, activo, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (
            nombre_completo,
            usuario,
            generate_password_hash(password),
            perfil_id,
            pregunta_seguridad,
            generate_password_hash(respuesta_seguridad.strip().lower()),
            fecha
        ))

        conn.commit()

    except Exception as e:

        conn.rollback()
        raise ValueError("Ya existe un usuario con ese nombre de usuario") from e

    finally:

        conn.close()


def actualizar_usuario_admin(usuario_id, nombre_completo, perfil_id, activo):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET nombre_completo = ?, perfil_id = ?, activo = ?
        WHERE id = ?
    """, (nombre_completo, perfil_id, int(activo), usuario_id))

    conn.commit()
    conn.close()


def resetear_password_admin(usuario_id, password_nueva):
    """Un administrador restablece la contraseña de otro usuario
    (equivalente a un 'olvidé mi contraseña' resuelto por el dueño)."""

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE usuarios SET password_hash = ? WHERE id = ?
    """, (generate_password_hash(password_nueva), usuario_id))

    conn.commit()
    conn.close()


def cambiar_mi_password(usuario_id, password_actual, password_nueva):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT password_hash FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()

    if row is None or not check_password_hash(row["password_hash"], password_actual):
        conn.close()
        raise ValueError("La contraseña actual no es correcta")

    cursor.execute("""
        UPDATE usuarios SET password_hash = ? WHERE id = ?
    """, (generate_password_hash(password_nueva), usuario_id))

    conn.commit()
    conn.close()


def actualizar_mi_usuario(usuario_id, nombre_completo, usuario_login):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE usuarios SET nombre_completo = ?, usuario = ? WHERE id = ?
        """, (nombre_completo, usuario_login, usuario_id))

        conn.commit()

    except Exception as e:

        conn.rollback()
        raise ValueError("Ese nombre de usuario ya está en uso") from e

    finally:

        conn.close()


# ======================================================
# "OLVIDÉ MI CONTRASEÑA" — vía pregunta de seguridad
# (no hay email/SMS configurado; esta es la alternativa
# de autoservicio sin depender de un administrador)
# ======================================================
def obtener_pregunta_seguridad(usuario):

    user = obtener_usuario_por_login(usuario)

    if user is None or not user["activo"]:
        return None

    return user["pregunta_seguridad"]


def resetear_password_con_respuesta(usuario, respuesta, password_nueva):

    user = obtener_usuario_por_login(usuario)

    if user is None or not user["activo"]:
        raise ValueError("Usuario no encontrado")

    if not user["respuesta_seguridad_hash"]:
        raise ValueError("Este usuario no tiene una pregunta de seguridad configurada")

    if not check_password_hash(user["respuesta_seguridad_hash"], respuesta.strip().lower()):
        raise ValueError("La respuesta no es correcta")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE usuarios SET password_hash = ? WHERE id = ?
    """, (generate_password_hash(password_nueva), user["id"]))

    conn.commit()
    conn.close()


def actualizar_pregunta_seguridad(usuario_id, pregunta, respuesta):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET pregunta_seguridad = ?, respuesta_seguridad_hash = ?
        WHERE id = ?
    """, (pregunta, generate_password_hash(respuesta.strip().lower()), usuario_id))

    conn.commit()
    conn.close()
