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
# 1. CONFIGURACIÓN VISUAL (CORREGIDA)
# ==========================================
st.set_page_config(page_title="SalePony Elite", page_icon="🦄", layout="wide")

# CSS PRO: Elimina espacios blancos y armoniza inputs
st.markdown("""
    <style>
    /* FUENTE */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

    /* FONDO OSCURO UNIFORME */
    .stApp { background-color: #0E1117; }

    /* TÍTULOS DORADOS */
    h1, h2, h3 {
        background: linear-gradient(to right, #bf953f, #fcf6ba, #b38728, #fbf5b7, #aa771c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
    }

    /* TARJETAS KPI (Métricas) */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-left: 4px solid #D4AF37;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricLabel"] { color: #888 !important; }
    div[data-testid="stMetricValue"] { color: #fff !important; }

    /* INPUTS OSCUROS (SOLUCIÓN A ESPACIOS BLANCOS) */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #262730 !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #D4AF37 !important;
        box-shadow: 0 0 0 1px #D4AF37 !important;
    }
    /* Arreglo para el texto dentro de selectbox */
    div[data-baseweb="select"] span { color: #ffffff !important; }

    /* BOTONES ELITE */
    div.stButton > button {
        background: linear-gradient(145deg, #D4AF37, #C5A059);
        color: #000 !important;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        transition: transform 0.2s;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.4);
    }

    /* PESTAÑAS */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: rgba(212, 175, 55, 0.1);
        border-bottom: 2px solid #D4AF37;
        color: #D4AF37 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Archivos
ARCHIVO_INVENTARIO = 'mi_inventario.csv'
ARCHIVO_HISTORIAL = 'historial_movimientos.csv'
ARCHIVO_PEDIDOS = 'pedidos_pendientes.csv'
ARCHIVO_USUARIOS = 'usuarios_seguridad_v3.csv' 

# ==========================================
# 2. SEGURIDAD Y DATOS
# ==========================================

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def sanitizar_texto(texto):
    if isinstance(texto, str): return re.sub(r'[;,\n\r]', ' ', texto).strip()
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
    # Inicializar si vacío
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
    time.sleep(1) # Simulación
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
        st.markdown("<br><br><h1 style='text-align: center;'>🦄 SalePony <span style='color:#fff'>Elite</span></h1>", unsafe_allow_html=True)
        with st.container():
            st.markdown("---")
            with st.form("login"):
                u = st.text_input("Usuario")
                p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("ACCEDER"):
                    val = verificar_login(u, p)
                    if val is not None:
                        st.session_state.sesion_iniciada = True
                        st.session_state.rol_usuario = val['Rol']
                        st.session_state.nombre_usuario = val['Nombre']
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
        st.divider()
        
        with st.expander("🇨🇳 Importación"):
            c = st.number_input("Costo China", 0.0, step=10.0)
            e = st.number_input("Envío", 0.0, step=10.0)
            v = st.number_input("Venta", 0.0, step=10.0)
            if st.button("Calc. Margen"):
                gan = v - (c + e) - (v * 0.15)
                if gan > 0: st.success(f"Ganas: ${gan:,.2f}")
                else: st.error(f"Pierdes: ${gan:,.2f}")

        if st.button("🔄 Sincronizar Nube"):
            with st.spinner("Buscando..."):
                news = sincronizar(df_inv)
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

        # SOPORTE TÉCNICO (Botón + Input Limpio)
        with st.expander("📧 Soporte", expanded=False):
            key_din = f"txt_soporte_{st.session_state.contador_soporte}"
            msg_err = st.text_area("Mensaje:", key=key_din)
            if st.button("Enviar"):
                if msg_err and enviar_correo_soporte(msg_err):
                    st.success("Enviado")
                    st.session_state.contador_soporte += 1
                    time.sleep(1)
                    st.rerun()

        if st.button("Salir"):
            st.session_state.sesion_iniciada = False
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

    # 2. POS (Corregido Stock)
    with t_pos:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### 🛍️ Caja")
            scan = st.text_input("🔍 Buscar:", placeholder="Escanear...")
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
                
                cq, cp = st.columns(2)
                # Candado visual: Max value es el stock real
                q = cq.number_input("Cant.", 1, max(1, stock), 1)
                tot = sel['Precio_Venta'] * q
                cp.metric("Total", f"${tot:,.2f}")
                
                if st.button("COBRAR", type="primary", use_container_width=True):
                    # Candado lógico final
                    if q > stock:
                        st.error(f"⛔ Error: Solo hay {stock} piezas.")
                    else:
                        df_inv.at[idx, 'Cantidad'] -= q
                        guardar_df(df_inv, ARCHIVO_INVENTARIO)
                        registrar_historial("VENTA", sel['SKU'], sel['Modelo'], q, sel['Precio_Venta'], sel['Costo_Unitario'], "Mostrador")
                        st.session_state.ultimo_ticket = generar_ticket(sel['SKU'], sel['Modelo'], q, tot, st.session_state.nombre_usuario)
                        st.success("Venta OK")
                        time.sleep(0.5)
                        st.rerun()
        with c2:
            st.info("🧾 Ticket")
            if st.session_state.ultimo_ticket:
                st.code(st.session_state.ultimo_ticket)

    # 3. INVENTARIO
    with t_inv:
        st.markdown("#### 📦 Inventario")
        # Mostrar columnas críticas
        st.dataframe(
            df_inv[['SKU', 'Modelo', 'Cantidad', 'Stock_Minimo', 'Precio_ML', 'Precio_Amazon']], 
            use_container_width=True,
            column_config={
                "Cantidad": st.column_config.ProgressColumn("Stock Real", format="%d", min_value=0, max_value=int(df_inv['Cantidad'].max()))
            }
        )

    # 4. ADMIN (CORREGIDO LECTURA DE MINIMO)
    if t_adm:
        with t_adm:
            st.markdown("#### 🛠️ Gestión")
            act = st.radio("Acción", ["Nuevo", "Editar Stock"], horizontal=True)
            d_sku, d_mod, d_qty, d_min, d_cost, d_pv = "", "", 10, 5, 0.0, 0.0
            idx_e = -1
            
            if act == "Editar Stock" and not df_inv.empty:
                s = st.selectbox("Editar:", df_inv['Modelo'].unique())
                idx_e = df_inv[df_inv['Modelo']==s].index[0]
                r = df_inv.iloc[idx_e]
                d_sku, d_mod = r['SKU'], r['Modelo']
                # CORRECCIÓN: Ahora leemos el Stock Mínimo para que no se resetee
                d_qty = int(r['Cantidad'])
                d_min = int(r['Stock_Minimo']) # <-- ESTO FALTABA
                d_cost = float(r['Costo_Unitario'])
                d_pv = float(r['Precio_Venta'])

            with st.form("adm"):
                c1, c2 = st.columns(2)
                f_sku = c1.text_input("SKU", d_sku, disabled=(act=="Editar Stock"))
                f_mod = c2.text_input("Modelo", d_mod, disabled=(act=="Editar Stock"))
                c3, c4 = st.columns(2)
                f_qty = c3.number_input("Stock Físico", value=d_qty)
                f_min = c4.number_input("Stock Mínimo", value=d_min) # Ahora carga el valor real
                c5, c6 = st.columns(2)
                f_cos = c5.number_input("Costo", value=d_cost)
                f_pv = c6.number_input("Precio Venta", value=d_pv)
                
                if st.form_submit_button("Guardar"):
                    if act == "Editar Stock" and idx_e != -1:
                        df_inv.at[idx_e, 'Cantidad'] = f_qty
                        df_inv.at[idx_e, 'Stock_Minimo'] = f_min
                        df_inv.at[idx_e, 'Costo_Unitario'] = f_cos
                        df_inv.at[idx_e, 'Precio_Venta'] = f_pv
                        guardar_df(df_inv, ARCHIVO_INVENTARIO)
                        registrar_historial("EDICION", d_sku, d_mod, abs(f_qty-d_qty), 0, 0, "Ajuste Admin")
                        st.success("Actualizado")
                        time.sleep(1)
                        st.rerun()
                    else:
                        # Lógica de nuevo (simplificada)
                        if not f_sku: f_sku = f"GEN-{str(uuid.uuid4())[:4]}"
                        new = {'SKU':f_sku, 'Modelo':f_mod, 'Cantidad':f_qty, 'Stock_Minimo':f_min, 'Costo_Unitario':f_cos, 'Precio_Venta':f_pv, 'Categoria':'Gral', 'Tipo':'Imp', 'Link_AliExpress':'', 'Precio_ML':0, 'Precio_Amazon':0}
                        df_inv = pd.concat([df_inv, pd.DataFrame([new])], ignore_index=True)
                        guardar_df(df_inv, ARCHIVO_INVENTARIO)
                        st.success("Creado")
                        st.rerun()

    # 5. REPORTES
    if t_rep:
        with t_rep:
            st.markdown("#### 📈 Finanzas")
            if df_full is not None and not df_full.empty:
                grp = df_full.groupby(df_full['Fecha_Dt'].dt.date)[['Monto_Venta', 'Monto_Gasto']].sum()
                st.line_chart(grp)
            else: st.info("Sin datos")
