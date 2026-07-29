import win32print
import logging
from PIL import Image
import os

logger = logging.getLogger(__name__)

# Nombre EXACTO de la impresora instalada en Windows
PRINTER_NAME = "EPSON TM-T20 ReceiptE4"


class PrinterService:

    @staticmethod
    def imprimir_ticket(ticket):
        """
        Imprime un ticket utilizando la cola de impresión de Windows.
        """

        try:
            contenido = ticket.generar_ticket_pos()

            hPrinter = win32print.OpenPrinter(PRINTER_NAME)

            try:
                win32print.StartDocPrinter(
                    hPrinter,
                    1,
                    ("Pedido " + str(ticket.numero_pedido), None, "RAW")
                )

                win32print.StartPagePrinter(hPrinter)
                #PrinterService.imprimir_logo(hPrinter)

                # Inicializar impresora
                win32print.WritePrinter(hPrinter, b"\x1B\x40")

                # Seleccionar página de códigos 16
                win32print.WritePrinter(hPrinter, b"\x1B\x74\x10")

                # Imprimir contenido
                win32print.WritePrinter(
                    hPrinter,
                    contenido.encode("cp1252", errors="replace")
                )

                # Alimentar papel
                win32print.WritePrinter(hPrinter, b"\n\n\n\n\n\n")

                # Corte total
                win32print.WritePrinter(hPrinter, b"\x1D\x56\x00")

                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)

            finally:
                win32print.ClosePrinter(hPrinter)

            logger.info(f"✓ Ticket {ticket.numero_pedido} impreso correctamente")
            return True

        except Exception:
            logger.exception("Error imprimiendo ticket")
            return False

    @staticmethod
    def imprimir_logo(hPrinter):
        """
        Imprime el logo de la empresa.
        """
        try:
            ruta_logo = os.path.join(
                os.getcwd(),
                "static",
                "img",
                "logo.png"      # <-- cambia el nombre si tu logo tiene otro nombre
            )

            img = Image.open(ruta_logo)

            # Convertir a blanco y negro
            img = img.convert("1")

            # Ancho máximo para TM-T20II 58mm
            ancho = 384

            w, h = img.size
            alto = int(h * (ancho / w))

            img = img.resize((ancho, alto))

            # Guardar temporalmente en formato BMP monocromo
            temp = os.path.join(os.getcwd(), "logo.bmp")
            img.save(temp)

            # ESC * NO soporta BMP directamente.
            # Esta función queda preparada para el siguiente paso.
            logger.info("Logo preparado correctamente.")

        except Exception:
            logger.exception("No fue posible cargar el logo.")    

def imprimir_ticket(ticket):
    return PrinterService.imprimir_ticket(ticket)