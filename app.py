from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn
from funciones_crm import obtener_clientes, registrar_cliente, registrar_seguimiento, obtener_historial_cliente, inicializar_base_de_datos
app = FastAPI(title="Corporación Castiel CRM")
inicializar_base_de_datos()

@app.get("/", response_class=HTMLResponse)
def index():
    clientes = obtener_clientes()
    
    # Aquí embebemos el diseño que te gustó, pero ahora es dinámico
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Panel de Control - Corporación Castiel S.A.</title>
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
        <script src="https://unpkg.com/lucide@latest"></script>
        <style>
            :root {{ --azul-corp: #0B3C5D; --azul-oscuro: #062337; --gris-fondo: #F5F7FA; }}
        </style>
    </head>
    <body class="bg-[var(--gris-fondo)] text-gray-800 font-sans flex h-screen overflow-hidden">

        <aside class="w-64 bg-white border-r border-gray-200 flex flex-col justify-between shadow-sm">
            <div>
                <div class="p-6 border-b border-gray-100 text-center">
                    <div class="text-[var(--azul-corp)] font-bold text-lg tracking-wider">CORPORACIÓN</div>
                    <div class="text-[var(--azul-oscuro)] font-black text-2xl tracking-widest -mt-1">CASTIEL</div>
                    <div class="text-gray-400 text-[10px] tracking-widest uppercase border-t border-gray-100 mt-1 pt-1">
                        INTEGRIDAD • VISIÓN • LIDERAZGO
                    </div>
                </div>
                <nav class="p-4 space-y-1">
                    <a href="/" class="flex items-center space-x-3 px-4 py-3 rounded-lg bg-blue-50 text-[var(--azul-corp)] font-medium">
                        <i data-lucide="users" class="w-5 h-5"></i>
                        <span>Lista de Clientes</span>
                    </a>
                </nav>
            </div>
            <div class="p-4 border-t border-gray-100 text-xs text-gray-400 text-center">Castiel CRM v1.1</div>
        </aside>

        <main class="flex-1 flex flex-col overflow-hidden">
            <header class="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-8 shadow-xs">
                <h1 class="text-xl font-bold text-gray-800">Panel de Control de Clientes</h1>
                <button onclick="toggleModal('modalCliente')" class="bg-[var(--azul-corp)] hover:bg-[var(--azul-oscuro)] text-white font-medium px-4 py-2 rounded-lg text-sm transition flex items-center space-x-2">
                    <i data-lucide="user-plus" class="w-4 h-4"></i>
                    <span>Nuevo Cliente</span>
                </button>
            </header>

            <div class="flex-1 overflow-y-auto p-8 space-y-6">
                <div class="bg-white rounded-xl border border-gray-200 shadow-xs overflow-hidden">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-gray-100/70 border-b border-gray-200 text-xs font-semibold uppercase text-gray-600 tracking-wider">
                                <th class="py-3 px-6">ID</th>
                                <th class="py-3 px-6">Cliente</th>
                                <th class="py-3 px-6">Negocio</th>
                                <th class="py-3 px-6">Teléfono</th>
                                <th class="py-3 px-6">Dirección</th>
                                <th class="py-3 px-6">Giro</th>
                                <th class="py-3 px-6">Acciones</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100 text-sm">
    """
    
    for c in clientes:
        html_content += f"""
                            <tr class="hover:bg-gray-50/80 transition">
                                <td class="py-4 px-6 font-bold text-[var(--azul-corp)]">#{c[0]}</td>
                                <td class="py-4 px-6 font-medium text-gray-900">{c[1]}</td>
                                <td class="py-4 px-6 text-gray-600">{c[2]}</td>
                                <td class="py-4 px-6 text-gray-600">{c[3]}</td>
                                <td class="py-4 px-6 text-gray-600">{c[4]}</td>
                                <td class="py-4 px-6 text-gray-600">{c[5]}</td>
                                <td class="py-4 px-6">
                                    <button onclick="abrirSeguimiento({c[0]}, '{c[2]}')" class="text-xs bg-gray-100 hover:bg-blue-100 hover:text-[var(--azul-corp)] px-3 py-1.5 rounded-md font-medium transition flex items-center space-x-1">
                                        <i data-lucide="plus-circle" class="w-3.5 h-3.5"></i>
                                        <span>Historial / Agregar</span>
                                    </button>
                                </td>
                            </tr>
        """
        
    html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
        </main>

        <div id="modalCliente" class="hidden fixed inset-0 bg-black/50 flex items-center justify-center p-4">
            <div class="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden">
                <div class="bg-[var(--azul-corp)] text-white p-4 font-bold">Registrar Nuevo Cliente</div>
                <form action="/guardar-cliente" method="POST" class="p-6 space-y-4">
                    <div><label class="block text-xs font-semibold uppercase text-gray-500 mb-1">Nombre del Cliente</label><input type="text" name="nombre" required class="w-full p-2 border border-gray-300 rounded-lg text-sm"></div>
                    <div><label class="block text-xs font-semibold uppercase text-gray-500 mb-1">Nombre del Negocio</label><input type="text" name="negocio" required class="w-full p-2 border border-gray-300 rounded-lg text-sm"></div>
                    <div><label class="block text-xs font-semibold uppercase text-gray-500 mb-1">Teléfono</label><input type="text" name="telefono" class="w-full p-2 border border-gray-300 rounded-lg text-sm"></div>
                    <div><label class="block text-xs font-semibold uppercase text-gray-500 mb-1">Dirección</label><input type="text" name="direccion" class="w-full p-2 border border-gray-300 rounded-lg text-sm"></div>
                    <div><label class="block text-xs font-semibold uppercase text-gray-500 mb-1">Giro de Negocio</label><input type="text" name="giro" class="w-full p-2 border border-gray-300 rounded-lg text-sm"></div>
                    <div class="flex justify-end space-x-3 pt-2">
                        <button type="button" onclick="toggleModal('modalCliente')" class="px-4 py-2 text-sm font-medium text-gray-500 hover:bg-gray-100 rounded-lg">Cancelar</button>
                        <button type="submit" class="px-4 py-2 text-sm font-medium bg-[var(--azul-corp)] text-white rounded-lg hover:bg-[var(--azul-oscuro)]">Guardar Cliente</button>
                    </div>
                </form>
            </div>
        </div>

        <div id="modalSeguimiento" class="hidden fixed inset-0 bg-black/50 flex items-center justify-center p-4">
            <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[85vh]">
                <div class="bg-[var(--azul-oscuro)] text-white p-4 font-bold flex justify-between items-center">
                    <span id="seguimientoTitulo">Seguimiento</span>
                    <button onclick="toggleModal('modalSeguimiento')" class="text-white hover:text-gray-300">✕</button>
                </div>
                
                <div class="p-6 overflow-y-auto space-y-6 flex-1">
                    <form action="/guardar-seguimiento" method="POST" class="bg-gray-50 p-4 rounded-xl border border-gray-200 grid grid-cols-2 gap-4">
                        <input type="hidden" name="id_cliente" id="seg_id_cliente">
                        <div>
                            <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Asesor Responsable</label>
                            <input type="text" name="asesor" placeholder="Ej. Luis Gómez" required class="w-full p-2 bg-white border border-gray-300 rounded-lg text-sm">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Producto / Servicio de Interés</label>
                            <select name="producto" class="w-full p-2 bg-white border border-gray-300 rounded-lg text-sm">
                                <option value="PocketApp">PocketApp (Punto de Venta)</option>
                                <option value="Chispudo">Chispudo (Punto de Venta)</option>
                                <option value="Equipo POS">Equipo POS (Computadora/Tablet/Post)</option>
                                <option value="Software + Equipo">Combo: Software + Equipo POS</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Tipo de Interacción</label>
                            <select name="tipo" class="w-full p-2 bg-white border border-gray-300 rounded-lg text-sm">
                                <option value="WhatsApp">WhatsApp</option>
                                <option value="Llamada">Llamada Telefónica</option>
                                <option value="Visita">Visita Presencial</option>
                                <option value="Demo">Demostración de Sistema</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Estatus actual</label>
                            <select name="estatus" class="w-full p-2 bg-white border border-gray-300 rounded-lg text-sm">
                                <option value="Interesado">Interesado / En Proceso</option>
                                <option value="Cotizado">Cotizado</option>
                                <option value="Venta Exitosa">Venta Cerrada (Éxito)</option>
                                <option value="No interesado">No interesado</option>
                            </select>
                        </div>
                        <div class="col-span-2">
                            <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Detalles de la Conversación (Secuencia)</label>
                            <textarea name="detalles" rows="2" placeholder="Escribe aquí los acuerdos, dudas del cliente o siguientes pasos..." required class="w-full p-2 bg-white border border-gray-300 rounded-lg text-sm"></textarea>
                        </div>
                        <div class="col-span-2 flex justify-end">
                            <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition">Registrar Interacción</button>
                        </div>
                    </form>

                    <div>
                        <h4 class="font-bold text-gray-700 text-sm mb-3 uppercase tracking-wider">Línea de Tiempo del Cliente</h4>
                        <div id="historialContenedor" class="space-y-4 border-l-2 border-gray-100 pl-6 ml-3">
                            </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            lucide.createIcons();
            function toggleModal(id) {
                document.getElementById(id).classList.toggle('hidden');
            }
            function abrirSeguimiento(id, negocio) {
                document.getElementById('seg_id_cliente').value = id;
                document.getElementById('seguimientoTitulo').innerText = "Historial de Seguimiento: " + negocio;
                
                // Llamamos al servidor para traer la secuencia de este cliente de forma asíncrona
                fetch('/historial/' + id)
                    .then(res => res.json())
                    .then(data => {
                        const contenedor = document.getElementById('historialContenedor');
                        contenedor.innerHTML = "";
                        if(data.length === 0) {
                            contenedor.innerHTML = "<p class='text-sm text-gray-400 italic'>No hay registros de seguimiento aún para este cliente.</p>";
                        }
                        data.forEach(reg => {
                            contenedor.innerHTML += `
                                <div class="relative">
                                    <div class="absolute -left-[31px] top-1.5 w-4 h-4 bg-blue-500 rounded-full border-4 border-white"></div>
                                    <div class="text-xs font-semibold text-gray-400">${reg.fecha}</div>
                                    <div class="bg-gray-50 p-4 rounded-lg border border-gray-100 mt-1 text-sm">
                                        <div class="grid grid-cols-2 gap-2 mb-1">
                                            <div><strong>Asesor:</strong> ${reg.asesor}</div>
                                            <div><strong>Producto:</strong> <span class="text-blue-700 font-medium">${reg.producto}</span></div>
                                            <div><strong>Vía:</strong> ${reg.tipo}</div>
                                            <div><strong>Estado:</strong> <span class="px-2 py-0.5 text-xs bg-amber-100 text-amber-800 rounded font-bold">${reg.estatus}</span></div>
                                        </div>
                                        <p class="text-gray-600 border-t border-gray-200 pt-1.5 mt-1.5"><strong>Detalles:</strong> ${reg.detalles}</p>
                                    </div>
                                </div>
                            `;
                        });
                    });
                toggleModal('modalSeguimiento');
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/guardar-cliente")
def guardar_cliente(nombre: str = Form(...), negocio: str = Form(...), telefono: str = Form(""), direccion: str = Form(""), giro: str = Form("")):
    registrar_cliente(nombre, negocio, telefono, direccion, giro)
    return RedirectResponse(url="/", status_code=303)

@app.post("/guardar-seguimiento")
def guardar_seguimiento(id_cliente: int = Form(...), asesor: str = Form(...), producto: str = Form(...), tipo: str = Form(...), detalles: str = Form(...), estatus: str = Form(...)):
    registrar_seguimiento(id_cliente, asesor, producto, tipo, detalles, estatus)
    return RedirectResponse(url="/", status_code=303)

@app.get("/historial/{id_cliente}")
def historial_cliente(id_cliente: int):
    historial = obtener_historial_cliente(id_cliente)
    # Formateamos la respuesta para que JavaScript la lea fácil
    return [{"fecha": h[0], "asesor": h[1], "producto": h[2], "tipo": h[3], "detalles": h[4], "estatus": h[5]} for h in historial]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
