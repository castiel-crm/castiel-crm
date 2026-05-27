import sqlite3  
conexion = sqlite3.connect('castiel_crm.db')  
cursor = conexion.cursor()  
cursor.execute("CREATE TABLE IF NOT EXISTS clientes (id_cliente INTEGER PRIMARY KEY AUTOINCREMENT, nombre_cliente TEXT NOT NULL, nombre_negocio TEXT NOT NULL, telefono TEXT, direccion TEXT, giro_negocio TEXT)")  
cursor.execute("CREATE TABLE IF NOT EXISTS seguimientos (id_seguimiento INTEGER PRIMARY KEY AUTOINCREMENT, id_cliente INTEGER, fecha TEXT NOT NULL, nombre_asesor TEXT NOT NULL, producto_interes TEXT NOT NULL, tipo_interaccion TEXT NOT NULL, detalles TEXT, estatus TEXT, FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente) ON DELETE CASCADE)")  
conexion.commit()  
conexion.close()  
print('Base de datos creada con exito') 
