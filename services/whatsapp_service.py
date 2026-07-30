"""
Servicio de WhatsApp que conecta con servidor wpp-connect en puerto 21465
"""

import requests
import logging
import random

logger = logging.getLogger(__name__)

# URL del servidor wpp-connect
WHATSAPP_SERVER = "http://localhost:21465"


def limpiar_numero(numero):
    """
    Limpia y formatea el número de teléfono para wpp-connect
    Entrada: 927389769 (9 dígitos)
    Salida: 51927389769 (con código de país)
    """
    # Remover caracteres especiales
    numero = numero.replace("+", "").replace(" ", "").replace("-", "").strip()
    
    # Si tiene menos de 10 dígitos, agregar código de país Perú (51)
    if len(numero) == 9:
        numero = f"51{numero}"
    
    # Si ya tiene el código de país pero empieza con 0, remover el 0
    if numero.startswith("0"):
        numero = numero[1:]
    
    # Si tiene el código de país al inicio, asegurar que sea correcto
    if not numero.startswith("51") and len(numero) >= 9:
        numero = f"51{numero[-9:]}"
    
    return numero


def enviar_mensaje(numero, mensaje):
    """Envía un mensaje de texto simple por WhatsApp"""
    try:        
        numero = limpiar_numero(numero)
        
        payload = {
            "phone": numero,
            "message": mensaje
        }
        
        url = f"{WHATSAPP_SERVER}/api/pedidos/send-message"
        
        r = requests.post(
            url,
            json=payload,
            timeout=30
        )
        
        if r.status_code not in (200, 201):
            raise Exception(r.text)
        
        logger.info(f"✓ Mensaje enviado a {numero}")
        return r.json()
        
    except Exception as e:
        logger.error(f"✗ Error enviando mensaje: {str(e)}")
        raise


def enviar_ticket_por_whatsapp(numero, ticket):
    """
    Envía el ticket formateado por WhatsApp
    """
    try:
        numero = limpiar_numero(numero)
        
        # ✅ CAMBIO: Usar generar_ticket_whatsapp() en lugar de generar_ticket_pos()
        contenido = ticket.generar_ticket_whatsapp()
        
        mensaje = f"{contenido}"
        
        payload = {
            "phone": numero,
            "message": mensaje
        }
        
        url = f"{WHATSAPP_SERVER}/api/pedidos/send-message"
        
        r = requests.post(
            url,
            json=payload,
            timeout=30
        )
        
        if r.status_code not in (200, 201):
            raise Exception(r.text)
        
        logger.info(f"✓ Ticket {ticket.numero_pedido} enviado a {numero}")
        return r.json()
        
    except Exception as e:
        logger.error(f"✗ Error enviando ticket por WhatsApp: {str(e)}")
        raise

def obtener_plantilla_confirmacion(
        numero_pedido,
        total,
        items_count,
        detalle_productos
):

    plantillas = [

f"""*¡Pedido recibido!* 

Hola 👋
Hemos registrado correctamente tu pedido.
{detalle_productos}
📋 Pedido: *{numero_pedido}*
💰 Total: *S/ {total:.2f}*
🛍️ Productos: *{items_count or 'varios'}*

Muy pronto nos comunicaremos contigo para coordinar la entrega.

Gracias por confiar en *DOÑA FLORI* 💚
""",


f"""¡Gracias por comprar con nosotros! 😊

Tu pedido ya fue registrado.
{detalle_productos}
📦 Código:
*{numero_pedido}*

💵 Total:
*S/ {total:.2f}*

Nos comunicaremos contigo en breve para confirmar los detalles.
¡Que tengas un excelente día!

*DOÑA FLORI*
""",


f"""✅ Hemos recibido tu pedido.

Número:
*{numero_pedido}*
{detalle_productos}
Monto:
*S/ {total:.2f}*

Cantidad de productos:
*{items_count or 'varios'}*

En unos minutos confirmaremos la información contigo.

Muchas gracias por elegir *DOÑA FLORI*.
""",


f"""Hola 👋

Tu compra fue registrada correctamente.

📋 Pedido:
{numero_pedido}
{detalle_productos}
💰 Total:
S/ {total:.2f}

Nuestro equipo revisará el pedido y pronto se pondrá en contacto contigo.

¡Gracias por preferirnos! 🌸
*DOÑA FLORI*
""",


f"""🎉 ¡Excelente!

Ya tenemos tu pedido.

📋 Pedido:
{numero_pedido}
{detalle_productos}
💰 Total:
S/ {total:.2f}

🛒 Productos:
{items_count or 'varios'}

En breve confirmaremos la entrega.

Muchas gracias 😊
DOÑA FLORI
"""

    ]

    return random.choice(plantillas)

def enviar_confirmacion_pedido(numero, numero_pedido, total, items_count=None, items_detalle=None):
    """Envía confirmación simple de pedido recibido"""
    try:
        numero = limpiar_numero(numero)
        
        # Construir detalle de productos
        detalle_productos = ""
        if items_detalle:
            detalle_productos = "\n🛍️ *Tu pedido incluye:*\n"
            for item in items_detalle:
                detalle_productos += f"  ✓ {item}\n"

        logger.info(f"items_detalle: {items_detalle}")
        logger.info(f"detalle_productos:\n{detalle_productos}")
        
        mensaje = obtener_plantilla_confirmacion(
            numero_pedido,
            total,
            items_count,
            detalle_productos
        )
        
        return enviar_mensaje(numero, mensaje.strip())
        
    except Exception as e:
        logger.error(f"✗ Error enviando confirmación: {str(e)}")
        raise


def enviar_pedido_listo(numero, numero_pedido):
    """Notifica que el pedido está listo"""
    try:
        numero = limpiar_numero(numero)
        
        mensaje = f"""
Hola 👋

✓ Tu pedido está LISTO
📋 Número: {numero_pedido}

Ya puedes pasar a recogerlo.
¡Gracias! 🙏
DOÑA FLORI
        """
        
        return enviar_mensaje(numero, mensaje.strip())
        
    except Exception as e:
        logger.error(f"✗ Error enviando notificación: {str(e)}")
        raise