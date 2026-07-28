"""
Servicio de WhatsApp mejorado para enviar tickets y mensajes
"""

import requests
from config import Config
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {Config.WPP_TOKEN}",
    "Content-Type": "application/json"
}


def limpiar_numero(numero):
    """Limpia el número de teléfono"""
    return numero.replace("+", "").replace(" ", "").strip()


def enviar_mensaje(numero, mensaje):
    """Envía un mensaje de texto simple por WhatsApp"""
    try:
        numero = limpiar_numero(numero)
        
        payload = {
            "phone": numero,
            "message": mensaje
        }
        
        url = f"{Config.WPP_URL}/api/{Config.WPP_SESSION}/send-message"
        
        r = requests.post(
            url,
            json=payload,
            headers=HEADERS,
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
    Recibe un objeto Ticket con el método generar_ticket_pos()
    """
    try:
        numero = limpiar_numero(numero)
        
        # Generar contenido del ticket
        contenido = ticket.generar_ticket_whatsapp()
        
        # WhatsApp tiene límite de caracteres, así que usamos comillas
        # para mantener el formato monoespaciado
        mensaje = contenido
        
        payload = {
            "phone": numero,
            "message": mensaje
        }
        
        url = f"{Config.WPP_URL}/api/{Config.WPP_SESSION}/send-message"
        
        r = requests.post(
            url,
            json=payload,
            headers=HEADERS,
            timeout=30
        )
        
        if r.status_code not in (200, 201):
            raise Exception(r.text)
        
        logger.info(f"✓ Ticket {ticket.numero_pedido} enviado a {numero}")
        return r.json()
        
    except Exception as e:
        logger.error(f"✗ Error enviando ticket por WhatsApp: {str(e)}")
        raise


def enviar_confirmacion_pedido(numero, numero_pedido, total):
    """Envía confirmación de pedido recibido"""
    try:
        numero = limpiar_numero(numero)
        
        mensaje = f"""
Hola 👋

✓ Tu pedido ha sido recibido
📋 Número de pedido: {numero_pedido}
💰 Total: S/{total:.2f}

Te confirmaremos cuando esté listo para recoger o enviar.

¡Gracias por tu compra! 🙏
DOÑA FLORI
        """
        
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