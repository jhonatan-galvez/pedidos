import sqlite3

conn = sqlite3.connect("database/database.db")
cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE pedidos
        ADD COLUMN tipo_pago TEXT DEFAULT 'Efectivo'
    """)

    conn.commit()
    print("✅ Columna tipo_pago agregada correctamente.")

except Exception as e:
    print("❌", e)

finally:
    conn.close()