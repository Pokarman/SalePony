import streamlit as st
import pandas as pd
import os
import time
import random
import uuid
import hashlib
import re
import smtplib 
from email.mime.text import MIMEText 
from email.mime.multipart import MIMEMultipart 
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN GENERAL Y ESTILO ELITE
# ==========================================
st.set_page_config(page_title="SalePony Elite", page_icon="🦄", layout="wide")

# CSS AVANZADO: TEMA "ELITE GOLD & DARK"
st.markdown("""
    <style>
    /* IMPORTAR FUENTE ELEGANTE */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }

    /* COLOR DE ACENTO Y TÍTULOS */
    h1, h2, h3 {
        color: #D4AF37 !important; /* Oro Metálico */
        font-weight: 700;
        letter-spacing: 1px;
    }
    
    /* MËTRICAS (KPI CARDS) - ESTILO GLASSMORPHISM */
    div[data-testid="stMetric"] {
        background-color: rgba(30, 30, 30, 0.6);
        border: 1px solid #333;
        border-left: 5px solid #D4AF37;
        padding: 15px;
        border-radius: 10px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(212, 175, 55, 0.15);
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        color: #aaa !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #fff !important;
        font-weight: 600;
    }

    /* BOTONES PRIMARIOS DE LUJO */
    div.stButton > button:first-child {
        background: linear-gradient(145deg, #1a1a1a, #0d0d0d);
        color: #D4AF37;
        border: 1px solid #D4AF37;
        padding: 0.6em 1.2em;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        width: 100%;
    }
    div.stButton > button:hover {
        background: #D4AF37;
        color: #000;
        border-color: #D4AF37;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.4);
    }

    /* INPUTS Y FORMULARIOS */
    .stTextInput > div > div > input {
        background-color: #1E1E1E;
        color: #fff;
        border: 1px solid #444;
        border-radius: 6px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #D4AF37;
        box-shadow: 0 0 0 1px #D4AF37;
    }
    
    /* PESTAÑAS (TABS) ESTILIZADAS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 1px solid #333;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        color: #888;
        font-weight: 600;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        color: #D4AF37 !important;
        background-color: rgba(212, 175, 55, 0.1) !important;
        border-bottom: 2px solid #D4AF37 !important;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #0E0E0E;
        border-right: 1px solid #333;
    }
    
    /* ALERTA DE EXITO/ERROR ESTILIZADA */
    .stAlert {
        background-color: #1E1E1E;
        border: 1px solid #333;
        color: #fff;
        border-radius: 8px;
    }
    
    /* SEPARADOR */
    hr {
        border-color: #333;
        margin: 2em 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Nombres de archivos
ARCHIVO_INVENTARIO = 'mi_inventario.csv'
ARCHIVO_HISTORIAL = 'historial_movimientos.csv'
ARCHIVO_PEDIDOS = 'pedidos_pendientes.csv'
ARCHIVO_USUARIOS = 'usuarios_seguridad_v3.csv' 
ARCHIVO_CONFIG_API = 'config_apis.csv'

# ==========================================
# 2. GESTIÓN DE SEGURIDAD (HASHING & SANITIZACIÓN)
# ==========================================

def hash_password(password):
    """Convierte contraseña a Hash SHA-256."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def sanitizar_texto(texto):
    """Limpia entradas de caracteres peligrosos para CSV."""
    if isinstance(texto, str):
        return re.sub(r'[;,\n\r]', ' ', texto).strip()
    return texto

def cargar_usuarios():
    """Carga usuarios con contraseñas encriptadas."""
    if not os.path.exists(ARCHIVO_USUARIOS):
        usuarios_defecto = [
            {'Usuario': 'admin', 'Clave': hash_password('admin123'), 'Rol': 'Administrador', 'Nombre': 'CEO SalePony'},
            {'Usuario': 'operador', 'Clave': hash_password('op123'), 'Rol': 'Vendedor', 'Nombre': 'Operador Logístico'}
        ]
        df = pd.DataFrame(usuarios_defecto)
        df.to_csv(ARCHIVO_USUARIOS, index=False)
        return df
    return pd.read_csv(ARCHIVO_USUARIOS)

def verificar_login(usuario, clave_plana):
    """Verifica credenciales comparando HASHES."""
    df = cargar_usuarios()
    user_match = df[df['Usuario'] == usuario]
    
    if not user_match.empty:
        stored_hash = user_match.iloc[0]['Clave']
        input_hash = hash_password(clave_plana)
        if stored_hash == input_hash:
            return user_match.iloc[0]
    return None

if 'sesion_iniciada' not in st.session_state:
    st.session_state.sesion_iniciada = False
    st.session_state.rol_usuario = None
    st.session_state.nombre_usuario = None
    st.session_state.usuario_id = None
    st.session_state.ultimo_ticket = ""
    if 'contador_soporte' not in st.session_state:
        st.session_state.contador_soporte = 0

# ==========================================
# 3. LÓGICA DE NEGOCIO Y CORREO
# ==========================================

def enviar_correo_soporte(mensaje_error):
    """Envía reporte de error al correo del administrador."""
    sender_email = "alanbdb64@gmail.com"
    sender_password = "dxah wqco wygs bjgk".replace(" ", "") 
    receiver_email = "alanbdb64@gmail.com"

    msg = MIMEMultipart()
    msg['From'] = "SalePony System"
    msg['To'] = receiver_email
    msg['Subject'] = f"🚨 Reporte SalePony - {datetime.now().strftime('%d/%m %H:%M')}"

    cuerpo = f"""
    NUEVO REPORTE DE INCIDENCIA
    --------------------------------------
    Usuario: {st.session_state.nombre_usuario} ({st.session_state.rol_usuario})
    Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    DETALLE DEL REPORTE:
    {mensaje_error}
    --------------------------------------
    Sistema SalePony Gold
    """
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error de conexión con Gmail: {e}")
        return False

@st.cache_data(show_spinner=False)
def cargar_csv(archivo, columnas):
    if not os.path.exists(archivo): return pd.DataFrame(columns=columnas)
    try:
        df = pd.read_csv(archivo)
        if df.empty: return pd.DataFrame(columns=columnas)
        for col in columnas:
            if col not in df.columns:
                df[col] = 0.0 if "Precio" in col or "Costo" in col or "Cantidad" in col else ""
        return df
    except: return pd.DataFrame(columns=columnas)

def inicializar_catalogo_accesorios():
    if not os.path.exists(ARCHIVO_INVENTARIO):
        datos = [
            {'SKU': 'IP15-CASE-CLR', 'Categoria': 'Fundas', 'Modelo': 'Funda iPhone 15 Transparente Anti-Shock', 'Tipo': 'Importado', 'Cantidad': 20, 'Stock_Minimo': 5, 'Costo_Unitario': 35.0, 'Precio_Venta': 199.0, 'Link_AliExpress': 'https://aliexpress.com', 'Precio_ML': 249.0, 'Precio_Amazon': 229.0},
            {'SKU': 'IP-GLASS-9H', 'Categoria': 'Micas', 'Modelo': 'Cristal Templado 9H Universal (Pack 3)', 'Tipo': 'Importado', 'Cantidad': 50, 'Stock_Minimo': 10, 'Costo_Unitario': 18.0, 'Precio_Venta': 150.0, 'Link_AliExpress': '', 'Precio_ML': 199.0, 'Precio_Amazon': 180.0},
            {'SKU': 'SAM-A54-RUG', 'Categoria': 'Fundas', 'Modelo': 'Case Samsung A54 Uso Rudo Anillo', 'Tipo': 'Importado', 'Cantidad': 15, 'Stock_Minimo': 3, 'Costo_Unitario': 55.0, 'Precio_Venta': 280.0, 'Link_AliExpress': '', 'Precio_ML': 320.0, 'Precio_Amazon': 310.0},
            {'SKU': 'CAB-USBC-20W', 'Categoria': 'Cables', 'Modelo': 'Cable Carga Rápida USB-C 20W', 'Tipo': 'Importado', 'Cantidad': 30, 'Stock_Minimo': 8, 'Costo_Unitario': 25.0, 'Precio_Venta': 120.0, 'Link_AliExpress': '', 'Precio_ML': 150.0, 'Precio_Amazon': 160.0}
        ]
        df = pd.DataFrame(datos)
        df.to_csv(ARCHIVO_INVENTARIO, index=False)
        return df
    columnas = ['SKU', 'Categoria', 'Modelo', 'Tipo', 'Cantidad', 'Stock_Minimo', 'Costo_Unitario', 'Precio_Venta', 'Link_AliExpress', 'Precio_ML', 'Precio_Amazon']
    return cargar_csv(ARCHIVO_INVENTARIO, columnas)

def cargar_inventario():
    return inicializar_catalogo_accesorios()

def guardar_df(df, archivo):
    try:
        if not os.path.exists("respaldos"): os.makedirs("respaldos")
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base = os.path.splitext(os.path.basename(archivo))[0]
        if os.path.exists(archivo):
            try: pd.read_csv(archivo).to_csv(f"respaldos/{base}_BACKUP_{ts}.csv", index=False)
            except: pass
        df.to_csv(archivo, index=False)
        st.cache_data.clear()
    except Exception as e: st.error(f"Error al guardar: {e}")

def registrar_historial(accion, sku, modelo, cantidad, precio_venta=0, costo_unitario=0, notas=""):
    user = st.session_state.nombre_usuario if 'nombre_usuario' in st.session_state else "Sistema"
    venta = accion in ['VENTA', 'VENTA_AUTO', 'VENTA_MANUAL']
    compra = accion in ['ENTRADA', 'ALTA']
    
    nuevo = {
        'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Usuario': user, 'Accion': accion,
        'SKU': sku, 'Modelo': modelo, 'Cantidad': cantidad,
        'Monto_Venta': float(precio_venta) * int(cantidad) if venta else 0.0,
        'Costo_Venta': float(costo_unitario) * int(cantidad) if venta else 0.0,
        'Monto_Gasto': float(costo_unitario) * int(cantidad) if compra else 0.0,
        'Notas': notas
    }
    df_h = pd.DataFrame([nuevo])
    try:
        df_h.to_csv(ARCHIVO_HISTORIAL, mode='a' if os.path.exists(ARCHIVO_HISTORIAL) else 'w', header=not os.path.exists(ARCHIVO_HISTORIAL), index=False)
        st.cache_data.clear()
    except: pass

def generar_ticket(sku, modelo, cant, total, user):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    return f"""
--------------------------------
      SALE PONY ACCESORIOS      
--------------------------------
Fecha: {now}
Atendió: {user}
--------------------------------
{modelo[:18]:<18} x{cant} ${total:,.2f}
SKU: {sku}
--------------------------------
TOTAL:             ${total:,.2f}
--------------------------------
    ¡Gracias por su compra!
"""

def sincronizar_marketplaces(df_inv):
    nuevos = []
    msgs = ["🔵 Conectando Mercado Libre...", "🟠 Conectando Amazon..."]
    time.sleep(1.5)
    
    if not df_inv.empty and random.random() > 0.6: 
        stock = df_inv[df_inv['Cantidad'] > 0]
        if not stock.empty:
            prod = stock.sample(1).iloc[0]
            qty = random.randint(1, 2)
            plat = "Mercado Libre" if random.random() > 0.5 else "Amazon"
            if prod['Cantidad'] >= qty:
                nuevos.append({'Plataforma': plat, 'SKU': prod['SKU'], 'Modelo': prod['Modelo'], 'Cantidad': qty})
                msgs.append(f"✅ ¡Venta en {plat}! {prod['Modelo']}")
    return nuevos, msgs

def calcular_stats():
    if not os.path.exists(ARCHIVO_HISTORIAL): return None, None, pd.DataFrame()
    try: df = pd.read_csv(ARCHIVO_HISTORIAL)
    except: return None, None, pd.DataFrame()
    if df.empty: return None, None, pd.DataFrame()
    if 'Monto_Gasto' not in df.columns: df['Monto_Gasto'] = 0.0
    df['Fecha_Dt'] = pd.to_datetime(df['Fecha'])
    return df, None, df

# ==========================================
# 4. INTERFAZ GRÁFICA ELITE
# ==========================================

# --- LOGIN ---
if not st.session_state.sesion_iniciada:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>🦄 SalePony <span style='color:#fff'>Gold</span></h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Acceso al Sistema Integral</p>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("---")
            with st.form("login"):
                u = st.text_input("Usuario")
                p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("INGRESAR AL SISTEMA", use_container_width=True):
                    val = verificar_login(u, p)
                    if val is not None:
                        st.session_state.sesion_iniciada = True
                        st.session_state.rol_usuario = val['Rol']
                        st.session_state.nombre_usuario = val['Nombre']
                        st.session_state.usuario_id = val['Usuario']
                        st.rerun()
                    else: st.error("Acceso Denegado")
            st.caption("Admin: admin/admin123 | Op: operador/op123")

# --- APP ---
else:
    df_inv = cargar_inventario()
    df_ped = cargar_csv(ARCHIVO_PEDIDOS, ['ID_Pedido', 'Fecha', 'SKU', 'Modelo', 'Cantidad', 'Plataforma', 'Estado'])
    
    # --- SIDEBAR ELITE ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2316/2316680.png", width=50) # Icono Unicornio Opcional
        st.markdown(f"### Hola, {st.session_state.nombre_usuario}")
        st.caption(f"Rol: {st.session_state.rol_usuario}")
        st.divider()
        
        # MENÚS LATERALES
        with st.expander("🇨🇳 Importación"):
            costo = st.number_input("Costo China ($)", 0.0, step=10.0)
            envio = st.number_input("Envío/Imp ($)", 0.0, step=10.0)
            venta = st.number_input("P. Venta ($)", 0.0, step=10.0)
            if st.button("Calcular Margen"):
                total = costo + envio
                comision = venta * 0.15 
                ganancia = venta - total - comision
                if ganancia > 0: st.success(f"Ganancia: ${ganancia:,.2f}")
                else: st.error(f"Pérdida: ${ganancia:,.2f}")

        with st.expander("💰 Arqueo de Caja"):
            raw, _, df_full = calcular_stats()
            esperado = 0.0
            if df_full is not None and not df_full.empty:
                hoy = datetime.now().date()
                mask = (df_full['Fecha_Dt'].dt.date == hoy) & (df_full['Accion'].str.contains('VENTA')) & (df_full['Usuario'] == st.session_state.nombre_usuario)
                esperado = df_full[mask]['Monto_Venta'].sum()
            st.write(f"Esperado: ${esperado:,.2f}")
            real = st.number_input("Efectivo:", 0.0)
            if st.button("Validar Caja"):
                diff = real - esperado
                if diff == 0: st.success("✅ Cuadra")
                elif diff > 0: st.warning(f"⚠️ Sobra ${diff}")
                else: st.error(f"❌ Falta ${abs(diff)}")

        if st.session_state.rol_usuario == "Administrador":
            with st.expander("🔌 APIs"):
                ml_token_env = os.environ.get("ML_TOKEN", "")
                st.text_input("Mercado Libre ID", value=ml_token_env, type="password", placeholder="API KEY")
                st.text_input("Amazon Token", type="password", placeholder="TOKEN")

        st.markdown("---")
        if st.button("🔄 Sincronizar", type="primary"):
            with st.spinner("Conectando..."):
                news, logs = sincronizar_marketplaces(df_inv)
                if news:
                    for n in news:
                        idx = df_inv[df_inv['SKU']==n['SKU']].index[0]
                        df_inv.at[idx, 'Cantidad'] -= n['Cantidad']
                        new_p = {'ID_Pedido':f"ORD-{int(time.time())}", 'Fecha':datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'SKU':n['SKU'], 'Modelo':n['Modelo'], 'Cantidad':n['Cantidad'], 'Plataforma':n['Plataforma'], 'Estado':'Pendiente'}
                        df_ped = pd.concat([df_ped, pd.DataFrame([new_p])], ignore_index=True)
                        registrar_historial("VENTA_AUTO", n['SKU'], n['Modelo'], n['Cantidad'], 0, 0, f"Venta {n['Plataforma']}")
                    guardar_df(df_inv, ARCHIVO_INVENTARIO)
                    guardar_df(df_ped, ARCHIVO_PEDIDOS)
                    st.success(f"{len(news)} Pedidos!")
                    time.sleep(1)
                    st.rerun()
                else: st.info("Todo actualizado")

        # SOPORTE TÉCNICO
        with st.expander("📧 Soporte", expanded=False):
            key_dinamica = f"txt_soporte_{st.session_state.contador_soporte}"
            msg_error = st.text_area("Mensaje:", key=key_dinamica)
            if st.button("Enviar"):
                if msg_error:
                    with st.spinner("Enviando..."):
                        if enviar_correo_soporte(msg_error):
                            st.success("Enviado")
                            st.session_state.contador_soporte += 1
                            time.sleep(1)
                            st.rerun()

        if st.button("Salir"):
            st.session_state.sesion_iniciada = False
            st.rerun()

        # ZONA DE PELIGRO (Admin)
        if st.session_state.rol_usuario == "Administrador":
            with st.expander("⚠️ Zona Peligro", expanded=False):
                password_confirm = st.text_input("Clave Admin:", type="password")
                confirmar_reset = st.checkbox("Borrar Todo")
                btn_disabled = True
                if password_confirm and confirmar_reset:
                    user_data = verificar_login(st.session_state.usuario_id, password_confirm)
                    if user_data is not None: btn_disabled = False
                    else: st.error("Clave mal")
                if st.button("🗑️ Resetear", disabled=btn_disabled, type="primary"):
                    if os.path.exists(ARCHIVO_HISTORIAL): os.remove(ARCHIVO_HISTORIAL)
                    if os.path.exists(ARCHIVO_PEDIDOS): os.remove(ARCHIVO_PEDIDOS)
                    st.cache_data.clear()
                    st.success("Limpio")
                    time.sleep(1)
                    st.rerun()

    # --- HEADER DASHBOARD ---
    st.title("🦄 SalePony Gold")
    
    # KPIs SUPERIORES
    pend = df_ped[df_ped['Estado']=='Pendiente'].shape[0]
    low = df_inv[df_inv['Cantidad'] <= df_inv['Stock_Minimo']].shape[0]
    raw, _, df_full = calcular_stats()
    ventas_hoy = 0
    if df_full is not None and not df_full.empty:
        hoy = datetime.now().date()
        m = df_full[(df_full['Fecha_Dt'].dt.date == hoy) & (df_full['Accion'].str.contains('VENTA'))]
        ventas_hoy = m['Monto_Venta'].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ventas Hoy", f"${ventas_hoy:,.2f}")
    col2.metric("Envíos Pendientes", pend, delta_color="inverse" if pend>0 else "normal")
    col3.metric("Stock Bajo", low, delta_color="inverse")
    col4.metric("Estado", "Operativo 🟢")

    st.divider()

    # --- CONTENIDO PRINCIPAL ---
    tabs = st.tabs(["📦 PEDIDOS WEB", "🛒 PUNTO DE VENTA", "📱 INVENTARIO", "📝 ADMIN", "📊 REPORTES"]) if st.session_state.rol_usuario == "Administrador" else st.tabs(["📦 PEDIDOS WEB", "🛒 PUNTO DE VENTA", "📱 CONSULTAR"])
    
    t_ped, t_pos, t_inv = tabs[0], tabs[1], tabs[2]
    t_adm = tabs[3] if len(tabs) > 3 else None
    t_rep = tabs[4] if len(tabs) > 3 else None

    # 1. PEDIDOS WEB
    with t_ped:
        st.subheader("Gestión de Envíos")
        p_list = df_ped[df_ped['Estado']=='Pendiente']
        if p_list.empty: st.info("✅ Todo limpio.")
        else:
            for i, r in p_list.iterrows():
                with st.container():
                    c1, c2, c3, c4 = st.columns([1,3,2,2])
                    icon = "🟡" if r['Plataforma']=="Mercado Libre" else "🟠"
                    c1.markdown(f"## {icon}")
                    c2.markdown(f"**{r['Modelo']}**")
                    c2.caption(f"SKU: {r['SKU']} | Cant: **x{r['Cantidad']}**")
                    c3.text(f"ID: {r['ID_Pedido']}")
                    if c4.button("Enviado ✅", key=r['ID_Pedido']):
                        df_ped.loc[df_ped['ID_Pedido']==r['ID_Pedido'], 'Estado']='Enviado'
                        guardar_df(df_ped, ARCHIVO_PEDIDOS)
                        st.toast("Enviado")
                        time.sleep(0.5)
                        st.rerun()
                    st.divider()

    # 2. PUNTO DE VENTA
    with t_pos:
        c_izq, c_der = st.columns([2, 1])
        with c_izq:
            st.subheader("Venta Mostrador")
            scan = st.text_input("🔫 Escáner SKU", placeholder="Clic aquí...")
            sel = None
            if scan:
                scan_clean = sanitizar_texto(scan) 
                f = df_inv[df_inv['SKU'].astype(str) == scan_clean]
                if not f.empty:
                    sel = f.iloc[0]
                    st.success(f"Producto: {sel['Modelo']}")
                else: st.warning("No encontrado")
            
            if not df_inv.empty:
                ok = df_inv[df_inv['Cantidad'] > 0]
                if sel is None:
                    op = ok.apply(lambda x: f"{x['Modelo']} | {x['SKU']}", axis=1)
                    s = st.selectbox("Búsqueda Manual", op)
                    sel = df_inv[df_inv['SKU'] == s.split(" | ")[1]].iloc[0] if s else None
                
                if sel is not None:
                    idx = df_inv[df_inv['SKU'] == sel['SKU']].index[0]
                    item = df_inv.iloc[idx]
                    stock_real = int(item['Cantidad'])
                    
                    st.markdown(f"**{item['Modelo']}** | Disp: {item['Cantidad']}")
                    cq, cp = st.columns(2)
                    q = cq.number_input("Cantidad", 1, max(1, stock_real), 1)
                    tot = item['Precio_Venta'] * q
                    cp.metric("Total", f"${tot:,.2f}")
                    
                    if st.button("COBRAR", type="primary", use_container_width=True):
                        if q > stock_real:
                            st.error("⛔ ERROR: Stock insuficiente.")
                        else:
                            df_inv.at[idx, 'Cantidad'] -= q
                            guardar_df(df_inv, ARCHIVO_INVENTARIO)
                            registrar_historial("VENTA", item['SKU'], item['Modelo'], q, item['Precio_Venta'], item['Costo_Unitario'], "Mostrador")
                            st.session_state.ultimo_ticket = generar_ticket(item['SKU'], item['Modelo'], q, tot, st.session_state.nombre_usuario)
                            st.success("Venta OK")
                            time.sleep(0.5)
                            st.rerun()
        with c_der:
            st.markdown("🧾 **Ticket**")
            if st.session_state.ultimo_ticket:
                st.text_area("", st.session_state.ultimo_ticket, height=300)
                st.download_button("Descargar", st.session_state.ultimo_ticket, "ticket.txt")

    # 3. INVENTARIO
    with t_inv:
        st.subheader("Inventario")
        cols = ['SKU', 'Modelo', 'Cantidad', 'Stock_Minimo', 'Link_AliExpress', 'Precio_ML', 'Precio_Amazon']
        st.dataframe(df_inv[cols], use_container_width=True, column_config={"Link_AliExpress": st.column_config.LinkColumn("AliExpress")})

    # 4. ADMIN
    if t_adm:
        with t_adm:
            st.subheader("Gestión")
            act = st.radio("Acción", ["Nuevo", "Clonar", "Editar Info", "Ajuste Stock"], horizontal=True)
            d_sku, d_mod, d_cat, d_cos, d_pre, d_can, d_link, d_ml, d_amz = "", "", "Fundas", 0.0, 0.0, 0, "", 0.0, 0.0
            idx_e = -1
            if act != "Nuevo" and not df_inv.empty:
                s_ed = st.selectbox("Seleccionar:", df_inv['Modelo'].unique())
                idx_e = df_inv[df_inv['Modelo']==s_ed].index[0]
                row = df_inv.iloc[idx_e]
                d_mod = row['Modelo'] + (" (Copia)" if act=="Clonar" else "")
                d_sku = "" if act=="Clonar" else row['SKU']
                d_cat, d_can = row['Categoria'], int(row['Cantidad'])
                d_cos, d_pre = float(row['Costo_Unitario']), float(row['Precio_Venta'])
                d_link, d_ml, d_amz = row['Link_AliExpress'], float(row['Precio_ML']), float(row['Precio_Amazon'])

            with st.form("admin_p"):
                c1, c2 = st.columns(2)
                f_sku = c1.text_input("SKU", d_sku, disabled=(act in ["Editar Info", "Ajuste Stock"]))
                f_mod = c2.text_input("Modelo", d_mod, disabled=(act=="Ajuste Stock"))
                c3, c4, c5 = st.columns(3)
                f_cat = c3.selectbox("Cat.", ["Fundas", "Micas", "Cargadores", "Cables", "Otro"], index=0)
                f_can = c4.number_input("Stock", value=d_can)
                f_min = c5.number_input("Mínimo", 5)
                c6, c7, c8 = st.columns(3)
                f_cos = c6.number_input("Costo", value=d_cos)
                f_pre = c7.number_input("P. Venta", value=d_pre)
                f_lnk = c8.text_input("Link Ali", d_link)
                c9, c10 = st.columns(2)
                f_ml = c9.number_input("Precio ML", value=d_ml)
                f_amz = c10.number_input("Precio Amz", value=d_amz)
                if st.form_submit_button("Guardar"):
                    if not f_mod: st.error("Falta nombre")
                    else:
                        f_mod = sanitizar_texto(f_mod)
                        f_sku = sanitizar_texto(f_sku)
                        if not f_sku: f_sku = f"ACC-{str(uuid.uuid4())[:6].upper()}"
                        new_d = {'SKU': f_sku, 'Categoria': f_cat, 'Modelo': f_mod, 'Tipo': 'Imp', 'Cantidad': f_can, 'Stock_Minimo': f_min, 'Costo_Unitario': f_cos, 'Precio_Venta': f_pre, 'Link_AliExpress': f_lnk, 'Precio_ML': f_ml, 'Precio_Amazon': f_amz}
                        if act in ["Editar Info", "Ajuste Stock"] and idx_e != -1:
                            diff = f_can - df_inv.at[idx_e, 'Cantidad']
                            for k,v in new_d.items(): df_inv.at[idx_e, k] = v
                            guardar_df(df_inv, ARCHIVO_INVENTARIO)
                            registrar_historial("EDICION", f_sku, f_mod, abs(diff), 0, 0, f"Ajuste {diff}")
                            st.success("Guardado")
                        else:
                            df_inv = pd.concat([df_inv, pd.DataFrame([new_d])], ignore_index=True)
                            guardar_df(df_inv, ARCHIVO_INVENTARIO)
                            registrar_historial("ALTA", f_sku, f_mod, f_can, 0, f_cos, "Alta")
                            st.success("Creado")
                        time.sleep(1)
                        st.rerun()

    # 5. REPORTES
    if t_rep:
        with t_rep:
            st.subheader("Finanzas")
            freq = st.radio("Ver por:", ["Día", "Mes"], horizontal=True)
            if df_full is not None and not df_full.empty:
                df_c = df_full.copy()
                grp = df_c['Fecha_Dt'].dt.date if freq=="Día" else df_c['Fecha_Dt'].dt.strftime('%Y-%m')
                st.markdown("### 1. Flujo de Caja")
                tab = df_c.groupby(grp)[['Monto_Venta', 'Monto_Gasto']].sum()
                tab.columns = ['Ventas', 'Compras']
                tab['Neto'] = tab['Ventas'] - tab['Compras']
                st.dataframe(tab.style.format("${:,.2f}"), use_container_width=True)
                st.divider()
                st.markdown("### 2. Rentabilidad Real")
                c1, c2 = st.columns(2)
                imp_pct = c1.number_input("Impuestos %", 16.0) / 100
                com_pct = c2.number_input("Comisión %", 15.0) / 100
                vs = df_c[df_c['Accion'].str.contains('VENTA')]
                if not vs.empty:
                    tot_v = vs['Monto_Venta'].sum()
                    tot_c = vs['Costo_Venta'].sum()
                    bruta = tot_v - tot_c
                    gastos = tot_v * (imp_pct + com_pct)
                    neta = bruta - gastos
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Venta Total", f"${tot_v:,.2f}")
                    m2.metric("Costo Prod.", f"-${tot_c:,.2f}")
                    m3.metric("Utilidad Bruta", f"${bruta:,.2f}")
                    m4, m5, m6 = st.columns(3)
                    m4.metric("Impuestos/Comis", f"-${gastos:,.2f}")
                    m5.metric("💰 GANANCIA LIBRE", f"${neta:,.2f}")
                    if tot_v > 0: m6.metric("Margen", f"{(neta/tot_v)*100:.1f}%")
                else: st.info("Sin ventas")
            else: st.info("Sin datos")
