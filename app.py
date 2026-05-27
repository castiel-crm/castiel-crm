from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
from funciones_crm import inicializar_base_de_datos, registrar_cliente, registrar_seguimiento, obtener_historial_cliente, obtener_clientes
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# Configuración de Seguridad: Añadimos una clave secreta para proteger las sesiones de usuario
app.add_middleware(SessionMiddleware, secret_key="CastielCorpCRMSecretKey_ChangeMe")

# Inicializamos la base de datos al encender el servidor
inicializar_base_de_datos()

# ==========================================
# 1. CONTROL DE ACCESO (LOGÍN VISUAL)
# ==========================================

@app.get("/login", response_class=HTMLResponse)
def vista_login(request: Request, error: str = None):
    # Genera una pantalla de inicio de sesión elegante y limpia
    mensaje_error = f'<p style="color: #e74c3c; background: #fdf2f2; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;">{error}</p>' if error else ''
    
    html_login = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Iniciar Sesión - Corporación CASTIEL</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .login-card {{ background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); width: 100%; max-width: 360px; }}
            .brand {{ text-align: center; margin-bottom: 30px; }}
            .brand h2 {{ margin: 0; color: #1a252f; letter-spacing: 1px; font-size: 24px; }}
            .brand p {{ margin: 5px 0 0 0; color: #7f8c8d; font-size: 12px; font-weight: bold; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; color: #34495e; font-size: 14px; font-weight: 500; }}
            .form-group input {{ width: 100%; padding: 10px; border: 1px solid #dcdde1; border-radius: 6px; box-sizing: border-box; font-size: 14px; }}
            .form-group input:focus {{ border-color: #2c3e50; outline: none; }}
            .btn-submit {{ width: 100%; padding: 12px; background: #2c3e50; border: none; color: white; font-weight: bold; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s; }}
            .btn-submit:hover {{ background: #1a252f; }}
        </style>
    </head>
    <body>
        <div class="login-card">
            <div class="brand">
                <h2>CORPORACIÓN</h2>
                <h2><strong>CASTIEL</strong></h2>
                <p>SEGURIDAD • VISIÓN • LIDERAZGO</p>
            </div>
            {mensaje_error}
            <form action="/login" method="post">
                <div class="form-group">
                    <label>Usuario</label>
                    <input type="text" name="username" required placeholder="Escribe tu usuario">
                </div>
                <div class="form-group">
                    <label>Contraseña</label>
                    <input type="password" name="password" required placeholder="••••••••">
                </div>
                <button type="submit" class="btn-submit">Ingresar al Sistema</button>
            </form>
        </div>
    </body>
    </html>
    """
    return html_login

@app.post("/login")
def procesar_login(request: Request, username: str = Form(...), password: str = Form(...)):
    # Conectamos a la base de datos para verificar si el usuario existe
    conn = sqlite3.connect('castiel_crm.db')
    c = conn.cursor()
    c.execute("SELECT rol FROM usuarios WHERE usuario = ? AND contrasena = ?", (username, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        # Guardamos los datos de acceso del usuario en la sesión del navegador
        request.session["usuario"] = username
        request.session["rol"] = user[0]
        return RedirectResponse(url="/", status_code=303)
    else:
        return RedirectResponse(url="/login?error=Usuario o contraseña incorrectos", status_code=303)

@app.get("/logout")
def cerrar_sesion(request: Request):
    # Borra la sesión del usuario del navegador y lo expulsa
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


# ==========================================
# 2. VISTAS PRINCIPALES DEL CRM (PROTEGIDAS)
# ==========================================

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    # Si el usuario no ha iniciado sesión, lo redirige automáticamente al Login
    if "usuario" not in request.session:
        return RedirectResponse(url="/login", status_code=303)
        
    clientes = obtener_clientes()
    
    # Renderizamos la lista de clientes en la tabla visual
    tabla_clientes = ""
    for cli in clientes:
        tabla_clientes += f"""
        <tr>
            <td>#{cli[0]}</td>
            <td><strong>{cli[1]}</strong></td>
            <td>{cli[2]}</td>
            <td>{cli[3]}</td>
            <td>{cli[4]}</td>
            <td><span class="badge">{cli[5]}</span></td>
            <td>
                <button class="btn-action" onclick="abrirModalSeguimiento({cli[0]}, '{cli[1]}')">＋ Seguimiento</button>
                <button class="btn-action btn-secondary" onclick="verHistorial({cli[0]}, '{cli[1]}')">👁 Ver Historial</button>
            </td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Panel de Control - Corporación CASTIEL</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; background-color: #f8f9fa; display: flex; color: #333; }}
            .sidebar {{ width: 250px; background-color: #2c3e50; color: white; min-height: 100vh; padding: 20px; box-sizing: border-box; }}
            .sidebar h2 {{ margin: 0; font-size: 20px; letter-spacing: 1px; text-align: center; }}
            .sidebar p {{ margin: 5px 0 30px 0; font-size: 10px; color: #bdc3c7; text-align: center; letter-spacing: 2px; }}
            .menu-item {{ padding: 12px 15px; color: #ecf0f1; text-decoration: none; display: block; border-radius: 5px; font-weight: bold; margin-bottom: 5px; }}
            .menu-item:hover, .menu-item.active {{ background-color: #34495e; color: white; }}
            .logout-btn {{ background: #c0392b; text-align: center; margin-top: 30px; }}
            .logout-btn:hover {{ background: #e74c3c; }}
            .main-content {{ flex-grow: 1; padding: 40px; box-sizing: border-box; }}
            .header-panel {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 2px solid #eaeaea; padding-bottom: 15px; }}
            .header-panel h1 {{ margin: 0; color: #2c3e50; font-size: 26px; }}
            .user-tag {{ font-size: 14px; color: #7f8c8d; background: #eef1f4; padding: 6px 12px; border-radius: 20px; font-weight: bold; }}
            .btn-primary {{ background-color: #2c3e50; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 14px; }}
            .btn-primary:hover {{ background-color: #1a252f; }}
            table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }}
            th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #f1f2f6; }}
            th {{ background-color: #f8f9fa; color: #7f8c8d; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }}
            .badge {{ background-color: #ffeaa7; color: #d63031; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
            .btn-action {{ background-color: #2ecc71; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; cursor: pointer; margin-right: 5px; }}
            .btn-action:hover {{ background-color: #27ae60; }}
            .btn-secondary {{ background-color: #3498db; }}
            .btn-secondary:hover {{ background-color: #2980b9; }}
            .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); justify-content: center; align-items: center; z-index: 1000; }}
            .modal-content {{ background: white; padding: 30px; border-radius: 8px; width: 450px; box-shadow: 0 5px 15px rgba(0,0,0,0.2); position: relative; }}
            .modal-content h3 {{ margin-top: 0; color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
            .form-input {{ width: 100%; padding: 8px; margin: 8px 0 15px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
            .close-modal {{ position: absolute; top: 15px; right: 15px; cursor: pointer; font-size: 20px; color: #aaa; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h2>CORPORACIÓN</h2>
            <h2><strong>CASTIEL</strong></h2>
            <p>SEGURIDAD • VISIÓN • LIDERAZGO</p>
            <a href="/" class="menu-item active">📋 Lista de Clientes</a>
            <a href="/logout" class="menu-item logout-btn">🚪 Cerrar Sesión</a>
        </div>
        <div class="main-content">
            <div class="header-panel">
                <div>
                    <h1>Panel de Control de Clientes</h1>
                </div>
                <div>
                    <span class="user-tag">👤 Conectado: {request.session["usuario"]} ({request.session["rol"]})</span>
                    <button class="btn-primary" style="margin-left: 10px;" onclick="toggleModal('modalCliente')">＋ Nuevo Cliente</button>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Cliente</th>
                        <th>Negocio</th>
                        <th>Teléfono</th>
                        <th>Detalle/Dirección</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {tabla_clientes}
                </tbody>
            </table>
        </div>

        <div id="modalCliente" class="modal">
            <div class="modal-content">
                <span class="close-modal" onclick="toggleModal('modalCliente')">&times;</span>
                <h3>Registrar Nuevo Cliente</h3>
                <form action="/guardar-cliente" method="post">
                    <label>Nombre del Cliente</label>
                    <input type="text" name="nombre" class="form-input" required>
                    <label>Nombre del Negocio</label>
                    <input type="text" name="negocio" class="form-input" required>
                    <label>Teléfono</label>
                    <input type="text" name="telefono" class="form-input" required>
                    <label>Detalle / Dirección</label>
                    <input type="text" name="direccion" class="form-input">
                    <label>Estado Inicial</label>
                    <input type="text" name="giro" class="form-input" value="Prospecto">
                    <button type="submit" class="btn-primary" style="width: 100%;">Guardar Cliente</button>
                </form>
            </div>
        </div>

        <div id="modalSeguimiento" class="modal">
            <div class="modal-content">
                <span class="close-modal" onclick="toggleModal('modalSeguimiento')">&times;</span>
                <h3>Agregar Seguimiento a: <span id="lblClienteSeguimiento" style="color:#3498db;"></span></h3>
                <form action="/guardar-seguimiento" method="post">
                    <input type="hidden" name="id_cliente" id="inputClienteId">
                    <label>Nombre del Asesor</label>
                    <input type="text" name="asesor" class="form-input" value="{request.session['usuario']}" readonly>
                    <label>Producto de Interés</label>
                    <input type="text" name="producto" class="form-input" required>
                    <label>Tipo de Interacción</label>
                    <input type="text" name="tipo" class="form-input" placeholder="Ej. WhatsApp, Llamada, Visita" required>
                    <label>Detalle del Seguimiento</label>
                    <textarea name="detalles" class="form-input" style="height:80px;" required></textarea>
                    <label>Estado Actual del Cliente</label>
                    <input type="text" name="estatus" class="form-input" value="En Proceso">
                    <button type="submit" class="btn-primary" style="width: 100%;">Registrar Seguimiento</button>
                </form>
            </div>
        </div>

        <div id="modalHistorial" class="modal">
            <div class="modal-content" style="width: 600px;">
                <span class="close-modal" onclick="toggleModal('modalHistorial')">&times;</span>
                <h3>Historial de Seguimientos: <span id="lblClienteHistorial" style="color:#3498db;"></span></h3>
                <div id="cronologiaHistorial" style="max-height: 400px; overflow-y: auto; padding-right: 10px;">
                    </div>
            </div>
        </div>

        <script>
            function toggleModal(id) {{
                var modal = document.getElementById(id);
                modal.style.display = (modal.style.display === 'flex') ? 'none' : 'flex';
            }}
            function abrirModalSeguimiento(id, nombre) {{
                document.getElementById('inputClienteId').value = id;
                document.getElementById('lblClienteSeguimiento').innerText = nombre;
                toggleModal('modalSeguimiento');
            }}
            function verHistorial(id, nombre) {{
                document.getElementById('lblClienteHistorial').innerText = nombre;
                var contenedor = document.getElementById('cronologiaHistorial');
                contenedor.innerHTML = '<p style="text-align:center; color:#7f8c8d;">Cargando historial...</p>';
                toggleModal('modalHistorial');
                
                fetch('/historial/' + id)
                    .then(response => response.json())
                    .then(data => {{
                        contenedor.innerHTML = '';
                        if(data.length === 0) {{
                            contenedor.innerHTML = '<p style="text-align:center; color:#7f8c8d; margin-top:20px;">No hay ningún seguimiento registrado para este cliente todavía.</p>';
                            return;
                        }}
                        data.forEach(seg => {{
                            var item = document.createElement('div');
                            item.style.borderBottom = '1px solid #eee';
                            item.style.padding = '12px 0';
                            item.innerHTML = '<div style="display:flex; justify-content:space-between; font-size:12px; color:#7f8c8d;"><span>📅 ' + seg.fecha + '</span><span>👤 Asesor: <strong>' + seg.asesor + '</strong></span></div>' +
                                             '<div style="margin: 6px 0; font-size:14px;">' + seg.detalle + '</div>' +
                                             '<div style="font-size:12px;"><span style="background:#eef1f4; padding:2px 6px; border-radius:4px; color:#34495e;">📦 ' + seg.producto + '</span> <span style="background:#e3f2fd; padding:2px 6px; border-radius:4px; color:#1565c0; margin-left:5px;">💬 ' + seg.tipo + '</span></div>';
                            contenedor.appendChild(item);
                        }});
                    }});
            }}
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/guardar-cliente")
def guardar_cliente(request: Request, nombre: str = Form(...), negocio: str = Form(...), telefono: str = Form(...), direccion: str = Form(""), giro: str = Form("")):
    if "usuario" not in request.session:
        return RedirectResponse(url="/login", status_code=303)
    registrar_cliente(nombre, negocio, telefono, direccion, giro)
    return RedirectResponse(url="/", status_code=303)

@app.post("/guardar-seguimiento")
def guardar_seguimiento(request: Request, id_cliente: int = Form(...), asesor: str = Form(...), producto: str = Form(...), tipo: str = Form(...), detalles: str = Form(...), estatus: str = Form(...)):
    if "usuario" not in request.session:
        return RedirectResponse(url="/login", status_code=303)
    registrar_seguimiento(id_cliente, asesor, producto, tipo, detalles, estatus)
    return RedirectResponse(url="/", status_code=303)

@app.get("/historial/{{id_cliente}}")
def historial_json(id_cliente: int, request: Request):
    if "usuario" not in request.session:
        return []
    historial = obtener_historial_cliente(id_cliente)
    resultado = []
    for h in historial:
        resultado.append({
            "fecha": h[0],
            "asesor": h[1],
            "producto": h[2],
            "tipo": h[3],
            "detalle": h[4],
            "estatus": h[5]
        })
    return resultado
