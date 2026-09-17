"""
MIGRACIÓN: Inventario físico (stock real vs stock teórico)
============================================================
Ejecutar UNA SOLA VEZ en el servidor:

    python migracion_inventario_fisico.py

Es seguro ejecutarlo más de una vez (verifica antes de crear).

Qué crea:
- Tabla "inventarios_fisicos": la cabecera de cada conteo
  (numeración INV-001, INV-002..., fecha/hora, estado, observación).
- Tabla "inventario_fisico_detalle": el detalle por producto de
  cada conteo (stock teórico al momento del conteo, stock real
  digitado, y la diferencia).

IMPORTANTE: esto NO reemplaza la columna "stock" de productos.
Esa columna sigue siendo el stock teórico (el que mueven las
ventas y la sincronización con Excel). El stock real que se
cuenta físicamente vive aparte, en estas tablas nuevas, y solo
se refleja en "productos.stock" si decides "cerrar" el inventario
aplicando los ajustes (usa el mismo mecanismo de REGULARIZACION
que ya tenías en stock_service.py).
"""

import sys
sys.path.insert(0, __file__.rsplit("/migracion_inventario_fisico.py", 1)[0] or ".")

from services.database_service import conectar


def tabla_existe(cursor, tabla):
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (tabla,))
    return cursor.fetchone() is not None


def main():

    conn = conectar()
    cursor = conn.cursor()

    # ============================================
    # 1. Cabecera de cada inventario físico
    # ============================================
    if not tabla_existe(cursor, "inventarios_fisicos"):
        cursor.execute("""
            CREATE TABLE inventarios_fisicos(

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                numero TEXT UNIQUE NOT NULL,

                fecha_inicio TEXT NOT NULL,
                fecha_cierre TEXT,

                estado TEXT DEFAULT 'ABIERTO',

                observacion TEXT,
                usuario TEXT

            )
        """)
        print("✅ Tabla 'inventarios_fisicos' creada")
    else:
        print("- Tabla 'inventarios_fisicos' ya existía")

    # ============================================
    # 2. Detalle por producto de cada inventario
    # ============================================
    if not tabla_existe(cursor, "inventario_fisico_detalle"):
        cursor.execute("""
            CREATE TABLE inventario_fisico_detalle(

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                inventario_id INTEGER NOT NULL,

                producto_codigo TEXT NOT NULL,
                producto TEXT,
                marca TEXT,
                tipo TEXT,
                presentacion TEXT,

                stock_teorico INTEGER,
                stock_real INTEGER,
                diferencia INTEGER,

                fecha_conteo TEXT,

                FOREIGN KEY(inventario_id)
                REFERENCES inventarios_fisicos(id)

            )
        """)
        print("✅ Tabla 'inventario_fisico_detalle' creada")
    else:
        print("- Tabla 'inventario_fisico_detalle' ya existía")

    conn.commit()
    conn.close()

    print("\nMigración de inventario físico completada.")


if __name__ == "__main__":
    main()
