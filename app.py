import os
import sqlite3
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# Configuración segura para manejo de sesiones
app.add_middleware(SessionMiddleware, secret_key="super-secret-key-castiel-crm")

# CONFIGURACIÓN DE RUTAS ABSOLUTAS (Limpia y sin duplicados)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates_path = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_path)

DB_PATH = os.path.join(BASE_DIR, "crm.db")

# Función para inicializar la base de datos de manera limpia en producción
def inicializar_base_de_datos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Crear tabla de usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        contrasena TEXT NOT NULL,
        nombre_completo TEXT NOT NULL,
        rol TEXT NOT NULL,
        estado TEXT NOT NULL,
        p_ver_clientes INTEGER DEFAULT 0,
        p_gestionar_clientes INTEGER DEFAULT 0,
        p_ver_comisiones INTEGER DEFAULT 0
    )
    """)
    
    # 2. Crear tabla de clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT NOT NULL,
        negocio TEXT,
        telefono TEXT,
        direccion TEXT,
        giro TEXT
    )
    """)
    
    # 3. Crear tabla de comisiones
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comisiones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asesor TEXT NOT NULL,
        monto REAL NOT NULL,
        fecha TEXT NOT NULL,
        descripcion TEXT
    )
    """)
    
    # 4. Insertar un usuario administrador si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO usuarios (usuario, contrasena, nombre_completo, rol, estado, p_ver_clientes, p_gestionar_clientes, p_ver_comisiones)
        VALUES ('admin', 'admin123', 'Administrador General', 'admin', 'Activo', 1, 1, 1)
        """)
        
    conn.commit()
    conn.close()

# Evento controlado de inicio del servidor FastAPI
@app.on_event("startup")
async def startup_event():
    inicializar_base_de_datos()


# --- CONTROL DE ACCESOS Y PERMISOS ---

async def obtener_usuario_actual(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        raise HTTPException(status_code=303, detail="No autenticado")
    return usuario

def verificar_permiso(usuario: str, permiso_columna: str) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"SELECT {permiso_columna}, rol FROM usuarios WHERE usuario = ?", (usuario,))
        res = cursor.fetchone()
        conn.close()
        
        if res:
            if res[1] == "admin":
                return True
            return res[0] == 1
        return False
    except Exception:
        return False


# --- RUTAS DE AUTENTICACIÓN ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("usuario"):
        return RedirectResponse(url="/panel", status_code=303)
    
    # El orden correcto que exige Jinja2 en tu servidor:
    return templates.TemplateResponse(
        request, 
        name="login.html", 
        context={"error": None}
    )
@app.post("/login")
async def login(request: Request, usuario: str = Form(...), contrasena: str = Form(...)):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT usuario, rol, estado FROM usuarios WHERE usuario = ? AND contrasena = ?", (usuario, contrasena))
        user_record = cursor.fetchone()
        conn.close()

        if user_record:
            username, rol, estado = user_record
            if estado == "Inactivo":
                return templates.TemplateResponse(
                    request=request,
                    name="login.html",
                    context={"error": "Tu cuenta ha sido bloqueada por el Administrador."}
                )

            request.session["usuario"] = username
            request.session["rol"] = rol
            return RedirectResponse(url="/panel", status_code=303)

        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Usuario o contraseña incorrectos"})
    except Exception as e:
        return HTMLResponse(content=f"Error en el Servidor (Login): {str(e)}", status_code=500)


# --- VISTAS DEL PANEL ---

@app.get("/panel", response_class=HTMLResponse)
async def panel_clientes(request: Request, usuario=Depends(obtener_usuario_actual)):
    if not verificar_permiso(usuario, "p_ver_clientes"):
        return HTMLResponse(content="No tienes permisos para ver la lista de clientes.", status_code=403)

    p_gestionar = verificar_permiso(usuario, "p_gestionar_clientes")
    p_comisiones = verificar_permiso(usuario, "p_ver_comisiones")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, negocio, telefono, direccion, giro FROM clientes")
    clientes = cursor.fetchall()
    conn.close()

    lista_clientes = [
        {"id": c[0], "cliente": c[1], "negocio": c[2], "telefono": c[3], "direccion": c[4], "giro": c[5]}
        for c in clientes
    ]

    return templates.TemplateResponse(
        request=request,
        name="panel.html",
        context={
            "clientes": lista_clientes,
            "usuario": usuario,
            "rol": request.session.get("rol"),
            "p_gestionar": p_gestionar,
            "p_comisiones": p_comisiones
        }
    )


# --- SECCIÓN DE COMISIONES ---

@app.get("/comisiones", response_class=HTMLResponse)
async def ver_comisiones(request: Request, usuario=Depends(obtener_usuario_actual)):
    if not verificar_permiso(usuario, "p_ver_comisiones"):
        return HTMLResponse(content="No tienes permisos para ver comisiones.", status_code=403)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, asesor, monto, fecha, descripcion FROM comisiones")
    comisiones = cursor.fetchall()
    conn.close()

    lista_comisiones = [
        {"id": c[0], "asesor": c[1], "monto": c[2], "fecha": c[3], "descripcion": c[4]}
        for c in comisiones
    ]

    return templates.TemplateResponse(
        request=request,
        name="comisiones.html",
        context={
            "comisiones": lista_comisiones,
            "usuario": usuario,
            "rol": request.session.get("rol")
        }
    )


