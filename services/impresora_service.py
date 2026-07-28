"""
Servicio para imprimir tickets en impresora Epson T20II
Requiere: pip install python-escpos
"""

from escpos.printer import Usb
from config import Config
import logging

logger = logging.getLogger(__name__)

# Configuración de la impresora Epson T20II
VENDOR_ID = 0x04b8  # Epson
PRODUCT_ID = 0x0202  # T20II

class PrinterService:
    _printer = None
    
    @staticmethod
    def conectar_impresora():
        """Conecta con la impresora Epson T20II por USB"""
        try:
            printer = Usb(
                idVendor=VENDOR_ID,
                idProduct=PRODUCT_ID,
                timeout=3
            )
            PrinterService._printer = printer
            logger.info("✓ Impresora conectada exitosamente")
            return printer
        except Exception as e:
            logger.error(f"✗ Error conectando impresora: {str(e)}")
            return None
    
    @staticmethod
    def obtener_impresora():
        """Obtiene la instancia de la impresora, conectando si es necesario"""
        if PrinterService._printer is None:
            PrinterService.conectar_impresora()
        return PrinterService._printer
    
    @staticmethod
    def imprimir_ticket(ticket):
        """
        Imprime un ticket en la Epson T20II
        Recibe un objeto Ticket con el método generar_ticket_pos()
        """
        try:
            printer = PrinterService.obtener_impresora()
            
            if printer is None:
                logger.warning("Impresora no disponible, abortando impresión")
                return False
            
            # Generar contenido del ticket
            contenido = ticket.generar_ticket_pos()
            
            # Configurar impresora
            printer.set(align='center')

            printer.text(contenido)
            # Imprimir línea por línea
            #for linea in contenido.split('\n'):
            #    printer.text(linea + '\n')
            
            # Corte de papel
            printer.cut()

            printer.text("\n\n")
            # Cerrar conexión
            #printer.close()
            PrinterService._printer = None
            
            logger.info(f"✓ Ticket {ticket.numero_pedido} impreso correctamente")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error imprimiendo ticket: {str(e)}")
            return False


def imprimir_ticket(ticket):
    """Función simplificada para imprimir"""
    return PrinterService.imprimir_ticket(ticket)