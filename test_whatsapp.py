from services.whatsapp_service import enviar_mensaje

respuesta = enviar_mensaje(
    "51969365639",
    "Hola, este es un mensaje de prueba desde WPPConnect."
)

print(respuesta)