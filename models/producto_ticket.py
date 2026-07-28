from dataclasses import dataclass


@dataclass
class ProductoTicket:
    producto: str
    marca: str
    presentacion: str
    descripcion: str
    cantidad: int
    precio_unitario: float
    subtotal: float