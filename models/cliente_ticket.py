from dataclasses import dataclass


@dataclass
class ClienteTicket:
    nombre: str
    telefono: str
    direccion: str