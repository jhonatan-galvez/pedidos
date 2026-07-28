from dataclasses import dataclass, field
from typing import List
from .cliente_ticket import ClienteTicket
from .producto_ticket import ProductoTicket


@dataclass
class Ticket:
    numero_pedido: str
    fecha: str
    cliente: ClienteTicket
    productos: List[ProductoTicket] = field(default_factory=list)
    subtotal: float = 0
    delivery: float = 0
    descuento: float = 0
    total: float = 0
    estado: str = ""
    observaciones: str = ""

    def generar_ticket_pos(self):
        lineas = []

        lineas.append("=" * 40)
        lineas.append("          DOÑA FLORI")
        lineas.append("=" * 40)
        lineas.append("")

        lineas.append(f"Pedido : {self.numero_pedido}")
        lineas.append(f"Fecha  : {self.fecha}")
        lineas.append("")

        lineas.append(f"Cliente: {self.cliente.nombre}")
        lineas.append(f"Teléfono: {self.cliente.telefono}")
        lineas.append("")

        lineas.append("-" * 40)

        for producto in self.productos:
            lineas.append(producto.descripcion)
            linea = (
                f"{producto.cantidad} x "
                f"S/{producto.precio_unitario:.2f}"
            )
            subtotal = f"S/{producto.subtotal:.2f}"
            lineas.append(
                f"{linea:<20}{subtotal:>20}"
            )
            lineas.append("")

        lineas.append("-" * 40)
        lineas.append(
            f"Subtotal{'':<16}S/{self.subtotal:.2f}"
        )
        lineas.append(
            f"Delivery{'':<16}S/{self.delivery:.2f}"
        )
        lineas.append(
            f"Descuento{'':<15}S/{self.descuento:.2f}"
        )
        lineas.append("")
        lineas.append(
            f"TOTAL{'':<20}S/{self.total:.2f}"
        )
        lineas.append("")
        lineas.append("=" * 40)
        lineas.append("Gracias por su compra")
        lineas.append("=" * 40)
        return "\n".join(lineas)

    def generar_ticket_whatsapp(self):

        lineas = []

        lineas.append("🛒 *NUEVO PEDIDO*")
        lineas.append("")

        lineas.append(f"📋 *Pedido:* {self.numero_pedido}")
        lineas.append(f"📅 *Fecha:* {self.fecha}")
        lineas.append("")

        lineas.append("👤 *Cliente*")
        lineas.append(self.cliente.nombre)
        lineas.append("")

        lineas.append(f"📱 {self.cliente.telefono}")

        if self.cliente.direccion:
            lineas.append(f"📍 {self.cliente.direccion}")

        lineas.append("")
        lineas.append("━━━━━━━━━━━━━━━━━━━━")

        for producto in self.productos:

            lineas.append(f"• {producto.descripcion}")

            lineas.append(
                f"   {producto.cantidad} × S/{producto.precio_unitario:.2f}"
                f" = S/{producto.subtotal:.2f}"
            )

            lineas.append("")

        lineas.append("━━━━━━━━━━━━━━━━━━━━")

        lineas.append(f"Subtotal : S/{self.subtotal:.2f}")
        lineas.append(f"Delivery : S/{self.delivery:.2f}")
        lineas.append(f"Descuento: S/{self.descuento:.2f}")

        lineas.append("")
        lineas.append(f"💰 *TOTAL: S/{self.total:.2f}*")

        if self.observaciones:

            lineas.append("")
            lineas.append("📝 Observaciones:")
            lineas.append(self.observaciones)

        return "\n".join(lineas)