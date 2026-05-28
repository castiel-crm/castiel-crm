import os
import sqlite3
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
@app.on_event("startup")
def iniciar_sistema():
    inicializar_base_de_datos()

# Configuración de cookies seguras para la sesión
app.add_middleware(SessionMiddleware, secret_key="super-secret-key-castiel-crm")

templates = Jinja2Templates(directory="templates")

DB_PATH = "castiel_crm.db"

def inicializar_base_de_datos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla de Clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            negocio TEXT,
            telefono TEXT,
            direccion TEXT,
            giro TEXT
        )
    ''')
    
    # Tabla de Usuarios (con Permisos específicos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            contrasena TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            rol TEXT DEFAULT 'asesor',
            estado TEXT DEFAULT 'Activo',
            p_ver_clientes INTEGER DEFAULT 1,
            p_gestionar_clientes INTEGER DEFAULT 1,
            p_ver_comisiones INTEGER DEFAULT 0
        )
    ''')
    
    # Tabla de Comisiones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comisiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            monto REAL NOT NULL,
            concepto TEXT,
            fecha TEXT,
            estado_pago TEXT DEFAULT 'Pendiente',
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
    ''')
    
    # Insertar administrador por defecto con todos los permisos habilitados (1 = Sí, 0 = No)
    cursor.execute("SELECT * FROM usuarios WHERE rol = 'admin'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO usuarios (usuario, contrasena, nombre_completo, rol, estado, p_ver_clientes, p_gestionar_clientes, p_ver_comisiones)
            VALUES ('admin', 'admin123', 'Administrador Principal', 'admin', 'Activo', 1, 1, 1)
        ''')
        
    conn.commit()
    conn.close()

inicializar_base_de_datos()

# --- CONTROL DE ACCESOS Y PERMISOS ---
def obtener_usuario_actual(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        raise HTTPException(status_code=303, detail="No autenticado")
    return usuario

def verificar_permiso(usuario: str, permiso_columna: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT {permiso_columna}, rol FROM usuarios WHERE usuario = ?", (usuario,))
    res = cursor.fetchone()
    conn.close()
    if res:
        # El administrador siempre tiene todos los permisos
        if res[1] == "admin":
            return True
        return res[0] == 1
    return False

# --- RUTAS DE AUTENTICACIÓN ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("usuario"):
        return RedirectResponse(url="/panel", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})

@app.post("/login")
async def login(request: Request, usuario: str = Form(...), contrasena: str = Form(...)):
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

    return templates.TemplateResponse(request=request, name="login.html", context={"error": "Usuario o contraseña incorrectos."})
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


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


# --- SECCIÓN DE USUARIOS (ADMIN) ---

@app.get("/usuarios", response_class=HTMLResponse)
async def listar_usuarios(request: Request, usuario=Depends(obtener_usuario_actual)):
    if request.session.get("rol") != "admin":
        return RedirectResponse(url="/panel", status_code=303)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, nombre_completo, rol, estado, p_ver_clientes, p_gestionar_clientes, p_ver_comisiones FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()

    lista_usuarios = [
        {
            "usuario": u[0],
            "nombre_completo": u[1],
            "rol": u[2],
            "estado": u[3],
            "p_ver_clientes": u[4],
            "p_gestionar_clientes": u[5],
            "p_ver_comisiones": u[6]
        }
        for u in usuarios
    ]

    return templates.TemplateResponse(
        request=request,
        name="usuarios.html",
        context={
            "usuarios": lista_usuarios,
            "usuario": usuario,
            "rol": request.session.get("rol")
        }
    )


@app.post("/usuarios/crear")
async def crear_usuario(
    request: Request,
    usuario: str = Form(...),
    contrasena: str = Form(...),
    nombre_completo: str = Form(...),
    p_ver_c: int = Form(0),
    p_gest_c: int = Form(0),
    p_ver_com: int = Form(0),
    usuario_act=Depends(obtener_usuario_actual)
):
    if request.session.get("rol") != "admin":
        return RedirectResponse(url="/panel", status_code=303)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO usuarios (usuario, contrasena, nombre_completo, rol, estado, p_ver_clientes, p_gestionar_clientes, p_ver_comisiones)
               VALUES (?, ?, ?, 'asesor', 'Activo', ?, ?, ?)""",
            (usuario, contrasena, nombre_completo, p_ver_c, p_gest_c, p_ver_com)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

    return RedirectResponse(url="/usuarios", status_code=303)


@app.post("/usuarios/actualizar-permisos/{user_id}")
async def actualizar_permisos(
    request: Request,
    user_id: str,
    p_ver_c: int = Form(0),
    p_gest_c: int = Form(0),
    p_ver_com: int = Form(0),
    usuario_act=Depends(obtener_usuario_actual)
):
    if request.session.get("rol") != "admin":
        return RedirectResponse(url="/panel", status_code=303)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE usuarios 
           SET p_ver_clientes = ?, p_gestionar_clientes = ?, p_ver_comisiones = ? 
           WHERE usuario = ?""",
        (p_ver_c, p_gest_c, p_ver_com, user_id)
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url="/usuarios", status_code=303)


@app.post("/usuarios/cambiar-estado/{user_id}")
async def cambiar_estado(
    request: Request,
    user_id: str,
    nuevo_estado: str = Form(...),
    usuario_act=Depends(obtener_usuario_actual)
):
    if request.session.get("rol") != "admin":
        return RedirectResponse(url="/panel", status_code=303)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET estado = ? WHERE usuario = ?", (nuevo_estado, user_id))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/usuarios", status_code=303)
