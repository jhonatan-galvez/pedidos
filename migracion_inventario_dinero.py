"""
MIGRACIÓN: Diferencia en soles en el Inventario Físico
============================================================
Ejecutar UNA SOLA VEZ, DESPUÉS de migracion_compras.py:

    python migracion_inventario_dinero.py

Qué hace: agrega dos columnas a inventario_fisico_detalle:
- costo_unitario: el costo del producto (productos.precio_compra)
  congelado al momento de crear el inventario.
- diferencia_valor: diferencia (stock_real - stock_teorico)
  multiplicada por el costo unitario = a cuánto equivale esa
  diferencia en soles.
"""

import sys
sys.path.insert(0, __file__.rsplit("/migracion_inventario_dinero.py", 1)[0] or ".")

from services.database_service import conectar


def columna_existe(cursor, tabla, columna):
    cursor.execute(f"PRAGMA table_info({tabla})")
    return any(fila["name"] == columna for fila in cursor.fetchall())


def main():

    conn = conectar()
    cursor = conn.cursor()

    if not columna_existe(cursor, "inventario_fisico_detalle", "costo_unitario"):
        cursor.execute("""
            ALTER TABLE inventario_fisico_detalle
            ADD COLUMN costo_unitario REAL DEFAULT 0
        """)
        print("✅ Columna 'costo_unitario' agregada")
    else:
        print("- Columna 'costo_unitario' ya existía")

    if not columna_existe(cursor, "inventario_fisico_detalle", "diferencia_valor"):
        cursor.execute("""
            ALTER TABLE inventario_fisico_detalle
            ADD COLUMN diferencia_valor REAL
        """)
        print("✅ Columna 'diferencia_valor' agregada")
    else:
        print("- Columna 'diferencia_valor' ya existía")

    conn.commit()
    conn.close()

    print("\nMigración completada.")


if __name__ == "__main__":
    main()
