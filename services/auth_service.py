from functools import wraps
from flask import session, redirect, url_for, request, render_template


def usuario_actual():
    """Devuelve el dict del usuario en sesión, o None si no hay sesión."""

    if "usuario_id" not in session:
        return None

    return {
        "id": session["usuario_id"],
        "nombre_completo": session.get("nombre_completo"),
        "usuario": session.get("usuario_login"),
        "perfil_nombre": session.get("perfil_nombre"),
        "es_admin": session.get("es_admin", False),
        "puede_crear": session.get("puede_crear", False),
        "puede_editar": session.get("puede_editar", False),
    }


def iniciar_sesion(user):

    session["usuario_id"] = user["id"]
    session["nombre_completo"] = user["nombre_completo"]
    session["usuario_login"] = user["usuario"]
    session["perfil_nombre"] = user["perfil_nombre"]
    session["es_admin"] = bool(user["es_admin"])
    session["puede_crear"] = bool(user["puede_crear"])
    session["puede_editar"] = bool(user["puede_editar"])


def cerrar_sesion():
    session.clear()


def login_required(f):

    @wraps(f)
    def envoltura(*args, **kwargs):

        if "usuario_id" not in session:
            return redirect(url_for("login", next=request.path))

        return f(*args, **kwargs)

    return envoltura


def admin_required(f):

    @wraps(f)
    def envoltura(*args, **kwargs):

        if "usuario_id" not in session:
            return redirect(url_for("login", next=request.path))

        if not session.get("es_admin"):
            return render_template(
                "admin/sin_permiso.html",
                mensaje="Esta sección es solo para el perfil Administrador."
            ), 403

        return f(*args, **kwargs)

    return envoltura


def permiso_requerido(permiso):
    """permiso: 'puede_crear' o 'puede_editar'. El admin siempre tiene acceso."""

    def decorador(f):

        @wraps(f)
        def envoltura(*args, **kwargs):

            if "usuario_id" not in session:
                return redirect(url_for("login", next=request.path))

            if not session.get("es_admin") and not session.get(permiso):
                return render_template(
                    "admin/sin_permiso.html",
                    mensaje="Tu perfil no tiene permiso para realizar esta acción."
                ), 403

            return f(*args, **kwargs)

        return envoltura

    return decorador
