"""
MIGRACIÓN: Caja de Recaudación + campo "pagado" en pedidos
============================================================
Ejecutar UNA SOLA VEZ en el servidor:

    python migracion_caja.py

Es seguro ejecutarlo más de una vez (verifica antes de crear/alterar).
"""

import sys
sys.path.insert(0, __file__.rsplit("/migracion_caja.py", 1)[0] or ".")

from services.database_service import conectar


def columna_existe(cursor, tabla, columna):
    cursor.execute(f"PRAGMA table_info({tabla})")
    columnas = [c[1] for c in cursor.fetchall()]
    return columna in columnas


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
    # 1. Columna "pagado" en pedidos
    # ============================================
    if not columna_existe(cursor, "pedidos", "pagado"):
        cursor.execute("ALTER TABLE pedidos ADD COLUMN pagado INTEGER DEFAULT 0")
        print("✅ Columna 'pagado' agregada a pedidos")
    else:
        print("- Columna 'pagado' ya existía")

    if not columna_existe(cursor, "pedidos", "fecha_pago"):
        cursor.execute("ALTER TABLE pedidos ADD COLUMN fecha_pago TEXT")
        print("✅ Columna 'fecha_pago' agregada a pedidos")
    else:
        print("- Columna 'fecha_pago' ya existía")

    # ============================================
    # 2. Tabla caja_movimientos
    # ============================================
    if not tabla_existe(cursor, "caja_movimientos"):

        cursor.execute("""
            CREATE TABLE caja_movimientos (

                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                tipo_pago TEXT NOT NULL,
                tipo_movimiento TEXT NOT NULL,
                monto REAL NOT NULL,
                pedido_id INTEGER,
                observacion TEXT,

                FOREIGN KEY(pedido_id) REFERENCES pedidos(id)
            )
        """)

        print("✅ Tabla 'caja_movimientos' creada")

    else:
        print("- Tabla 'caja_movimientos' ya existía")

    conn.commit()
    conn.close()

    print()
    print("Migración completa.")


if __name__ == "__main__":
    main()
