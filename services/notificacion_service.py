import threading
import time
import random
import logging

from services.ticket_service import generar_ticket
from services.impresora_service import imprimir_ticket
from services.whatsapp_service import enviar_confirmacion_pedido
from services.pedido_service import obtener_pedido_completo

logger = logging.getLogger(__name__)


def iniciar_notificacion(pedido_id):
    """
    Inicia un proceso en segundo plano.
    """

    hilo = threading.Thread(
        target=procesar_notificacion,
        args=(pedido_id,),
        daemon=True
    )

    hilo.start()


def procesar_notificacion(pedido_id):
    """
    Ejecuta impresión y WhatsApp sin bloquear Flask.
    """

    try:

        pedido = obtener_pedido_completo(pedido_id)

        if pedido is None:
            logger.warning("Pedido no encontrado")
            return

        ticket = generar_ticket(pedido_id)

        # -----------------------------
        # IMPRIMIR
        # -----------------------------

        try:

            imprimir_ticket(ticket)

            logger.info(
                f"Ticket {pedido['numero']} impreso."
            )

        except Exception as e:

            logger.warning(
                f"No se pudo imprimir: {e}"
            )

        # -----------------------------
        # ESPERA NATURAL
        # -----------------------------

        espera = random.randint(5, 12)

        logger.info(
            f"Esperando {espera} segundos para enviar WhatsApp..."
        )

        time.sleep(espera)

        # -----------------------------
        # WHATSAPP
        # -----------------------------

        items_detalle = []

        for item in pedido["detalle"]:
            descripcion = (
                f"{item['producto']} x {item['cantidad']}"
            )
            items_detalle.append(descripcion)

        enviar_confirmacion_pedido(

            pedido["cliente"]["telefono"],
            pedido["numero"],
            pedido["total"],
            items_count=len(pedido["detalle"]),
            items_detalle=items_detalle,
            tipo_pago=pedido.get("tipo_pago", "No especificado")
        )

        logger.info(
            f"WhatsApp enviado para {pedido['numero']}"
        )

    except Exception as e:

        logger.exception(e)