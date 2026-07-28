import win32print
import logging

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

                # Texto
                win32print.WritePrinter(
                    hPrinter,
                    contenido.encode("cp858", errors="replace")
                )

                # Alimentar papel
                win32print.WritePrinter(hPrinter, b"\n\n\n\n\n\n")

                # Corte
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


def imprimir_ticket(ticket):
    return PrinterService.imprimir_ticket(ticket)