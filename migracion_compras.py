"""
MIGRACIÓN: Módulo de Compras (costo y márgenes de ganancia)
============================================================
Ejecutar UNA SOLA VEZ en el servidor:

    python migracion_compras.py

Qué hace:
- Agrega la columna "precio_compra" a productos: es el costo
  promedio ponderado del producto (se recalcula automáticamente
  cada vez que registras una compra nueva).
- Crea la tabla "compras" (cabecera: proveedor, fecha, total).
- Crea la tabla "detalle_compra" (qué productos, cantidad y
  precio unitario se compraron en cada compra).
"""

import sys
sys.path.insert(0, __file__.rsplit("/migracion_compras.py", 1)[0] or ".")

from services.database_service import conectar


def columna_existe(cursor, tabla, columna):
    cursor.execute(f"PRAGMA table_info({tabla})")
    return any(fila["name"] == columna for fila in cursor.fetchall())


def tabla_existe(cursor, tabla):
    cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name=?
    """, (tabla,))
    return cursor.fetchone() is not None


def main():

    conn = conectar()
    cursor = conn.cursor()

    # ============================================
    # 1. Costo promedio en productos
    # ============================================
    if not columna_existe(cursor, "productos", "precio_compra"):
        cursor.execute("""
            ALTER TABLE productos ADD COLUMN precio_compra REAL DEFAULT 0
        """)
        print("✅ Columna 'precio_compra' agregada a productos")
    else:
        print("- Columna 'precio_compra' ya existía en productos")

    # ============================================
    # 2. Cabecera de cada compra
    # ============================================
    if not tabla_existe(cursor, "compras"):
        cursor.execute("""
            CREATE TABLE compras(

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                numero TEXT UNIQUE NOT NULL,

                proveedor TEXT,
                fecha TEXT NOT NULL,

                total REAL DEFAULT 0,

                observacion TEXT,
                usuario TEXT

            )
        """)
        print("✅ Tabla 'compras' creada")
    else:
        print("- Tabla 'compras' ya existía")

    # ============================================
    # 3. Detalle (productos) de cada compra
    # ============================================
    if not tabla_existe(cursor, "detalle_compra"):
        cursor.execute("""
            CREATE TABLE detalle_compra(

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                compra_id INTEGER NOT NULL,

                producto_codigo TEXT,
                producto TEXT,
                marca TEXT,

                cantidad INTEGER,
                precio_unitario REAL,
                subtotal REAL,

                FOREIGN KEY(compra_id) REFERENCES compras(id)

            )
        """)
        print("✅ Tabla 'detalle_compra' creada")
    else:
        print("- Tabla 'detalle_compra' ya existía")

    conn.commit()
    conn.close()

    print("\nMigración de compras completada.")


if __name__ == "__main__":
    main()
