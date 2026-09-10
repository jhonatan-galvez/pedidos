from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE = BASE_DIR / "database" / "database.db"


def conectar():

    conexion = sqlite3.connect(DATABASE)
    conexion.row_factory = sqlite3.Row

    return conexion

def inicializar_database():

    conexion = conectar()
    cursor = conexion.cursor()

    # ==========================
    # PRODUCTOS
    # ==========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            codigo TEXT UNIQUE,

            producto TEXT NOT NULL,

            marca TEXT,

            tipo TEXT,

            presentacion TEXT,

            stock INTEGER,

            precio REAL,

            imagen TEXT,

            activo INTEGER DEFAULT 1,

            fecha_creacion TEXT,

            fecha_actualizacion TEXT

        )
    """)

    # ==========================
    # CATEGORIAS
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nombre TEXT UNIQUE,

        activo INTEGER DEFAULT 1

    )
    """) 
 
    # ==========================
    # CLIENTES
    # ==========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nombre TEXT NOT NULL,

            telefono TEXT UNIQUE,

            direccion TEXT,

            referencia TEXT,

            fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,

            ultima_compra TEXT,

            activo INTEGER DEFAULT 1                   
        )
    """)

    # ==========================
    # PEDIDOS
    # ==========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos(

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT UNIQUE,
            cliente_id INTEGER,
            fecha TEXT, 
            estado TEXT,
            subtotal REAL,
            delivery REAL DEFAULT 0,
            descuento REAL DEFAULT 0,
            total REAL,
            observaciones TEXT,
            fecha_actualizacion TEXT,
            usuario TEXT,
            tipo_pago TEXT DEFAULT 'Efectivo',

            FOREIGN KEY(cliente_id)
            REFERENCES clientes(id)

        )
    """)

    # ==========================
    # DETALLE PEDIDO
    # ==========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_pedido(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            pedido_id INTEGER,

            producto_codigo TEXT,

            producto TEXT,

            marca TEXT,

            presentacion TEXT,

            cantidad INTEGER,

            precio_unitario REAL,

            subtotal REAL,

            FOREIGN KEY(pedido_id)
            REFERENCES pedidos(id)

        )
    """)

    # ==========================
    # MOVIMIENTOS STOCK
    # ==========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_stock(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            producto_codigo TEXT,

            fecha TEXT,

            tipo TEXT,

            cantidad INTEGER,

            stock_anterior INTEGER,

            stock_nuevo INTEGER,

            pedido_id INTEGER,

            observacion TEXT

        )
    """)

    # ==========================
    # CONFIGURACIÓN
    # ==========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nombre_tienda TEXT,

            telefono TEXT,

            direccion TEXT,

            logo TEXT,

            delivery REAL DEFAULT 0,

            moneda TEXT DEFAULT 'S/',

            whatsapp TEXT

        )
    """)
    # ==========================
    # SINCRONIZACIONES
    # ==========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sincronizaciones(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            fecha TEXT NOT NULL,

            productos_leidos INTEGER DEFAULT 0,

            nuevos INTEGER DEFAULT 0,

            actualizados INTEGER DEFAULT 0,

            sin_cambios INTEGER DEFAULT 0,

            desactivados INTEGER DEFAULT 0,

            errores INTEGER DEFAULT 0,

            duracion REAL DEFAULT 0

        )
    """)
    
    # ==========================
    # PERFILES (roles de usuario)
    # ==========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfiles(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nombre TEXT UNIQUE NOT NULL,

            puede_crear INTEGER DEFAULT 0,
            puede_editar INTEGER DEFAULT 0,
            es_admin INTEGER DEFAULT 0,

            sistema INTEGER DEFAULT 0,

            fecha_creacion TEXT

        )
    """)

    # ==========================
    # USUARIOS
    # ==========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nombre_completo TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,

            perfil_id INTEGER,

            pregunta_seguridad TEXT,
            respuesta_seguridad_hash TEXT,

            activo INTEGER DEFAULT 1,
            fecha_creacion TEXT,
            ultimo_acceso TEXT,

            FOREIGN KEY(perfil_id) REFERENCES perfiles(id)

        )
    """)

    conexion.commit()

    # ==========================
    # SEMILLA: perfiles del sistema + cuenta master
    # Solo se ejecuta si todavía no hay ningún perfil creado
    # ==========================
    cursor.execute("SELECT COUNT(*) AS n FROM perfiles")

    if cursor.fetchone()["n"] == 0:

        from datetime import datetime
        from werkzeug.security import generate_password_hash

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Perfil Administrador: acceso total, no se puede borrar
        cursor.execute("""
            INSERT INTO perfiles (nombre, puede_crear, puede_editar, es_admin, sistema, fecha_creacion)
            VALUES ('Administrador', 1, 1, 1, 1, ?)
        """, (ahora,))
        id_admin = cursor.lastrowid

        # Perfil Vendedor: puede crear y editar pedidos, no elimina ni gestiona usuarios
        cursor.execute("""
            INSERT INTO perfiles (nombre, puede_crear, puede_editar, es_admin, sistema, fecha_creacion)
            VALUES ('Vendedor', 1, 1, 0, 1, ?)
        """, (ahora,))

        # Cuenta MASTER: para pruebas del desarrollador, perfil Administrador.
        # Usuario y contraseña iniciales: master / master123
        # (cámbialos de inmediato desde "Mi cuenta" al entrar la primera vez)
        cursor.execute("""
            INSERT INTO usuarios
            (nombre_completo, usuario, password_hash, perfil_id,
             pregunta_seguridad, respuesta_seguridad_hash, activo, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (
            "Cuenta Master",
            "master",
            generate_password_hash("master123"),
            id_admin,
            "¿Cuál es el nombre de este sistema?",
            generate_password_hash("doña flori"),
            ahora
        ))

        conexion.commit()

    conexion.close()