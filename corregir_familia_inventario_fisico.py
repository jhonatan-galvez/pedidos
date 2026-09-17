"""
CORRECCIÓN: Reagrupar inventarios físicos existentes por "producto"
============================================================
Ejecutar UNA SOLA VEZ en el servidor:

    python corregir_familia_inventario_fisico.py

Qué hace: para los inventarios físicos creados ANTES del cambio de
"tipo" a "producto" como familia, actualiza solo la columna "tipo"
de inventario_fisico_detalle (la que se usa para agrupar visualmente)
para que coincida con el "producto" actual de cada código en la
tabla productos. NO toca stock_real, stock_teorico ni diferencia:
todo lo que ya contaste se mantiene intacto.
"""

import sys
sys.path.insert(0, __file__.rsplit("/corregir_familia_inventario_fisico.py", 1)[0] or ".")

from services.database_service import conectar


def main():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE inventario_fisico_detalle
        SET tipo = (
            SELECT producto FROM productos
            WHERE productos.codigo = inventario_fisico_detalle.producto_codigo
        )
        WHERE producto_codigo IN (
            SELECT codigo FROM productos
        )
    """)

    afectados = cursor.rowcount

    conn.commit()
    conn.close()

    print(f"✅ {afectados} fila(s) de detalle reagrupadas por 'producto'.")


if __name__ == "__main__":
    main()
