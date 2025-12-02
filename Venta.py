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
# 1. CONFIGURACIÓN VISUAL "ELITE RESPONSIVE"
# ==========================================
st.set_page_config(page_title="SalePony Elite", page_icon="🦄", layout="wide")

# CSS INTELIGENTE: Diseño responsivo que respeta tus funciones
st.markdown("""
    <style>
    /* FUENTE GLOBAL */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

    /* TÍTULOS DORADOS */
    h1, h2, h3 {
        background: linear-gradient(to right, #C5A059, #D4AF37, #E6C269);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
    }

    /* TARJETAS DE MÉTRICAS (KPIs) */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-left: 5px solid #C5A059;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricLabel"] { color: var(--text-color) !important; opacity: 0.8; }
    div[data-testid="stMetricValue"] { color: var(--text-color) !important; font-weight: 700; }

    /* INPUTS Y SELECTBOXES (Corrección de colores) */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea {
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.3) !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #C5A059 !important;
        box-shadow: 0 0 0 1px #C5A059 !important;
    }
    div[data-baseweb="select"] span { color: var(--text-color) !important; }

    /* BOTONES ELITE */
    div.stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
        color: #C5A059 !important;
        font-weight: 700;
        border: 1px solid #C5A059;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    @media (prefers-color-scheme: light) {
        div.stButton > button {
            background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
            color: #B8860B !important;
        }
    }
    div.stButton > button:hover {
        background: #C5A059;
        color: #000000 !important;
        border-color: #fff;
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(197, 160, 89, 0.4);
    }

    /* LOGIN CARD */
    .login-card {
        background-color: var(--secondary-background-color);
        padding: 2.5rem;
        border-radius: 20px;
        border: 1px solid rgba(197, 160, 89, 0.3);
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        text-align: center;
    }
    
    /* PESTAÑAS */
    .stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid rgba(128,128,128,0.2); }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: rgba(197, 160, 89, 0.1);
        border-bottom: 3px solid #C5A059;
        color: #C5A059 !important;
        font-weight: 600;
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
# 2. SEGURIDAD Y DATOS
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
            {'Usuario': 'operador', 'Clave': hash_password('op123'), 'Rol': 'Vendedor', 'Nombre': 'Operador'}
        ]
        df = pd.DataFrame(usuarios_defecto)
        df.to_csv(ARCHIVO_USUARIOS, index=False)
        return df
    return pd.read_csv(ARCHIVO_USUARIOS)

def verificar_login(usuario, clave_plana):
    df = cargar_usuarios()
    match = df[df['Usuario'] == usuario]
    if not match.empty and match.iloc[0]['Clave'] == hash_password(clave_plana):
        return match.iloc[0]
    return None

if 'sesion_iniciada' not in st.session_state:
    st.session_state.sesion_iniciada = False
    st.session_state.rol_usuario = None
    st.session_state.nombre_usuario = None
    st.session_state.usuario_id = None
    st.session_state.ultimo_ticket = ""
    if 'contador_soporte' not in st.session_state: st.session_state.contador_soporte = 0

def enviar_correo_soporte(mensaje):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("alanbdb64@gmail.com", "dxah wqco wygs bjgk".replace(" ", ""))
        msg = MIMEMultipart()
        msg['Subject'] = f"🚨 Reporte SalePony - {datetime.now().strftime('%H:%M')}"
        msg.attach(MIMEText(f"Usuario: {st.session_state.nombre_usuario}\n\n{mensaje}", 'plain'))
        server.sendmail("alanbdb64@gmail.com", "alanbdb64@gmail.com", msg.as_string())
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
            if col not in df.columns: df[col] = 0.0 if "Precio" in col or "Costo" in col or "Cantidad" in col or "Minimo" in col else ""
        return df
    except: return pd.DataFrame(columns=columnas)

def cargar_inventario():
    cols = ['SKU', 'Categoria', 'Modelo', 'Tipo', 'Cantidad', 'Stock_Minimo', 'Costo_Unitario', 'Precio_Venta', 'Link_AliExpress', 'Precio_ML', 'Precio_Amazon']
    df = cargar_csv(ARCHIVO_INVENTARIO, cols)
    if df.empty:
        datos = [{'SKU': 'IP15-CLR', 'Categoria': 'Fundas', 'Modelo': 'Funda iPhone 15 Transparente', 'Tipo': 'Imp', 'Cantidad': 20, 'Stock_Minimo': 5, 'Costo_Unitario': 30.0, 'Precio_Venta': 199.0, 'Link_AliExpress': '', 'Precio_ML': 249.0, 'Precio_Amazon': 229.0}]
        df = pd.DataFrame(datos)
        df.to_csv(ARCHIVO_INVENTARIO, index=False)
    return df

def guardar_df(df, archivo):
    try:
        if not os.path.exists("respaldos"): os.makedirs("respaldos")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if os.path.exists(archivo):
            try: pd.read_csv(archivo).to_csv(f"respaldos/{os.path.basename(archivo).split('.')[0]}_{ts}.csv", index=False)
            except: pass
        df.to_csv(archivo, index=False)
        st.cache_data.clear()
    except: pass

def registrar_historial(accion, sku, modelo, cant, precio=0, costo=0, notas=""):
    nuevo = {
        'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Usuario': st.session_state.nombre_usuario,
        'Accion': accion, 'SKU': sku, 'Modelo': modelo, 'Cantidad': cant,
        'Monto_Venta': float(precio)*int(cant) if "VENTA" in accion else 0,
        'Costo_Venta': float(costo)*int(cant) if "VENTA" in accion else 0,
        'Monto_Gasto': float(costo)*int(cant) if "ALTA" in accion or "ENTRADA" in accion else 0,
        'Notas': notas
    }
    df_h = pd.DataFrame([nuevo])
    try: df_h.to_csv(ARCHIVO_HISTORIAL, mode='a', header=not os.path.exists(ARCHIVO_HISTORIAL), index=False); st.cache_data.clear()
    except: pass

def generar_ticket(sku, modelo, cant, total, user):
    return f"""
    SALE PONY STORE
    --------------------------------
    Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}
    Atendió: {user}
    --------------------------------
    ITEM: {modelo[:20]}
    CANT: x{cant}
    SKU:  {sku}
    --------------------------------
    TOTAL: ${total:,.2f}
    --------------------------------
    ¡Gracias por su compra!
    """

def sincronizar(df_inv):
    nuevos = []
    time.sleep(1)
    if not df_inv.empty and random.random() > 0.6:
        stock = df_inv[df_inv['Cantidad'] > 0]
        if not stock.empty:
            p = stock.sample(1).iloc[0]
            if p['Cantidad'] > 0:
                nuevos.append({'Plataforma': 'Mercado Libre', 'SKU': p['SKU'], 'Modelo': p['Modelo'], 'Cantidad': 1})
    return nuevos

def calc_stats():
    if not os.path.exists(ARCHIVO_HISTORIAL): return None, None, pd.DataFrame()
    try: df = pd.read_csv(ARCHIVO_HISTORIAL); df['Fecha_Dt'] = pd.to_datetime(df['Fecha'])
    except: return None, None, pd.DataFrame()
    if 'Monto_Gasto' not in df.columns: df['Monto_Gasto'] = 0.0
    return df, None, df

# ==========================================
# 4. INTERFAZ
# ==========================================

if not st.session_state.sesion_iniciada:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div class="login-card">
                <h1 style='text-align: center; margin-bottom: 0; font-size: 2.5rem;'>🦄 SalePony <span style='color:#D4AF37'>Elite</span></h1>
                <p style='text-align: center; opacity: 0.8; letter-spacing: 2px; font-weight: 600; color: #C5A059;'>ACCESO SEGURO</p>
                <hr style='border-color: rgba(197, 160, 89, 0.3);'>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.form("login"):
            u = st.text_input("Usuario", placeholder="Ej: admin")
            p = st.text_input("Contraseña", type="password", placeholder="••••••••")
            if st.form_submit_button("ACCEDER AL SISTEMA"):
                val = verificar_login(u, p)
                if val is not None:
                    st.session_state.sesion_iniciada = True
                    st.session_state.rol_usuario = val['Rol']
                    st.session_state.nombre_usuario = val['Nombre']
                    st.session_state.usuario_id = val['Usuario']
                    st.rerun()
                else: st.error("Datos incorrectos")
        st.caption("Admin: admin/admin123 | Op: operador/op123")

else:
    df_inv = cargar_inventario()
    df_ped = cargar_csv(ARCHIVO_PEDIDOS, ['ID_Pedido','Fecha','SKU','Modelo','Cantidad','Plataforma','Estado'])
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state.nombre_usuario}")
        st.caption(f"Rol: {st.session_state.rol_usuario}")
        
        if st.button("🔄 Actualizar Datos", help="Forzar recarga"):
            st.cache_data.clear()
            st.rerun()
            
        st.divider()
        
        with st.expander("🇨🇳 Importación"):
            c = st.number_input("Costo China", 0.0, step=10.0)
            e = st.number_input("Envío", 0.0, step=10.0)
            v = st.number_input("Venta", 0.0, step=10.0)
            if st.button("Calc. Margen"):
                gan = v - (c + e) - (v * 0.15)
                if gan > 0: st.success(f"Ganas: ${gan:,.2f}")
                else: st.error(f"Pierdes: ${gan:,.2f}")

        with st.expander("💵 Arqueo de Caja"):
            raw, _, df_full = calc_stats()
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
            with st.spinner("Buscando..."):
                news, logs = sincronizar(df_inv)
                if news:
                    for n in news:
                        idx = df_inv[df_inv['SKU']==n['SKU']].index[0]
                        df_inv.at[idx, 'Cantidad'] -= n['Cantidad']
                        reg = {'ID_Pedido':f"ORD-{int(time.time())}", 'Fecha':datetime.now().strftime("%Y-%m-%d"), 'SKU':n['SKU'], 'Modelo':n['Modelo'], 'Cantidad':n['Cantidad'], 'Plataforma':'ML', 'Estado':'Pendiente'}
                        df_ped = pd.concat([df_ped, pd.DataFrame([reg])], ignore_index=True)
                        registrar_historial("VENTA_AUTO", n['SKU'], n['Modelo'], n['Cantidad'], 0, 0, "Venta Web")
                    guardar_df(df_inv, ARCHIVO_INVENTARIO)
                    guardar_df(df_ped, ARCHIVO_PEDIDOS)
                    st.success(f"{len(news)} Pedidos!")
                    time.sleep(1)
                    st.rerun()
                else: st.info("Todo al día")

        with st.expander("📧 Soporte", expanded=False):
            key_din = f"txt_soporte_{st.session_state.contador_soporte}"
            msg_err = st.text_area("Mensaje:", key=key_din)
            if st.button("Enviar"):
                if msg_err and enviar_correo_soporte(msg_err):
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
                    if os.path.exists(ARCHIVO_PEDIDOS): os.remove(ARCHIVO_PEDIDOS)
                    st.cache_data.clear()
                    st.rerun()

    # --- DASHBOARD ---
    st.title("🦄 SalePony Dashboard")
    
    # KPIs
    pend = df_ped[df_ped['Estado']=='Pendiente'].shape[0]
    low = df_inv[df_inv['Cantidad'] <= df_inv['Stock_Minimo']].shape[0]
    raw, _, df_full = calc_stats()
    vhoy = 0
    if df_full is not None and not df_full.empty:
        vhoy = df_full[(df_full['Fecha_Dt'].dt.date == datetime.now().date()) & (df_full['Accion'].str.contains('VENTA'))]['Monto_Venta'].sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ventas Hoy", f"${vhoy:,.2f}")
    k2.metric("Envíos Pendientes", pend, delta_color="inverse" if pend>0 else "normal")
    k3.metric("Stock Bajo", low, delta_color="inverse")
    k4.metric("Sistema", "Online 🟢")

    st.divider()

    # TABS
    tabs = st.tabs(["📦 PEDIDOS WEB", "🛒 PUNTO DE VENTA", "📱 INVENTARIO", "📝 ADMIN", "📊 REPORTES"]) if st.session_state.rol_usuario == "Administrador" else st.tabs(["📦 PEDIDOS WEB", "🛒 PUNTO DE VENTA", "📱 CONSULTAR"])
    t_ped, t_pos, t_inv = tabs[0], tabs[1], tabs[2]
    t_adm = tabs[3] if len(tabs) > 3 else None
    t_rep = tabs[4] if len(tabs) > 3 else None

    # 1. PEDIDOS
    with t_ped:
        p = df_ped[df_ped['Estado']=='Pendiente']
        if p.empty: st.success("✅ Todo limpio.")
        else:
            for i, r in p.iterrows():
                with st.container():
                    c1, c2, c3, c4 = st.columns([0.5, 3, 2, 1.5])
                    c1.write("📦")
                    c2.markdown(f"**{r['Modelo']}**")
                    c2.caption(f"SKU: {r['SKU']}")
                    c3.write(f"x{r['Cantidad']}")
                    if c4.button("Enviar", key=r['ID_Pedido']):
                        df_ped.loc[df_ped['ID_Pedido']==r['ID_Pedido'], 'Estado']='Enviado'
                        guardar_df(df_ped, ARCHIVO_PEDIDOS)
                        st.rerun()
                    st.divider()

    # 2. POS (STOCK FIXED)
    with t_pos:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### 🛍️ Caja")
            scan = st.text_input("🔍 Buscar:", placeholder="Escanear código...", label_visibility="collapsed")
            sel = None
            if scan:
                scan = sanitizar_texto(scan)
                f = df_inv[df_inv['SKU'].astype(str) == scan]
                if not f.empty: sel = f.iloc[0]
                else: 
                    fn = df_inv[df_inv['Modelo'].str.contains(scan, case=False)]
                    if not fn.empty: sel = fn.iloc[0]
            
            if sel is None and not df_inv.empty:
                op = df_inv[df_inv['Cantidad']>0].apply(lambda x: f"{x['Modelo']} | {x['SKU']}", axis=1)
                s = st.selectbox("Manual:", op, label_visibility="collapsed")
                if s: sel = df_inv[df_inv['SKU'] == s.split(" | ")[1]].iloc[0]
            
            if sel is not None:
                idx = df_inv[df_inv['SKU']==sel['SKU']].index[0]
                stock = int(df_inv.at[idx, 'Cantidad'])
                st.info(f"**{sel['Modelo']}** | Stock: {stock}")
                
                # LOGICA STOCK FIX
                if stock > 0:
                    cq, cp = st.columns(2)
                    q = cq.number_input("Cant.", 1, stock, 1)
                    tot = sel['Precio_Venta'] * q
                    cp.metric("Total", f"${tot:,.2f}")
                    
                    if st.button("COBRAR", type="primary", use_container_width=True):
                        if q > stock:
                            st.error("⛔ Error: Stock insuficiente.")
                        else:
                            df_inv.at[idx, 'Cantidad'] -= q
                            guardar_df(df_inv, ARCHIVO_INVENTARIO)
                            registrar_historial("VENTA", sel['SKU'], sel['Modelo'], q, sel['Precio_Venta'], sel['Costo_Unitario'], "Mostrador")
                            st.session_state.ultimo_ticket = generar_ticket(sel['SKU'], sel['Modelo'], q, tot, st.session_state.nombre_usuario)
                            st.success("Venta OK")
                            time.sleep(0.5)
                            st.rerun()
                else:
                    st.error("⚠️ PRODUCTO AGOTADO")
                    st.button("COBRAR", disabled=True, key="btn_agotado")

        with c2:
            st.info("🧾 Ticket")
            if st.session_state.ultimo_ticket:
                st.code(st.session_state.ultimo_ticket)

    # 3. INVENTARIO (FILTRO RESTAURADO)
    with t_inv:
        st.markdown("#### 📦 Inventario")
        ver_bajo = st.checkbox("Ver solo stock bajo") # RESTAURADO
        
        df_show = df_inv.copy()
        if ver_bajo:
            df_show = df_show[df_show['Cantidad'] <= df_show['Stock_Minimo']]
            
        st.dataframe(
            df_show[['SKU', 'Modelo', 'Cantidad', 'Stock_Minimo', 'Precio_ML', 'Precio_Amazon']], 
            use_container_width=True,
            column_config={
                "Cantidad": st.column_config.ProgressColumn("Stock Real", format="%d", min_value=0, max_value=int(df_inv['Cantidad'].max()))
            }
        )

    # 4. ADMIN (COMPLETO RESTAURADO)
    if t_adm:
        with t_adm:
            st.markdown("#### 🛠️ Gestión")
            act = st.radio("Acción", ["Nuevo", "Clonar", "Editar Info", "Ajuste Stock"], horizontal=True) # RESTAURADO
            d_sku, d_mod, d_qty, d_min, d_cost, d_pv = "", "", 10, 5, 0.0, 0.0
            d_cat, d_link, d_ml, d_amz = "Fundas", "", 0.0, 0.0 # RESTAURADO
            idx_e = -1
            
            if act != "Nuevo" and not df_inv.empty:
                s_ed = st.selectbox("Seleccionar:", df_inv['Modelo'].unique())
                idx_e = df_inv[df_inv['Modelo']==s_ed].index[0]
                r = df_inv.iloc[idx_e]
                d_sku = "" if act=="Clonar" else r['SKU']
                d_mod = r['Modelo'] + (" (Copia)" if act=="Clonar" else "")
                d_cat, d_qty = r['Categoria'], int(r['Cantidad'])
                d_min = int(r['Stock_Minimo'])
                d_cost = float(r['Costo_Unitario'])
                d_pv = float(r['Precio_Venta'])
                d_link, d_ml, d_amz = r['Link_AliExpress'], float(r['Precio_ML']), float(r['Precio_Amazon'])

            with st.form("adm"):
                c1, c2 = st.columns(2)
                f_sku = c1.text_input("SKU", d_sku, disabled=(act in ["Editar Info", "Ajuste Stock"]))
                f_mod = c2.text_input("Modelo", d_mod, disabled=(act=="Ajuste Stock"))
                
                c3, c4, c5 = st.columns(3)
                f_cat = c3.selectbox("Cat.", ["Fundas", "Micas", "Cargadores", "Cables", "Otro"], index=0) # RESTAURADO
                f_qty = c4.number_input("Stock", value=d_qty)
                f_min = c5.number_input("Mínimo", value=d_min) 
                
                c6, c7, c8 = st.columns(3)
                f_cos = c6.number_input("Costo", value=d_cost)
                f_pv = c7.number_input("P. Venta", value=d_pv)
                f_lnk = c8.text_input("Link Ali", d_link) # RESTAURADO
                
                c9, c10 = st.columns(2)
                f_ml = c9.number_input("Precio ML", value=d_ml) # RESTAURADO
                f_amz = c10.number_input("Precio Amz", value=d_amz) # RESTAURADO
                
                if st.form_submit_button("Guardar"):
                    if not f_mod: st.error("Falta nombre")
                    else:
                        f_mod = sanitizar_texto(f_mod)
                        f_sku = sanitizar_texto(f_sku)
                        if not f_sku: f_sku = f"ACC-{str(uuid.uuid4())[:6].upper()}"
                        new_d = {'SKU': f_sku, 'Categoria': f_cat, 'Modelo': f_mod, 'Tipo': 'Imp', 'Cantidad': f_qty, 'Stock_Minimo': f_min, 'Costo_Unitario': f_cos, 'Precio_Venta': f_pv, 'Link_AliExpress': f_lnk, 'Precio_ML': f_ml, 'Precio_Amazon': f_amz}
                        
                        if act in ["Editar Info", "Ajuste Stock"] and idx_e != -1:
                            diff = f_qty - df_inv.at[idx_e, 'Cantidad']
                            for k,v in new_d.items(): df_inv.at[idx_e, k] = v
                            guardar_df(df_inv, ARCHIVO_INVENTARIO)
                            registrar_historial("EDICION", f_sku, f_mod, abs(diff), 0, 0, "Ajuste Admin")
                            st.success("Actualizado")
                        else:
                            df_inv = pd.concat([df_inv, pd.DataFrame([new_d])], ignore_index=True)
                            guardar_df(df_inv, ARCHIVO_INVENTARIO)
                            registrar_historial("ALTA", f_sku, f_mod, f_qty, 0, f_cos, "Alta")
                            st.success("Creado")
                        time.sleep(1)
                        st.rerun()

    # 5. REPORTES (CON DESCARGA RESTAURADA)
    if t_rep:
        with t_rep:
            st.markdown("#### 📈 Finanzas")
            freq = st.radio("Ver por:", ["Día", "Mes"], horizontal=True)
            if df_full is not None and not df_full.empty:
                df_c = df_full.copy()
                grp = df_c['Fecha_Dt'].dt.date if freq=="Día" else df_c['Fecha_Dt'].dt.strftime('%Y-%m')
                
                # TABLA FLUJO
                st.markdown("### 1. Flujo de Caja")
                tab = df_c.groupby(grp)[['Monto_Venta', 'Monto_Gasto']].sum()
                tab.columns = ['Ventas', 'Compras']
                tab['Neto'] = tab['Ventas'] - tab['Compras']
                st.dataframe(tab.style.format("${:,.2f}"), use_container_width=True)
                
                # BOTÓN DESCARGA RESTAURADO
                csv = tab.to_csv().encode('utf-8')
                st.download_button(
                    label="📥 Descargar Reporte en Excel",
                    data=csv,
                    file_name='reporte_financiero.csv',
                    mime='text/csv',
                )

                st.divider()
                
                # SECCION RENTABILIDAD
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

                # COMISIONES
                st.divider()
                st.markdown("##### Comisiones Empleados")
                if not vs.empty:
                    com = vs.groupby('Usuario')['Monto_Venta'].sum().reset_index()
                    com['Pago (3%)'] = com['Monto_Venta'] * 0.03
                    st.dataframe(com.style.format({'Monto_Venta': '${:,.2f}', 'Pago (3%)': '${:,.2f}'}), use_container_width=True)

            else: st.info("Sin datos")
