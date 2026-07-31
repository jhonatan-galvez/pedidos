from services.pedido_service import obtener_pedido_completo

from models.ticket import Ticket
from models.cliente_ticket import ClienteTicket
from models.producto_ticket import ProductoTicket

def generar_ticket(pedido_id):
    pedido = obtener_pedido_completo(pedido_id)

    if pedido is None:
        return None
    
    cliente = ClienteTicket(
        nombre=pedido["cliente"]["nombre"],
        telefono=pedido["cliente"]["telefono"],
        direccion=pedido["cliente"]["direccion"],
    )

    ticket = Ticket(
        numero_pedido=pedido["numero"],
        fecha=pedido["fecha"],
        cliente=cliente,
        subtotal=pedido["subtotal"],
        delivery=pedido["delivery"],
        descuento=pedido["descuento"],
        total=pedido["total"],
        estado=pedido["estado"],
        observaciones=pedido["observaciones"],
        tipo_pago=pedido["tipo_pago"]
    )

    for item in pedido["detalle"]:
        descripcion = " ".join(
            parte.strip()
            for parte in [
                item["producto"],
                item["marca"],
                item["presentacion"]
            ]
            if parte and parte.strip()
        )
        
        producto = ProductoTicket(
            producto=item["producto"],
            marca=item["marca"],
            presentacion=item["presentacion"],
            descripcion=descripcion,
            cantidad=item["cantidad"],
            precio_unitario=item["precio_unitario"],
            subtotal=item["subtotal"]
        )

        ticket.productos.append(producto)

    return ticket