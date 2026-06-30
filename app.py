from services.database_service import inicializar_database
from services.producto_service import obtener_productos, obtener_admproductos
from services.pedido_service import crear_pedido, obtener_pedidos, obtener_pedido_completo, actualizar_estado_pedido, obtener_dashboard
from services.sync_service import sincronizar_productos
from werkzeug.utils import secure_filename
from services.sync_log_service import (
    obtener_ultima_sincronizacion,
    obtener_historial
)
from flask import Flask, render_template, request, jsonify, redirect, url_for
import os

UPLOAD_FOLDER = "upload"

app = Flask(__name__)
inicializar_database()

####################################
# SITIO PUBLICO - CLIENTE
####################################
@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/catalogo")
def catalogo():
    productos = obtener_productos()
    return render_template("catalogo.html", productos=productos)

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")

@app.post("/crear_pedido")
def crear_pedido_route():

    datos = request.get_json()

    datos_cliente = datos["cliente"]
    carrito = datos["carrito"]

    try:

        numero = crear_pedido(datos_cliente, carrito)
        return jsonify({
            "ok": True,
            "numero": numero
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500



'''@app.route("/pedidos", methods=["GET"])
def listar_pedidos():
    return jsonify(get_pedidos())

@app.route("/pedido/<int:id>", methods=["GET"])
def ver_pedido(id):
    return jsonify(get_pedido_completo(id))'''

####################################
# SITIO ADM - ADMINISTRADOR
####################################
@app.route("/admin")
def admin():
    return redirect(url_for("admin_pedidos"))

@app.route("/admin/pedidos")
def admin_pedidos():

    buscar = request.args.get("buscar")
    estado = request.args.get("estado")
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    pedidos = obtener_pedidos(
        buscar=buscar,
        estado=estado,
        desde=desde,
        hasta=hasta
    )

    return render_template(
        "admin/pedidos.html",
        pedidos=pedidos,
        buscar=buscar,
        estado=estado,
        desde=desde,
        hasta=hasta
    )

@app.route("/admin/pedido/<int:pedido_id>")
def admin_detalle_pedido(pedido_id):

    pedido = obtener_pedido_completo(pedido_id)

    return render_template(
        "admin/detalle_pedido.html",
        pedido=pedido
    )

@app.route("/admin/pedido/<int:pedido_id>/estado", methods=["POST"])
def cambiar_estado(pedido_id):

    estado = request.form.get("estado")

    actualizar_estado_pedido(pedido_id, estado)

    return redirect("/admin/pedidos")

@app.route("/admin/dashboard")
def dashboard():

    data = obtener_dashboard()

    return render_template(
        "admin/dashboard.html",
        data=data
    )

@app.route("/admin/productos")
def admin_productos():

    productos = obtener_admproductos()

    return render_template(
        "admin/productos.html",
        productos=productos
    )

@app.route("/admin/sincronizacion")
def admin_sincronizacion():

    return render_template(

        "admin/sincronizacion.html",

        ultima=obtener_ultima_sincronizacion(),

        historial=obtener_historial()

    )

@app.post("/admin/sincronizar")
def ejecutar_sincronizacion():

    resultado = sincronizar_productos()

    return jsonify(resultado)

@app.post("/admin/upload_excel")
def upload_excel():

    archivo = request.files.get("archivo")

    if archivo is None or archivo.filename == "":
        return jsonify({
            "ok": False,
            "mensaje": "No se seleccionó ningún archivo."
        }), 400

    if not archivo.filename.lower().endswith(".xlsx"):
        return jsonify({
            "ok": False,
            "mensaje": "Solo se permiten archivos .xlsx"
        }), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    nombre = secure_filename("productos.xlsx")

    ruta = os.path.join(UPLOAD_FOLDER, nombre)

    archivo.save(ruta)

    resultado = sincronizar_productos()

    return jsonify({
        "ok": True,
        "mensaje": "Catálogo actualizado correctamente.",
        "resultado": resultado
    })

#if __name__ == "__main__":
#    inicializar_database()
#    app.run(debug=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)