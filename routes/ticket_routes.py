from flask import Blueprint, render_template

from services.ticket_service import generar_ticket

ticket_bp = Blueprint(
    "ticket",
    __name__
)


@ticket_bp.get("/admin/ticket/<int:pedido_id>")
def ver_ticket(pedido_id):

    ticket = generar_ticket(pedido_id)

    if ticket is None:
        return "Pedido no encontrado", 404

    return render_template(
        "admin/ticket_preview.html",
        ticket=ticket,
        pedido_id=pedido_id
    )