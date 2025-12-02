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
# 1. CONFIGURACIÓN VISUAL "ELITE DARK GOLD"
# ==========================================
st.set_page_config(page_title="SalePony Elite", page_icon="🦄", layout="wide")

# Inyección de CSS Profesional
st.markdown("""
    <style>
    /* IMPORTAR FUENTE MODERNA */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    /* FONDO Y COLORES GENERALES PARA ARMONÍA DARK/LIGHT */
    .stApp {
        background-color: #0E1117; /* Fondo oscuro profundo */
    }

    /* TÍTULOS CON GRADIENTE DORADO DE LUJO */
    h1, h2, h3 {
        background: linear-gradient(90deg, #F9D423 0%, #FF4E50 100%); /* Opción fuego/oro */
        background: linear-gradient(to right, #bf953f, #fcf6ba, #b38728, #fbf5b7, #aa771c); /* Oro Real */
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
    }

    /* CONTENEDORES Y TARJETAS (LOGIN Y MÉTRICAS) */
    .css-1r6slb0, .css-12oz5g7 { 
        background-color: #1E1E1E;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* INPUTS (CAJAS DE TEXTO) - NO MÁS BLANCO PURO */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #262730 !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #D4AF37 !important;
        box-shadow: 0 0 0 1px #D4AF37 !important;
    }

    /* BOTONES PREMIUM (MEJORA 4 - INTERACCIONES) */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        background: linear-gradient(145deg, #D4AF37, #C5A059);
        color: #000000 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 7px 14px rgba(212, 175, 55, 0.4);
        background: linear-gradient(145deg, #FDD835, #FBC02D);
    }
    .stButton > button:active {
        transform: translateY(1px);
    }

    /* TABLAS VIVAS (MEJORA 3) */
    div[data-testid="stDataFrame"] {
        border: 1px solid #333;
        border-radius: 10px;
        overflow: hidden;
    }

    /* LOGIN CARD ESTILIZADA */
    .login-container {
        padding: 2rem;
        border-radius: 20px;
        background: rgba(30, 30, 30, 0.8);
        border: 1px solid #D4AF37;
        box-shadow: 0 0 50px rgba(212, 175, 55, 0.1);
    }

    /* ALINEACIÓN DE BOTONES */
    div.row-widget.stButton {
        text-align: center;
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
# 2. LÓGICA DE NEGOCIO Y SEGURIDAD (INTACTA)
# ==========================================

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def sanitizar_texto(texto):
    if isinstance(texto, str):
        return re.sub(r'[;,\n\r]', ' ', texto).strip()
    return texto

def cargar_usuarios():
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
    if 'contador_soporte' not in st.session_state: st.session_state.contador_soporte = 0

def enviar_correo_soporte(mensaje_error):
    sender_email = "alanbdb64@gmail.com"
    sender_password = "dxah wqco wygs bjgk".replace(" ", "")
    receiver_email = "alanbdb64@gmail.com"
    msg = MIMEMultipart()
    msg['From'] = "SalePony System"
    msg['To'] = receiver_email
    msg['Subject'] = f"🚨 Reporte SalePony - {datetime.now().strftime('%d/%m %H:%M')}"
    cuerpo = f"Usuario: {st.session_state.nombre_usuario}\nError: {mensaje_error}"
    msg.attach(MIMEText(cuerpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except: return False

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
    except: pass

def registrar_historial(accion, sku, modelo, cantidad, precio_venta=0, costo_unitario=0, notas=""):
    user = st.session_state.nombre_usuario if 'nombre_usuario' in st.session_state else "Sistema"
    venta = accion in ['VENTA', 'VENTA_AUTO', 'VENTA_MANUAL']
    compra = accion in ['ENTRADA', 'ALTA']
    nuevo = {'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Usuario': user, 'Accion': accion, 'SKU': sku, 'Modelo': modelo, 'Cantidad': cantidad, 'Monto_Venta': float(precio_venta) * int(cantidad) if venta else 0.0, 'Costo_Venta': float(costo_unitario) * int(cantidad) if venta else 0.0, 'Monto_Gasto': float(costo_unitario) * int(cantidad) if compra else 0.0, 'Notas': notas}
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
    msgs = ["🔵 Mercado Libre...", "🟠 Amazon..."]
    time.sleep(1.5)
    if not df_inv.empty and random.random() > 0.6: 
        stock = df_inv[df_inv['Cantidad'] > 0]
        if not stock.empty:
            prod = stock.sample(1).iloc[0]
            qty = random.randint(1, 2)
            plat = "Mercado Libre" if random.random() > 0.5 else "Amazon"
            if prod['Cantidad'] >= qty:
                nuevos.append({'Plataforma': plat, 'SKU': prod['SKU'], 'Modelo': prod['Modelo'], 'Cantidad': qty})
                msgs.append(f"✅ Venta {plat}: {prod['Modelo']}")
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
# 4. INTERFAZ GRÁFICA (MEJORA 5 y 7)
# ==========================================

# --- PANTALLA DE LOGIN SAAS (MEJORA 5) ---
if not st.session_state.sesion_iniciada:
    # Centrado vertical y horizontal usando columnas vacías
    c_void_1, c_login, c_void_2 = st.columns([1, 2, 1])
    
    with c_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Contenedor visual tipo Tarjeta
        with st.container():
            st.markdown("""
            <div class="login-container">
                <h1 style='text-align: center; margin-bottom: 0;'>🦄 SalePony</h1>
                <p style='text-align: center; color: #D4AF37; letter-spacing: 2px; font-size: 0.9em;'>ELITE EDITION</p>
                <hr style='border-color: #444;'>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                u = st.text_input("Usuario", placeholder="Ej: admin")
                p = st.text_input("Contraseña", type="password", placeholder="••••••••")
                
                st.markdown("<br>", unsafe_allow_html=True)
                # Botón de ancho completo
                if st.form_submit_button("ACCEDER AL SISTEMA"):
                    val = verificar_login(u, p)
                    if val is not None:
                        st.session_state.sesion_iniciada = True
                        st.session_state.rol_usuario = val['Rol']
                        st.session_state.nombre_usuario = val['Nombre']
                        st.session_state.usuario_id = val['Usuario']
                        st.rerun()
                    else: st.error("❌ Credenciales incorrectas")
            
            st.markdown("<p style='text-align: center; color: #666; font-size: 0.8em; margin-top: 20px;'>Admin: admin/admin123 | Op: operador/op123</p>", unsafe_allow_html=True)

# --- APLICACIÓN PRINCIPAL ---
else:
    df_inv = cargar_inventario()
    df_ped = cargar_csv(ARCHIVO_PEDIDOS, ['ID_Pedido', 'Fecha', 'SKU', 'Modelo', 'Cantidad', 'Plataforma', 'Estado'])
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 👋 Hola, {st.session_state.nombre_usuario}")
        st.caption(f"Rol: **{st.session_state.rol_usuario}**")
        st.divider()
        
        # MENÚS COLAPSABLES LIMPIOS
        with st.expander("📥 Importación China"):
            costo = st.number_input("Costo ($)", 0.0, step=10.0)
            envio = st.number_input("Envío ($)", 0.0, step=10.0)
            venta = st.number_input("Venta ($)", 0.0, step=10.0)
            if st.button("Calcular"):
                ganancia = venta - (costo + envio) - (venta * 0.15)
                if ganancia > 0: st.success(f"Ganas: ${ganancia:,.2f}")
                else: st.error(f"Pierdes: ${ganancia:,.2f}")

        with st.expander("💵 Arqueo de Caja"):
            raw, _, df_full = calcular_stats()
            esperado = 0.0
            if df_full is not None and not df_full.empty:
                hoy = datetime.now().date()
                mask = (df_full['Fecha_Dt'].dt.date == hoy) & (df_full['Accion'].str.contains('VENTA')) & (df_full['Usuario'] == st.session_state.nombre_usuario)
                esperado = df_full[mask]['Monto_Venta'].sum()
            st.markdown(f"**Sistema:** ${esperado:,.2f}")
            real = st.number_input("Real:", 0.0)
            if st.button("Validar"):
                diff = real - esperado
                if diff == 0: st.success("✅ Correcto")
                else: st.warning(f"Diferencia: ${diff:,.2f}")

        if st.session_state.rol_usuario == "Administrador":
            with st.expander("🔌 APIs"):
                ml_token_env = os.environ.get("ML_TOKEN", "")
                st.text_input("Mercado Libre ID", value=ml_token_env, type="password", placeholder="API KEY")
                st.text_input("Amazon Token", type="password", placeholder="TOKEN")

        st.markdown("---")
        if st.button("🔄 Sincronizar Nube"):
            with st.spinner("Descargando pedidos..."):
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
                    st.success(f"¡{len(news)} Pedidos Nuevos!")
                    time.sleep(1)
                    st.rerun()
                else: st.info("Todo al día")

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

        if st.button("Cerrar Sesión"):
            st.session_state.sesion_iniciada = False
            st.rerun()

        if st.session_state.rol_usuario == "Administrador":
            with st.expander("⚠️ Reset", expanded=False):
                if st.button("Borrar Datos"):
                    if os.path.exists(ARCHIVO_HISTORIAL): os.remove(ARCHIVO_HISTORIAL)
                    st.cache_data.clear()
                    st.rerun()

    # --- HEADER DASHBOARD (MEJORA 7) ---
    col_logo, col_title = st.columns([1, 10])
    with col_logo:
        st.write("🦄") # Aquí iría tu logo en imagen
    with col_title:
        st.markdown("# SalePony Dashboard")
    
    # KPIs SUPERIORES
    pend = df_ped[df_ped['Estado']=='Pendiente'].shape[0]
    low = df_inv[df_inv['Cantidad'] <= df_inv['Stock_Minimo']].shape[0]
    raw, _, df_full = calcular_stats()
    ventas_hoy = 0
    if df_full is not None and not df_full.empty:
        hoy = datetime.now().date()
        m = df_full[(df_full['Fecha_Dt'].dt.date == hoy) & (df_full['Accion'].str.contains('VENTA'))]
        ventas_hoy = m['Monto_Venta'].sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ventas Hoy", f"${ventas_hoy:,.2f}")
    k2.metric("Envíos Pendientes", pend, delta_color="inverse" if pend>0 else "normal")
    k3.metric("Stock Bajo", low, delta_color="inverse")
    k4.metric("Marketplaces", "🟢 ONLINE")

    st.markdown("<br>", unsafe_allow_html=True) # Espacio visual

    # --- PESTAÑAS (MEJORA 7 - ORDENADO) ---
    tabs = st.tabs(["📦 PEDIDOS WEB", "🛒 PUNTO DE VENTA", "📱 INVENTARIO", "📝 ADMIN", "📊 REPORTES"]) if st.session_state.rol_usuario == "Administrador" else st.tabs(["📦 PEDIDOS WEB", "🛒 PUNTO DE VENTA", "📱 CONSULTAR"])
    
    t_ped, t_pos, t_inv = tabs[0], tabs[1], tabs[2]
    t_adm = tabs[3] if len(tabs) > 3 else None
    t_rep = tabs[4] if len(tabs) > 3 else None

    # 1. PEDIDOS WEB
    with t_ped:
        p_list = df_ped[df_ped['Estado']=='Pendiente']
        if p_list.empty: 
            st.success("✅ Bandeja de salida limpia.")
        else:
            for i, r in p_list.iterrows():
                with st.container():
                    c1, c2, c3, c4 = st.columns([0.5, 3, 2, 1.5])
                    icon = "🟡" if r['Plataforma']=="Mercado Libre" else "🟠"
                    c1.markdown(f"## {icon}")
                    c2.markdown(f"**{r['Modelo']}**")
                    c2.caption(f"SKU: {r['SKU']} | Cant: **x{r['Cantidad']}**")
                    c3.write(f"ID: {r['ID_Pedido']}")
                    if c4.button("Enviado", key=r['ID_Pedido']):
                        df_ped.loc[df_ped['ID_Pedido']==r['ID_Pedido'], 'Estado']='Enviado'
                        guardar_df(df_ped, ARCHIVO_PEDIDOS)
                        st.toast("Pedido actualizado")
                        time.sleep(0.5)
                        st.rerun()
                    st.divider()

    # 2. PUNTO DE VENTA (MEJORA 7 - ORDENADO)
    with t_pos:
        c_izq, c_der = st.columns([2, 1])
        with c_izq:
            st.markdown("#### 🛍️ Nueva Venta")
            # Input grande y limpio
            scan = st.text_input("Buscar producto:", placeholder="Escanear código o escribir nombre...", label_visibility="collapsed")
            sel = None
            
            if scan:
                scan_clean = sanitizar_texto(scan) 
                f = df_inv[df_inv['SKU'].astype(str) == scan_clean]
                if not f.empty:
                    sel = f.iloc[0]
                    st.success(f"Producto: {sel['Modelo']}")
                else: 
                    # Búsqueda parcial por nombre si falla SKU
                    f_name = df_inv[df_inv['Modelo'].str.contains(scan, case=False)]
                    if not f_name.empty:
                        sel = f_name.iloc[0]
            
            if sel is None and not df_inv.empty:
                op = df_inv[df_inv['Cantidad'] > 0].apply(lambda x: f"{x['Modelo']} | {x['SKU']}", axis=1)
                s = st.selectbox("Selección manual:", op, label_visibility="collapsed")
                if s: sel = df_inv[df_inv['SKU'] == s.split(" | ")[1]].iloc[0]
            
            if sel is not None:
                st.markdown("---")
                idx = df_inv[df_inv['SKU'] == sel['SKU']].index[0]
                item = df_inv.iloc[idx]
                stock_real = int(item['Cantidad'])
                
                c_det, c_act = st.columns([2, 1])
                with c_det:
                    st.markdown(f"### {item['Modelo']}")
                    st.caption(f"SKU: {item['SKU']} | Stock Disponible: {stock_real}")
                
                with c_act:
                    q = st.number_input("Cantidad", 1, max(1, stock_real), 1)
                    tot = item['Precio_Venta'] * q
                    st.markdown(f"<h2 style='text-align:right; color:#D4AF37'>${tot:,.2f}</h2>", unsafe_allow_html=True)
                
                if st.button("COBRAR AHORA", type="primary", use_container_width=True):
                    if q > stock_real:
                        st.error("⛔ Stock insuficiente.")
                    else:
                        df_inv.at[idx, 'Cantidad'] -= q
                        guardar_df(df_inv, ARCHIVO_INVENTARIO)
                        registrar_historial("VENTA", item['SKU'], item['Modelo'], q, item['Precio_Venta'], item['Costo_Unitario'], "Mostrador")
                        st.session_state.ultimo_ticket = generar_ticket(item['SKU'], item['Modelo'], q, tot, st.session_state.nombre_usuario)
                        st.success("Venta Exitosa")
                        time.sleep(0.5)
                        st.rerun()
        
        with c_der:
            # Ticket visualmente separado (Mejora 7)
            st.info("🧾 Último Recibo")
            if st.session_state.ultimo_ticket:
                st.code(st.session_state.ultimo_ticket, language="text")
                st.download_button("Descargar .txt", st.session_state.ultimo_ticket, "ticket.txt")

    # 3. INVENTARIO (MEJORA 3 - TABLA VIVA)
    with t_inv:
        st.markdown("#### 📦 Inventario Global")
        cols = ['SKU', 'Modelo', 'Cantidad', 'Stock_Minimo', 'Link_AliExpress', 'Precio_ML', 'Precio_Amazon']
        
        st.dataframe(
            df_inv[cols], 
            use_container_width=True, 
            column_config={
                "Link_AliExpress": st.column_config.LinkColumn("Proveedor", display_text="Ver en AliExpress"),
                "Cantidad": st.column_config.ProgressColumn(
                    "Stock Real", 
                    format="%d", 
                    min_value=0, 
                    max_value=int(df_inv['Cantidad'].max()),
                ),
                "Precio_ML": st.column_config.NumberColumn("Precio ML", format="$%.2f"),
                "Precio_Amazon": st.column_config.NumberColumn("Precio Amz", format="$%.2f"),
            }
        )

    # 4. ADMIN RESTAURADO CON ESTILO NUEVO
    if t_adm:
        with t_adm:
            st.markdown("#### 🛠️ Gestión de Catálogo")
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
                
                if st.form_submit_button("Guardar Cambios"):
                    if not f_mod: st.error("Nombre requerido")
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
            st.markdown("#### 📈 Rendimiento Financiero")
            freq = st.radio("Agrupar:", ["Día", "Mes"], horizontal=True)
            if df_full is not None and not df_full.empty:
                df_c = df_full.copy()
                grp = df_c['Fecha_Dt'].dt.date if freq=="Día" else df_c['Fecha_Dt'].dt.strftime('%Y-%m')
                tab = df_c.groupby(grp)[['Monto_Venta', 'Monto_Gasto']].sum()
                tab['Neto'] = tab['Monto_Venta'] - tab['Monto_Gasto']
                st.dataframe(tab.style.format("${:,.2f}"), use_container_width=True)
            else: st.info("Sin datos.")
