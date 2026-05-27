import sqlite3
from datetime import datetime

def registrar_cliente(n, b, t, d, g):
    conn = sqlite3.connect('castiel_crm.db')
    c = conn.cursor()
    c.execute("INSERT INTO clientes (nombre_cliente, nombre_negocio, telefono, detalle, estado) VALUES (?, ?, ?, ?, ?)", (n, b, t, d, g))
    conn.commit()
    conn.close()

def registrar_seguimiento(id_c, ase, prod, tip, det, est):
    conn = sqlite3.connect('castiel_crm.db')
    c = conn.cursor()
    f = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO seguimientos (id_cliente, fecha, nombre_asesor, producto_interes, tipo_interaccion, detalle_seguimiento, estado_seguimiento) VALUES (?, ?, ?, ?, ?, ?, ?)", (id_c, f, ase, prod, tip, det, est))
    conn.commit()
    conn.close()
    conn.commit()
    conn.close()
def obtener_historial_cliente(id_c):  
 conn = sqlite3.connect('castiel_crm.db')  
 c = conn.cursor()  
 c.execute("SELECT fecha, nombre_asesor, producto_interes, tipo_interaccion, detalles, estatus FROM seguimientos WHERE id_cliente = ? ORDER BY fecha DESC", (id_c,))  
 h = c.fetchall()  
 conn.close()  
 return h  
def obtener_clientes():  
 conn = sqlite3.connect('castiel_crm.db')  
 c = conn.cursor()  
 c.execute("SELECT * FROM clientes")  
 l = c.fetchall()  
 conn.close()  
 return l 
def inicializar_base_de_datos():
    conn = sqlite3.connect('castiel_crm.db')
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_cliente TEXT,
        nombre_negocio TEXT,
        telefono TEXT,
        detalle TEXT,
        estado TEXT,
        vendedor TEXT,
        producto TEXT,
        comision REAL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS seguimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER,
        fecha TEXT,
        nombre_asesor TEXT,
        producto_interes TEXT,
        tipo_interaccion TEXT,
        detalle_seguimiento TEXT,
        estado_seguimiento TEXT,
        FOREIGN KEY(id_cliente) REFERENCES clientes(id)
    )
    """)
    conn.commit()
    conn.close()
