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
    
    conexion.commit()
    conexion.close()