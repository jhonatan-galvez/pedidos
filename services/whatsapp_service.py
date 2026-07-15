import requests

from config import Config


HEADERS = {
    "Authorization": f"Bearer {Config.WPP_TOKEN}",
    "Content-Type": "application/json"
}


def enviar_mensaje(numero, mensaje):

    numero = numero.replace("+", "")
    numero = numero.replace(" ", "")

    payload = {
        "phone": numero,
        "message": mensaje
    }

    url = f"{Config.WPP_URL}/api/{Config.WPP_SESSION}/send-message"

    r = requests.post(
        url,
        json=payload,
        headers=HEADERS,
        timeout=30
    )

    if r.status_code not in (200,201):
        raise Exception(r.text)

    return r.json()