from datetime import datetime

def construir_mensaje(numero_pedido, cliente, carrito, observaciones=None):

    texto = []

    texto.append("🟢 *NUEVO PEDIDO RECIBIDO*")
    texto.append("━━━━━━━━━━━━━━")
    texto.append(f"🧾 *Pedido:* #{numero_pedido}")
    texto.append("")

    texto.append("👤 *CLIENTE*")
    texto.append(f"• Nombre: {cliente['nombre']}")
    texto.append(f"• Celular: {cliente['telefono']}")
    texto.append(f"• Dirección: {cliente['direccion']}")
    texto.append("")

    texto.append("🛍️ *DETALLE DEL PEDIDO*")

    total = 0

    for item in carrito:

        subtotal = item["cantidad"] * item["precio"]
        total += subtotal

        texto.append(
            f"• {item['producto']}"
        )
        texto.append(
            f"   {item['cantidad']} × S/ {item['precio']:.2f} = *S/ {subtotal:.2f}*"
        )

    texto.append("")
    texto.append("━━━━━━━━━━━━━━")
    texto.append(f"💰 *TOTAL: S/ {total:.2f}*")

    texto.append(f"🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    if observaciones:
        texto.append("")
        texto.append("📝 *Observaciones*")
        texto.append(observaciones)

    texto.append("")
    texto.append("✅ Preparar pedido.")

    return "\n".join(texto) 