# =========================================================
# 🔄 SISTEMA DE MIGRACIÓN AUTOMÁTICA DE BASE DE DATOS
# =========================================================

def inicializar_base_datos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crear la tabla si es una instalación totalmente limpia
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            contrasena TEXT,
            rol TEXT,
            p_gestionar INTEGER DEFAULT 0,
            p_comisiones INTEGER DEFAULT 0,
            nombre_completo TEXT DEFAULT '',
            puesto TEXT DEFAULT 'Asesor'
        )
    """)
    
    # 🔎 Verificar dinámicamente qué columnas existen en el servidor de Render
    cursor.execute("PRAGMA table_info(usuarios)")
    columnas_actuales = [col[1] for col in cursor.fetchall()]
    
    # Agregar las columnas si faltan en la base de datos de producción
    if "nombre_completo" not in columnas_actuales:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN nombre_completo TEXT DEFAULT ''")
    if "puesto" not in columnas_actuales:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN puesto TEXT DEFAULT 'Asesor'")
    if "p_gestionar" not in columnas_actuales:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN p_gestionar INTEGER DEFAULT 0")
    if "p_comisiones" not in columnas_actuales:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN p_comisiones INTEGER DEFAULT 0")
        
    # Insertar el administrador maestro únicamente si la tabla está completamente vacía
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO usuarios (usuario, contrasena, rol, p_gestionar, p_comisiones, nombre_completo, puesto)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("admin", "admin123", "admin", 1, 1, "Eli Castillo", "Director Corporativo"))
        
    conn.commit()
    conn.close()

# Ejecutar migración de forma automática en cada reinicio del contenedor
inicializar_base_datos()


# =========================================================
# 👤 CONTROL DE ACCESOS Y MENÚ DE USUARIOS
# =========================================================

@app.get("/usuarios", response_class=HTMLResponse)
async def usuarios_page(request: Request):
    usuario_sesion = request.session.get("usuario")
    if not usuario_sesion:
        return RedirectResponse(url="/", status_code=303)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Forzar la verificación de privilegios de administrador
    cursor.execute("SELECT rol FROM usuarios WHERE usuario = ?", (usuario_sesion,))
    user_data = cursor.fetchone()
    if not user_data or user_data[0].lower() != "admin":
        conn.close()
        return HTMLResponse(content="Acceso denegado: Privilegios insuficientes.", status_code=403)
    
    # Consulta optimizada que incluye los nuevos campos requeridos por el template
    cursor.execute("SELECT id, usuario, contrasena, rol, nombre_completo, puesto, p_gestionar, p_comisiones FROM usuarios")
    filas = cursor.fetchall()
    
    lista_usuarios = []
    for fila in filas:
        lista_usuarios.append({
            "id": fila[0],
            "usuario": fila[1],
            "contrasena": fila[2],
            "rol": fila[3],
            "nombre_completo": fila[4] or "",
            "puesto": fila[5] or "Asesor",
            "p_gestionar": fila[6] or 0,
            "p_comisiones": fila[7] or 0
        })
        
    conn.close()
    return templates.TemplateResponse(
        request,
        name="usuarios.html",
        context={"usuarios": lista_usuarios, "usuario_actual": usuario_sesion}
    )


@app.post("/crear-usuario")
async def crear_usuario(
    nuevo_usuario: str = Form(...),
    contrasena: str = Form(...),
    nombre_completo: str = Form(""),
    puesto: str = Form("Asesor"),
    p_gestionar: str = Form(None),
    p_comisiones: str = Form(None)
):
    # Convertir las casillas de verificación (Checkboxes) HTML a valores binarios (0 o 1)
    valor_gestionar = 1 if p_gestionar else 0
    valor_comisiones = 1 if p_comisiones else 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO usuarios (usuario, contrasena, rol, nombre_completo, puesto, p_gestionar, p_comisiones) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nuevo_usuario.strip(), contrasena, "asesor", nombre_completo.strip(), puesto.strip(), valor_gestionar, valor_comisiones))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Manejo silencioso en caso de intentar registrar un identificador ya existente
    finally:
        conn.close()
    return RedirectResponse(url="/usuarios", status_code=303)


@app.post("/editar-usuario")
async def editar_usuario(
    id_usuario: int = Form(...),
    usuario_login: str = Form(...),
    nueva_contrasena: str = Form(...),
    nombre_completo: str = Form(...),
    puesto: str = Form(...),
    p_gestionar: str = Form(None),
    p_comisiones: str = Form(None)
):
    valor_gestionar = 1 if p_gestionar else 0
    valor_comisiones = 1 if p_comisiones else 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE usuarios 
            SET usuario = ?, contrasena = ?, nombre_completo = ?, puesto = ?, p_gestionar = ?, p_comisiones = ?
            WHERE id = ?
        """, (usuario_login.strip(), nueva_contrasena, nombre_completo.strip(), puesto.strip(), valor_gestionar, valor_comisiones, id_usuario))
        conn.commit()
    except Exception as e:
        print(f"Error detectado durante la edición en lote: {e}")
    finally:
        conn.close()
    return RedirectResponse(url="/usuarios", status_code=303)


# =========================================================
# 🚪 CIERRE Y EXPULSIÓN DE SESIONES
# =========================================================

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
