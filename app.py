from services.producto_service import actualizar_imagen_producto
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openpyxl import Workbook
from openpyxl.styles import Font
from io import BytesIO

from services.database_service import inicializar_database
from services.database_service import conectar
from services.producto_service import obtener_productos, obtener_admproductos
from services.sync_service import sincronizar_productos
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER, EXCEL_NAME
from services.sync_log_service import (obtener_ultima_sincronizacion,
    obtener_historial)
from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import zipfile
from flask import send_file
from services.cloudinary_service import subir_imagen

from services.ticket_service import generar_ticket, Ticket
from routes.ticket_routes import ticket_bp
from services.impresora_service import imprimir_ticket
from services.notificacion_service import iniciar_notificacion
import logging
from services.whatsapp_service import enviar_confirmacion_pedido
from services.producto_service import actualizar_producto, obtener_admproductos
from services.cliente_service import obtener_clientes, actualizar_cliente_admin, obtener_cliente_por_id
from services.pedido_service import (
    crear_pedido,
    obtener_pedidos,
    obtener_pedido_completo,
    actualizar_estado_pedido,
    obtener_dashboard,
    actualizar_pedido,
    obtener_pedidos_cliente,
    obtener_reporte_ventas,
    obtener_ventas_por_producto
)



logger = logging.getLogger(__name__)




BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PRODUCT_IMAGE_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "img",
    "productos"
)

load_dotenv()

app = Flask(__name__)
app.register_blueprint(ticket_bp)
inicializar_database()

####################################
# SITIO PUBLICO - CLIENTE
####################################
@app.get("/")
def index():

    carpeta = os.path.join(
        app.static_folder,
        "img",
        "banners"
    )

    banners = []

    if os.path.exists(carpeta):

        banners = sorted([

            archivo

            for archivo in os.listdir(carpeta)

            if archivo.lower().endswith(
                (".jpg", ".jpeg", ".png", ".webp")
            )

        ])

    return render_template(

        "index.html",

        banners=banners

    )


@app.route("/catalogo")
def catalogo():
    productos = obtener_productos()
    return render_template("catalogo.html", productos=productos)

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")


@app.route("/admin/productos/imagen/<int:id>", methods=["GET","POST"])
def imagen_producto(id):

    if request.method == "POST":

        archivo = request.files.get("imagen")

        if archivo:

            url_imagen = subir_imagen(archivo)

            actualizar_imagen_producto(
                id,
                url_imagen
            )

            return redirect("/admin/productos")


    return render_template(
        "admin/imagen_producto.html",
        id=id
    )

