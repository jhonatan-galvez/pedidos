from services.sync_service import sincronizar_productos

if __name__ == "__main__":
    resultado = sincronizar_productos()
    print(resultado)
    print("Sincronización completada")