@app.route("/admin/backup-imagenes")
def backup_imagenes():

    carpeta = PRODUCT_IMAGE_FOLDER

    if not os.path.exists(carpeta):
        return "La carpeta de imágenes no existe."

    zip_path = os.path.join(BASE_DIR, "backup_imagenes.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:

        for archivo in os.listdir(carpeta):

            ruta = os.path.join(carpeta, archivo)

            if os.path.isfile(ruta):

                zipf.write(
                    ruta,
                    arcname=archivo
                )

    return send_file(
        zip_path,
        as_attachment=True,
        download_name="backup_imagenes.zip"
    )

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

    nombre = secure_filename(EXCEL_NAME)

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

@app.post("/api/ticket/<int:pedido_id>")
def api_generar_ticket(pedido_id):
    """Genera un ticket en objeto para usarlo internamente"""
    try:
        ticket = generar_ticket(pedido_id)
        
        if ticket is None:
            return jsonify({
                "ok": False,
                "error": "Pedido no encontrado"
            }), 404
        
        return jsonify({
            "ok": True,
            "numero_pedido": ticket.numero_pedido,
            "contenido": ticket.generar_ticket_pos()
        })
        
    except Exception as e:
        logger.error(f"Error generando ticket: {str(e)}")
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.post("/admin/ticket/<int:pedido_id>/imprimir")
def imprimir_ticket_route(pedido_id):
    """Imprime el ticket en la Epson T20II"""
    try:
        ticket = generar_ticket(pedido_id)
        
        if ticket is None:
            return jsonify({
                "ok": False,
                "error": "Pedido no encontrado"
            }), 404
        
        exito = imprimir_ticket(ticket)
        
        if exito:
            return jsonify({
                "ok": True,
                "mensaje": f"Ticket {ticket.numero_pedido} impreso"
            })
        else:
            return jsonify({
                "ok": False,
                "error": "No se pudo imprimir el ticket (impresora no disponible)"
            }), 500
            
    except Exception as e:
        logger.error(f"Error imprimiendo: {str(e)}")
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

@app.post("/admin/ticket/<int:pedido_id>/whatsapp")
def enviar_ticket_whatsapp(pedido_id):
    """Envía el ticket por WhatsApp desde admin"""
    try:
        pedido = obtener_pedido_completo(pedido_id)
        
        if pedido is None:
            return jsonify({
                "ok": False,
                "error": "Pedido no encontrado"
            }), 404
        
        ticket = generar_ticket(pedido_id)
        numero = pedido["cliente"]["telefono"]
        
        # Construir items
        items_detalle = [
            f"{item['producto']} x {item['cantidad']}"
            for item in pedido["detalle"]
        ]
        
        # ✅ USAR CONFIRMACIÓN (no ticket)
        try:
            enviar_confirmacion_pedido(
                numero,
                pedido["numero"],
                pedido["total"],
                items_count=len(pedido["detalle"]),
                items_detalle=items_detalle,
                tipo_pago=pedido.get("tipo_pago", "No especificado")
            )
            return jsonify({
                "ok": True,
                "mensaje": f"Confirmación enviada a {numero}"
            })
        except Exception as e:
            return jsonify({
                "ok": False,
                "error": f"No se pudo enviar: {str(e)}"
            }), 500
        
    except Exception as e:
        logger.error(f"Error enviando WhatsApp: {str(e)}")
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

@app.route("/admin/ticket/<int:pedido_id>")
def ticket_preview(pedido_id):

    pedido = obtener_pedido_completo(pedido_id)

    ticket = generar_ticket(pedido_id)

    return render_template(
        "admin/ticket_preview.html",
        ticket=ticket,
        pedido_id=pedido_id
    )

@app.post("/crear_pedido")
def crear_pedido_route():
    datos = request.get_json()
    datos_cliente = datos["cliente"]
    carrito = datos["carrito"]

    try:
        pedido_id = crear_pedido(datos_cliente, carrito)

        pedido = obtener_pedido_completo(pedido_id)

        # Ejecutar impresión + WhatsApp en segundo plano
        iniciar_notificacion(pedido_id) 
               
        return jsonify({
            "ok": True,
            "pedido_id": pedido_id,
            "numero": pedido["numero"],
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/admin/productos/editar/<int:id>", methods=["GET","POST"])
def editar_producto(id):

    productos = obtener_admproductos()

    producto = next(
        (
            p for p in productos
            if p["id"] == id
        ),
        None
    )


    if producto is None:
        return "Producto no encontrado", 404


    if request.method == "POST":

        actualizar_producto(
            id,
            request.form["producto"],
            request.form["marca"],
            request.form["tipo"],
            request.form["presentacion"],
            request.form["stock"],
            request.form["precio"]
        )

        return redirect("/admin/productos")


    return render_template(
        "admin/editar_producto.html",
        producto=producto
    )

@app.route("/admin/clientes")
def admin_clientes():

    clientes = obtener_clientes()

    return render_template(
        "admin/clientes.html",
        clientes=clientes
    )

@app.route(
    "/admin/clientes/editar/<int:id>",
    methods=["GET","POST"]
)

def editar_cliente(id):

    cliente = obtener_cliente_por_id(id)


    if request.method == "POST":

        actualizar_cliente_admin(
            id,
            request.form["nombre"],
            request.form["telefono"],
            request.form["direccion"],
            request.form["referencia"]
        )

        return redirect("/admin/clientes")



    return render_template(
        "admin/editar_cliente.html",
        cliente=cliente
    )

def pedidos_cliente(id):

    cliente = obtener_cliente_por_id(id)

    pedidos = obtener_pedidos_cliente(id)


    return render_template(
        "admin/pedidos_cliente.html",
        cliente=cliente,
        pedidos=pedidos
    )

@app.route("/admin/clientes/<int:id>/pedidos")
def pedidos_cliente(id):

    cliente = obtener_cliente_por_id(id)

    pedidos = obtener_pedidos_cliente(id)


    return render_template(
        "admin/pedidos_cliente.html",
        cliente=cliente,
        pedidos=pedidos
    )

@app.route("/admin/pedido/<int:id>/editar", methods=["GET","POST"])
def editar_pedido(id):

    pedido = obtener_pedido_completo(id)

    if pedido is None:
        return "Pedido no encontrado"


    if request.method == "POST":

        datos = {

            "tipo_pago": request.form["tipo_pago"],
            "direccion": request.form["direccion"],
            "observaciones": request.form["observaciones"]

        }


        actualizar_pedido(
            id,
            datos
        )


        return redirect(
            f"/admin/pedido/{id}"
        )


    return render_template(
        "admin/editar_pedido.html",
        pedido=pedido
    )

# ======================================================
# REPORTE DE VENTAS
# ======================================================

@app.route("/admin/reporte-ventas")
def reporte_ventas():

    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    reporte = obtener_reporte_ventas(
        desde=desde,
        hasta=hasta
    )

    return render_template(
        "admin/reporte_ventas.html",
        reporte=reporte,
        desde=desde,
        hasta=hasta
    )


# ======================================================
# DESCARGAR REPORTE DE VENTAS EXCEL
# ======================================================

@app.route("/admin/reporte-ventas/descargar")
def descargar_reporte_ventas():

    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    reporte = obtener_reporte_ventas(
        desde=desde,
        hasta=hasta
    )

    # ======================================================
    # CREAR LIBRO
    # ======================================================

    wb = Workbook()

    ws = wb.active
    ws.title = "Ventas"

    # ======================================================
    # ENCABEZADOS
    # ======================================================

    encabezados = [
        "Pedido",
        "Fecha",
        "Estado",
        "Tipo de pago",
        "Cliente",
        "Teléfono",
        "Código",
        "Producto",
        "Marca",
        "Presentación",
        "Cantidad",
        "Precio unitario",
        "Importe"
    ]

    ws.append(encabezados)

    # Encabezados en negrita
    for celda in ws[1]:
        celda.font = Font(bold=True)

    # ======================================================
    # DATOS
    # ======================================================

    for item in reporte:

        ws.append([
            str(item.get("numero_pedido") or ""),
            str(item.get("fecha") or ""),
            str(item.get("estado") or ""),
            str(item.get("tipo_pago") or ""),
            str(item.get("cliente") or ""),
            str(item.get("telefono") or ""),
            str(item.get("codigo") or ""),
            str(item.get("producto") or ""),
            str(item.get("marca") or ""),
            str(item.get("presentacion") or ""),
            float(item.get("cantidad") or 0),
            float(item.get("precio_unitario") or 0),
            float(item.get("importe") or 0)
        ])

    # ======================================================
    # FORMATO DE COLUMNAS
    # ======================================================

    anchos = {
        "A": 16,
        "B": 20,
        "C": 15,
        "D": 18,
        "E": 30,
        "F": 15,
        "G": 15,
        "H": 30,
        "I": 20,
        "J": 20,
        "K": 12,
        "L": 18,
        "M": 18
    }

    for columna, ancho in anchos.items():
        ws.column_dimensions[columna].width = ancho

    # ======================================================
    # FORMATO MONEDA
    # ======================================================

    for fila in range(2, ws.max_row + 1):

        ws[f"L{fila}"].number_format = '"S/" #,##0.00'
        ws[f"M{fila}"].number_format = '"S/" #,##0.00'

    # ======================================================
    # FORMATO GENERAL
    # ======================================================

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    # ======================================================
    # GUARDAR EN MEMORIA
    # ======================================================

    archivo = BytesIO()

    wb.save(archivo)

    archivo.seek(0)

    # ======================================================
    # VALIDAR QUE EL XLSX SE PUEDA ABRIR
    # ======================================================

    try:

        from openpyxl import load_workbook

        archivo_prueba = BytesIO(archivo.getvalue())

        libro_prueba = load_workbook(
            archivo_prueba,
            read_only=True
        )

        libro_prueba.close()

        archivo.seek(0)

    except Exception as e:

        logger.error(
            f"Error validando reporte Excel: {str(e)}"
        )

        return jsonify({
            "ok": False,
            "error": "El archivo Excel generado no es válido.",
            "detalle": str(e)
        }), 500

    # ======================================================
    # NOMBRE DEL ARCHIVO
    # ======================================================

    nombre = "reporte_ventas"

    if desde and hasta:
        nombre += f"_{desde}_a_{hasta}"

    nombre += ".xlsx"

    # ======================================================
    # DESCARGA
    # ======================================================

    return send_file(
        archivo,
        as_attachment=True,
        download_name=nombre,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ======================================================
# REPORTE - VENTAS POR PRODUCTO
# ======================================================

@app.route("/admin/reporte-productos")
def reporte_productos():

    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    ventas = obtener_ventas_por_producto(
        desde=desde,
        hasta=hasta
    )

    return render_template(
        "admin/reporte_productos.html",
        ventas=ventas,
        desde=desde,
        hasta=hasta
    )

# ======================================================
# DESCARGAR REPORTE DE VENTAS POR PRODUCTO EN EXCEL
# ======================================================

@app.route("/admin/reporte-productos/excel")
def descargar_reporte_productos():

    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    ventas = obtener_ventas_por_producto(
        desde=desde,
        hasta=hasta
    )

    import pandas as pd
    from io import BytesIO

    datos = []

    for item in ventas:

        datos.append({

            "Código": item["codigo"],
            "Producto": item["producto"],
            "Marca": item["marca"],
            "Presentación": item["presentacion"],
            "Cantidad vendida": item["cantidad"],
            "Importe total": item["importe"]

        })

    df = pd.DataFrame(datos)

    archivo = BytesIO()

    with pd.ExcelWriter(
        archivo,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Ventas por Producto"
        )

    archivo.seek(0)

    return send_file(
        archivo,
        as_attachment=True,
        download_name="reporte_ventas_por_producto.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )





#ticket = generar_ticket(4)
#print(ticket.productos)
#print(ticket.generar_ticket_pos())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)