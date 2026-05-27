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
# 1. CONFIGURACIÓN VISUAL "ELITE" (RESPONSIVA)
# ==========================================
st.set_page_config(page_title="Tenis Rey | Sport", page_icon="👑", layout="wide")

# CSS: Diseño adaptable (Modo Claro/Oscuro), colores Negro, Blanco y Dorado
st.markdown("""
    <style>
    /* FUENTE ELEGANTE Y MODERNA */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

    /* TÍTULOS CON DEGRADADO DORADO */
    h1, h2, h3 {
        background: linear-gradient(to right, #bf953f, #fcf6ba, #b38728, #fbf5b7, #aa771c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
    }

    /* TARJETAS DE MÉTRICAS (Glassmorphism sutil adaptable) */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.15);
        border-left: 4px solid #C5A059;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(197, 160, 89, 0.2);
        border-left: 4px solid #D4AF37;
    }
    div[data-testid="stMetricLabel"] { color: var(--text-color) !important; opacity: 0.7; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;}
    div[data-testid="stMetricValue"] { color: var(--text-color) !important; font-weight: 700; }

    /* INPUTS Y SELECTBOXES (Adaptables a Dark/Light Mode) */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea {
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #C5A059 !important;
        box-shadow: 0 0 0 2px rgba(197, 160, 89, 0.3) !important;
    }
    div[data-baseweb="select"] span { color: var(--text-color) !important; }

    /* BOTONES PRIMARIOS (Negro mate y Dorado) */
    div.stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #111111 0%, #222222 100%);
        color: #D4AF37 !important;
        font-weight: 600;
        border: 1px solid #C5A059;
        border-radius: 8px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    /* Inversión en modo claro para que los botones destaquen */
    @media (prefers-color-scheme: light) {
        div.stButton > button {
            background: linear-gradient(135deg, #ffffff 0%, #f9f9f9 100%);
            color: #b38728 !important;
        }
    }
    div.stButton > button:hover {
        background: #C5A059;
        border-color: #C5A059;
        color: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(197, 160, 89, 0.4);
    }
    div.stButton > button:active {
        transform: translateY(1px);
    }

    /* LOGIN CARD */
    .login-card {
        background-color: var(--secondary-background-color);
        padding: 3rem;
        border-radius: 16px;
        border: 1px solid rgba(197, 160, 89, 0.3);
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        text-align: center;
        transition: all 0.3s ease;
    }
    .login-card:hover {
        box-shadow: 0 15px 40px rgba(197, 160, 89, 0.15);
    }
    
    /* PESTAÑAS (TABS) */
    .stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid rgba(128,128,128,0.1); gap: 10px;}
    .stTabs [data-baseweb="tab-list"] button { transition: all 0.3s ease; }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: rgba(197, 160, 89, 0.1);
        border-bottom: 3px solid #C5A059;
        color: #C5A059 !important;
        font-weight: 700;
        border-radius: 4px 4px 0 0;
    }
    </style>
""", unsafe_allow_html=True)

# Nombres de archivos
ARCHIVO_INVENTARIO = 'tr_inventario.csv'
ARCHIVO_HISTORIAL = 'tr_historial.csv'
ARCHIVO_PEDIDOS = 'tr_pedidos.csv'
ARCHIVO_USUARIOS = 'tr_usuarios.csv' 
ARCHIVO_CONFIG_API = 'tr_config_apis.csv'

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
            {'Usuario': 'admin', 'Clave': hash_password('admin123'), 'Rol': 'Administrador', 'Nombre': 'Gerencia Tenis Rey'},
            {'Usuario': 'vendedor', 'Clave': hash_password('ven123'), 'Rol': 'Vendedor', 'Nombre': 'Asesor Comercial'}
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
        msg['Subject'] = f"🚨 Alerta de Sistema (Tenis Rey) - {datetime.now().strftime('%H:%M')}"
        msg.attach(MIMEText(f"Usuario reporta: {st.session_state.nombre_usuario}\n\nDetalle de la incidencia:\n{mensaje}", 'plain'))
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
    cols = ['SKU', 'Categoria', 'Modelo', 'Tipo', 'Cantidad', 'Stock_Minimo', 'Costo_Unitario', 'Precio_Venta', 'Proveedor', 'Precio_ML', 'Precio_Amazon']
    df = cargar_csv(ARCHIVO_INVENTARIO, cols)
    if df.empty:
        # Catálogo por defecto
        datos = [
            {'SKU': 'NK-AJ1-RED-27', 'Categoria': 'Calzado', 'Modelo': 'Nike Air Jordan 1 Rojo 27cm', 'Tipo': 'Mayorista', 'Cantidad': 12, 'Stock_Minimo': 3, 'Costo_Unitario': 1200.0, 'Precio_Venta': 2500.0, 'Proveedor': 'Distribuidor Nacional', 'Precio_ML': 2800.0, 'Precio_Amazon': 2750.0},
            {'SKU': 'AD-ULB-BLK-26', 'Categoria': 'Calzado', 'Modelo': 'Adidas Ultraboost Negro 26cm', 'Tipo': 'Mayorista', 'Cantidad': 8, 'Stock_Minimo': 2, 'Costo_Unitario': 1500.0, 'Precio_Venta': 3200.0, 'Proveedor': 'Importación Directa', 'Precio_ML': 3500.0, 'Precio_Amazon': 3400.0},
            {'SKU': 'PM-TSH-WHT-M', 'Categoria': 'Ropa', 'Modelo': 'Playera Deportiva Puma Blanca Talla M', 'Tipo': 'Nacional', 'Cantidad': 25, 'Stock_Minimo': 5, 'Costo_Unitario': 250.0, 'Precio_Venta': 500.0, 'Proveedor': 'Textiles MX', 'Precio_ML': 600.0, 'Precio_Amazon': 550.0},
            {'SKU': 'NK-SOX-3PK', 'Categoria': 'Accesorios', 'Modelo': 'Calcetas Nike Dri-FIT (Pack 3)', 'Tipo': 'Nacional', 'Cantidad': 40, 'Stock_Minimo': 10, 'Costo_Unitario': 150.0, 'Precio_Venta': 350.0, 'Proveedor': 'Distribuidor Nacional', 'Precio_ML': 450.0, 'Precio_Amazon': 400.0}
        ]
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
========================================
         TENIS REY - SUCURSAL
========================================
 Fecha:   {datetime.now().strftime("%d/%m/%Y %H:%M")}
 Cajero:  {user}
----------------------------------------
 CANT | DESCRIPCION           | IMPORTE
----------------------------------------
 {str(cant).center(4)} | {modelo[:19]:<19} | ${total:,.2f}
 
 SKU: {sku}
----------------------------------------
           TOTAL A PAGAR: ${total:,.2f}
========================================
        ¡GRACIAS POR SU COMPRA!
      Conserve su ticket para 
       cualquier aclaración.
========================================
    """

def sincronizar(df_inv):
    nuevos = []
    time.sleep(1) # Simulación de conexión API
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
                <h2 style='text-align: center; margin-bottom: 0;'>TENIS REY</h2>
                <p style='text-align: center; opacity: 0.8; font-weight: 600; color: #D4AF37;'>Sport & Punto de Venta</p>
                <hr style='border-color: rgba(197, 160, 89, 0.2);'>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.form("login"):
            u = st.text_input("Identificador de Usuario", placeholder="Ingrese su usuario")
            p = st.text_input("Contraseña", type="password", placeholder="••••••••")
            if st.form_submit_button("INICIAR SESIÓN"):
                val = verificar_login(u, p)
                if val is not None:
                    st.session_state.sesion_iniciada = True
                    st.session_state.rol_usuario = val['Rol']
                    st.session_state.nombre_usuario = val['Nombre']
                    st.session_state.usuario_id = val['Usuario']
                    st.rerun()
                else: st.error("Autenticación fallida. Verifique sus credenciales.")

else:
    df_inv = cargar_inventario()
    df_ped = cargar_csv(ARCHIVO_PEDIDOS, ['ID_Pedido','Fecha','SKU','Modelo','Cantidad','Plataforma','Estado'])
    
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.markdown(f"#### Panel de Usuario")
        st.write(f"👤 **{st.session_state.nombre_usuario}**")
        st.caption(f"Perfil: {st.session_state.rol_usuario}")
        
        if st.button("🔄 Refrescar Sistema", help="Actualiza los datos en pantalla"):
            st.cache_data.clear()
            st.rerun()
            
        st.divider()
        
        with st.expander("📊 Simulador de Rentabilidad"):
            c = st.number_input("Costo Unitario ($)", 0.0, step=10.0)
            e = st.number_input("Gastos Logísticos ($)", 0.0, step=10.0)
            v = st.number_input("Precio de Venta ($)", 0.0, step=10.0)
            if st.button("Calcular Utilidad"):
                gan = v - (c + e) - (v * 0.15) # 15% estimación de comisión
                if gan > 0: st.success(f"Utilidad Proyectada: ${gan:,.2f}")
                else: st.error(f"Pérdida Proyectada: ${gan:,.2f}")

        with st.expander("💵 Arqueo de Caja"):
            raw, _, df_full = calc_stats()
            esperado = 0.0
            if df_full is not None and not df_full.empty:
                hoy = datetime.now().date()
                mask = (df_full['Fecha_Dt'].dt.date == hoy) & (df_full['Accion'].str.contains('VENTA')) & (df_full['Usuario'] == st.session_state.nombre_usuario)
                esperado = df_full[mask]['Monto_Venta'].sum()
            st.markdown(f"**Total Registrado:** ${esperado:,.2f}")
            real = st.number_input("Efectivo Físico en Caja:", 0.0)
            if st.button("Realizar Arqueo"):
                diff = real - esperado
                if diff == 0: st.success("✅ Cuadre de caja correcto.")
                else: st.warning(f"Diferencia detectada: ${diff:,.2f}")

        if st.session_state.rol_usuario == "Administrador":
            with st.expander("🔌 Integración E-commerce"):
                ml_token_env = os.environ.get("ML_TOKEN", "")
                st.text_input("API Key Mercado Libre", value=ml_token_env, type="password")
                st.text_input("API Key Amazon Seller", type="password")

        st.markdown("---")
        if st.button("📥 Sincronizar Órdenes (B2C)"):
            with st.spinner("Conectando con plataformas..."):
                news = sincronizar(df_inv)
                if news:
                    for n in news:
                        idx = df_inv[df_inv['SKU']==n['SKU']].index[0]
                        df_inv.at[idx, 'Cantidad'] -= n['Cantidad']
                        reg = {'ID_Pedido':f"ORD-{int(time.time())}", 'Fecha':datetime.now().strftime("%Y-%m-%d"), 'SKU':n['SKU'], 'Modelo':n['Modelo'], 'Cantidad':n['Cantidad'], 'Plataforma':n['Plataforma'], 'Estado':'Pendiente'}
                        df_ped = pd.concat([df_ped, pd.DataFrame([reg])], ignore_index=True)
                        registrar_historial("VENTA_AUTO", n['SKU'], n['Modelo'], n['Cantidad'], 0, 0, "Orden B2C Generada")
                    guardar_df(df_inv, ARCHIVO_INVENTARIO)
                    guardar_df(df_ped, ARCHIVO_PEDIDOS)
                    st.success(f"Se procesaron {len(news)} órdenes nuevas.")
                    time.sleep(1)
                    st.rerun()
                else: st.info("Inventario y órdenes sincronizadas. Sin novedades.")

        with st.expander("🛠️ Reportar Incidencia", expanded=False):
            key_din = f"txt_soporte_{st.session_state.contador_soporte}"
            msg_err = st.text_area("Describa el error del sistema:", key=key_din)
            if st.button("Enviar Ticket de Soporte"):
                if msg_err and enviar_correo_soporte(msg_err):
                    st.success("Ticket enviado al administrador.")
                    st.session_state.contador_soporte += 1
                    time.sleep(1)
                    st.rerun()

        if st.button("Cerrar Sesión"):
            st.session_state.sesion_iniciada = False
            st.rerun()

        if st.session_state.rol_usuario == "Administrador":
            with st.expander("⚠️ Mantenimiento de Base de Datos", expanded=False):
                if st.button("Purgar Historial de Transacciones"):
                    if os.path.exists(ARCHIVO_HISTORIAL): os.remove(ARCHIVO_HISTORIAL)
                    if os.path.exists(ARCHIVO_PEDIDOS): os.remove(ARCHIVO_PEDIDOS)
                    st.cache_data.clear()
                    st.rerun()

    # --- ÁREA DE TRABAJO PRINCIPAL ---
    st.markdown("<h2 style='margin-bottom: 0;'>Panel de Control - Tenis Rey</h2>", unsafe_allow_html=True)
    
    # CÁLCULO DE KPIs
    pend = df_ped[df_ped['Estado']=='Pendiente'].shape[0]
    low = df_inv[df_inv['Cantidad'] <= df_inv['Stock_Minimo']].shape[0]
    valor_inventario = (df_inv['Cantidad'] * df_inv['Costo_Unitario']).sum() if not df_inv.empty else 0.0
    
    raw, _, df_full = calc_stats()
    vhoy = 0
    if df_full is not None and not df_full.empty:
        vhoy = df_full[(df_full['Fecha_Dt'].dt.date == datetime.now().date()) & (df_full['Accion'].str.contains('VENTA'))]['Monto_Venta'].sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ingresos Diarios", f"${vhoy:,.2f}")
    k2.metric("Órdenes Pendientes", pend, delta_color="inverse" if pend>0 else "normal")
    k3.metric("Alertas de Stock", low, delta_color="inverse")
    k4.metric("Valor del Inventario", f"${valor_inventario:,.2f}")

    st.divider()

    # PESTAÑAS DE NAVEGACIÓN (SE SUMA PESTAÑA PARA VENDEDOR: MIS VENTAS)
    tabs = st.tabs(["📦 ÓRDENES E-COMMERCE", "🛒 TERMINAL PUNTO DE VENTA", "👟 GESTIÓN DE INVENTARIO", "📝 MANTENIMIENTO DE CATÁLOGO", "📊 REPORTES FINANCIEROS"]) if st.session_state.rol_usuario == "Administrador" else st.tabs(["📦 ÓRDENES E-COMMERCE", "🛒 TERMINAL PUNTO DE VENTA", "👟 CONSULTA DE INVENTARIO", "📊 MIS VENTAS"])
    
    t_ped, t_pos, t_inv = tabs[0], tabs[1], tabs[2]
    
    if st.session_state.rol_usuario == "Administrador":
        t_adm, t_rep = tabs[3], tabs[4]
        t_mis_ventas = None
    else:
        t_adm, t_rep = None, None
        t_mis_ventas = tabs[3]

    # 1. ÓRDENES
    with t_ped:
        p = df_ped[df_ped['Estado']=='Pendiente']
        if p.empty: st.success("No hay órdenes pendientes de despacho.")
        else:
            for i, r in p.iterrows():
                with st.container():
                    c1, c2, c3, c4 = st.columns([0.5, 3, 2, 1.5])
                    c1.markdown("<h4>📦</h4>", unsafe_allow_html=True)
                    c2.markdown(f"**{r['Modelo']}**")
                    c2.caption(f"SKU: {r['SKU']} | Unidades: **{r['Cantidad']}**")
                    c3.write(f"Ref. Externa: {r['ID_Pedido']}")
                    if c4.button("Confirmar Despacho", key=r['ID_Pedido']):
                        df_ped.loc[df_ped['ID_Pedido']==r['ID_Pedido'], 'Estado']='Enviado'
                        guardar_df(df_ped, ARCHIVO_PEDIDOS)
                        st.rerun()
                    st.divider()

    # 2. TPV (PUNTO DE VENTA)
    with t_pos:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### Registro de Venta")
            scan = st.text_input("Búsqueda de Artículo:", placeholder="Ingrese SKU o descripción del artículo...", label_visibility="collapsed")
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
                s = st.selectbox("Selección desde Catálogo:", op, label_visibility="collapsed")
                if s: sel = df_inv[df_inv['SKU'] == s.split(" | ")[1]].iloc[0]
            
            if sel is not None:
                idx = df_inv[df_inv['SKU']==sel['SKU']].index[0]
                stock = int(df_inv.at[idx, 'Cantidad'])
                st.info(f"**{sel['Modelo']}** | Inventario Físico: {stock} unidades")
                
                if stock > 0:
                    cq, cp = st.columns(2)
                    q = cq.number_input("Cantidad a vender", 1, stock, 1)
                    tot = sel['Precio_Venta'] * q
                    cp.metric("Importe a Cobrar", f"${tot:,.2f}")
                    
                    if st.button("PROCESAR TRANSACCIÓN", type="primary", use_container_width=True):
                        if q > stock:
                            st.error("Operación denegada: Inventario insuficiente.")
                        else:
                            df_inv.at[idx, 'Cantidad'] -= q
                            guardar_df(df_inv, ARCHIVO_INVENTARIO)
                            registrar_historial("VENTA", sel['SKU'], sel['Modelo'], q, sel['Precio_Venta'], sel['Costo_Unitario'], "Venta Directa TPV")
                            st.session_state.ultimo_ticket = generar_ticket(sel['SKU'], sel['Modelo'], q, tot, st.session_state.nombre_usuario)
                            st.success("Transacción registrada correctamente.")
                            time.sleep(0.5)
                            st.rerun()
                else:
                    st.error("El artículo seleccionado se encuentra agotado.")
                    st.button("PROCESAR TRANSACCIÓN", disabled=True, key="btn_agotado")

        with c2:
            st.info("Comprobante de Transacción")
            if st.session_state.ultimo_ticket:
                st.code(st.session_state.ultimo_ticket, language="text")

    # 3. INVENTARIO
    with t_inv:
        st.markdown("#### Base de Datos de Inventario")
        ver_bajo = st.checkbox("Mostrar únicamente artículos con alerta de stock") 
        
        df_show = df_inv.copy()
        if ver_bajo:
            df_show = df_show[df_show['Cantidad'] <= df_show['Stock_Minimo']]
            
        st.dataframe(
            df_show[['SKU', 'Categoria', 'Modelo', 'Cantidad', 'Costo_Unitario', 'Precio_Venta']], 
            use_container_width=True,
            column_config={
                "Cantidad": st.column_config.ProgressColumn("Unidades Disponibles", format="%d", min_value=0, max_value=int(df_inv['Cantidad'].max() if not df_inv.empty else 100)),
                "Costo_Unitario": st.column_config.NumberColumn("Costo Base", format="$%.2f"),
                "Precio_Venta": st.column_config.NumberColumn("Precio Público", format="$%.2f")
            }
        )

    # 4. ADMINISTRACIÓN DE CATÁLOGO
    if t_adm:
        with t_adm:
            st.markdown("#### Ingreso y Modificación de Artículos")
            act = st.radio("Tipo de Operación", ["Registro Nuevo", "Duplicar Registro", "Modificar Datos", "Ajuste de Existencias"], horizontal=True)
            d_sku, d_mod, d_qty, d_min, d_cost, d_pv = "", "", 1, 2, 0.0, 0.0
            d_cat, d_link, d_ml, d_amz = "Calzado", "", 0.0, 0.0 
            idx_e = -1
            
            if act != "Registro Nuevo" and not df_inv.empty:
                s_ed = st.selectbox("Seleccione el artículo a operar:", df_inv['Modelo'].unique())
                idx_e = df_inv[df_inv['Modelo']==s_ed].index[0]
                r = df_inv.iloc[idx_e]
                d_sku = "" if act=="Duplicar Registro" else r['SKU']
                d_mod = r['Modelo'] + (" (Copia)" if act=="Duplicar Registro" else "")
                d_cat, d_qty = r['Categoria'], int(r['Cantidad'])
                d_min = int(r['Stock_Minimo'])
                d_cost = float(r['Costo_Unitario'])
                d_pv = float(r['Precio_Venta'])
                d_link, d_ml, d_amz = r['Proveedor'], float(r['Precio_ML']), float(r['Precio_Amazon'])

            with st.form("adm"):
                st.markdown("##### Especificaciones del Artículo")
                c1, c2 = st.columns(2)
                f_sku = c1.text_input("Código SKU Interno", d_sku, disabled=(act in ["Modificar Datos", "Ajuste de Existencias"]))
                f_mod = c2.text_input("Descripción Comercial", d_mod, disabled=(act=="Ajuste de Existencias"))
                
                c3, c4, c5 = st.columns(3)
                f_cat = c3.selectbox("Línea de Producto", ["Calzado", "Ropa", "Accesorios"], index=0) 
                f_qty = c4.number_input("Unidades Físicas Ingresadas", value=d_qty)
                f_min = c5.number_input("Punto de Reorden (Stock Mínimo)", value=d_min) 
                
                st.markdown("##### Parámetros Financieros")
                c6, c7, c8 = st.columns(3)
                f_cos = c6.number_input("Costo de Adquisición Unitario", value=d_cost)
                f_pv = c7.number_input("Precio de Venta Sugerido", value=d_pv)
                f_lnk = c8.text_input("Identificador de Proveedor", d_link)
                
                c9, c10 = st.columns(2)
                f_ml = c9.number_input("Precio Mercado Libre", value=d_ml) 
                f_amz = c10.number_input("Precio Amazon", value=d_amz) 
                
                if st.form_submit_button("Aplicar Cambios en Base de Datos"):
                    if not f_mod: st.error("La descripción del artículo no puede estar vacía.")
                    else:
                        f_mod = sanitizar_texto(f_mod)
                        f_sku = sanitizar_texto(f_sku)
                        if not f_sku: f_sku = f"TR-{str(uuid.uuid4())[:6].upper()}"
                        new_d = {'SKU': f_sku, 'Categoria': f_cat, 'Modelo': f_mod, 'Tipo': 'Retail', 'Cantidad': f_qty, 'Stock_Minimo': f_min, 'Costo_Unitario': f_cos, 'Precio_Venta': f_pv, 'Proveedor': f_lnk, 'Precio_ML': f_ml, 'Precio_Amazon': f_amz}
                        
                        if act in ["Modificar Datos", "Ajuste de Existencias"] and idx_e != -1:
                            diff = f_qty - df_inv.at[idx_e, 'Cantidad']
                            for k,v in new_d.items(): df_inv.at[idx_e, k] = v
                            guardar_df(df_inv, ARCHIVO_INVENTARIO)
                            registrar_historial("AJUSTE_INV", f_sku, f_mod, abs(diff), 0, 0, "Modificación desde Panel Admin")
                            st.success("Registro actualizado en la base de datos.")
                        else:
                            df_inv = pd.concat([df_inv, pd.DataFrame([new_d])], ignore_index=True)
                            guardar_df(df_inv, ARCHIVO_INVENTARIO)
                            registrar_historial("ENTRADA_INV", f_sku, f_mod, f_qty, 0, f_cos, "Alta de Nuevo Artículo")
                            st.success("Artículo dado de alta exitosamente.")
                        time.sleep(1)
                        st.rerun()

    # 5. REPORTES FINANCIEROS Y BONOS (ADMIN)
    if t_rep:
        with t_rep:
            st.markdown("#### Análisis Comercial y de Rentabilidad")
            freq = st.radio("Período de Agrupación:", ["Diario", "Mensual"], horizontal=True)
            
            if df_full is not None and not df_full.empty:
                df_c = df_full.copy()
                grp = df_c['Fecha_Dt'].dt.date if freq=="Diario" else df_c['Fecha_Dt'].dt.strftime('%Y-%m')
                
                st.markdown("### Estado de Resultados (Simplificado)")
                tab = df_c.groupby(grp)[['Monto_Venta', 'Monto_Gasto']].sum()
                tab.columns = ['Ingresos Brutos', 'Costo de Adquisición/Gastos']
                tab['Utilidad Operativa'] = tab['Ingresos Brutos'] - tab['Costo de Adquisición/Gastos']
                st.dataframe(tab.style.format("${:,.2f}"), use_container_width=True)
                
                csv = tab.to_csv().encode('utf-8')
                st.download_button(
                    label="📥 Exportar Estado de Resultados (.csv)",
                    data=csv,
                    file_name='reporte_financiero_tr.csv',
                    mime='text/csv',
                )

                st.divider()
                
                st.markdown("### Indicadores de Desempeño Comercial")
                st.caption("Ajuste los parámetros impositivos y logísticos para calcular el margen neto real de las operaciones de venta.")
                c1, c2 = st.columns(2)
                imp_pct = c1.number_input("Carga Impositiva (Ej. IVA 16%)", 16.0) / 100
                com_pct = c2.number_input("Costo de Transacción (TPV/Plataformas)", 4.0) / 100
                
                vs = df_c[df_c['Accion'].str.contains('VENTA')]
                if not vs.empty:
                    tot_v = vs['Monto_Venta'].sum()
                    tot_c = vs['Costo_Venta'].sum() 
                    bruta = tot_v - tot_c
                    gastos_variables = tot_v * (imp_pct + com_pct)
                    neta = bruta - gastos_variables
                    
                    num_transacciones = len(vs)
                    ticket_promedio = tot_v / num_transacciones if num_transacciones > 0 else 0
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Facturación Total", f"${tot_v:,.2f}")
                    m2.metric("Costo de Ventas (CMV)", f"-${tot_c:,.2f}")
                    m3.metric("Utilidad Bruta", f"${bruta:,.2f}")
                    
                    m4, m5, m6 = st.columns(3)
                    m4.metric("Deducciones (Impuestos y Comisiones)", f"-${gastos_variables:,.2f}")
                    m5.metric("Utilidad Neta", f"${neta:,.2f}")
                    m6.metric("Margen Neto (%)", f"{(neta/tot_v)*100:.2f}%" if tot_v > 0 else "0.00%")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.info(f"💡 **Información Adicional:** Se registraron **{num_transacciones}** transacciones de venta en el histórico, resultando en un **Ticket Promedio de ${ticket_promedio:,.2f}** por operación.")
                else: 
                    st.info("El sistema requiere registrar ventas para calcular métricas de desempeño.")

                st.divider()
                st.markdown("##### Rendimiento por Asesor y Bonos")
                if not vs.empty:
                    com = vs.groupby('Usuario')['Monto_Venta'].sum().reset_index()
                    
                    st.markdown("###### 🏆 Reconocimiento al Mejor Vendedor")
                    top_vendedor = com.loc[com['Monto_Venta'].idxmax()]
                    
                    c_top1, c_top2 = st.columns([1, 2])
                    with c_top1:
                        st.success(f"🥇 **{top_vendedor['Usuario'].upper()}**\n\nLíder de ventas con: **${top_vendedor['Monto_Venta']:,.2f}**")
                    with c_top2:
                        bono_top = st.number_input("Premio Especial 1er Lugar ($):", min_value=0.0, value=500.0, step=50.0)

                    st.markdown("###### 💰 Cálculo General")
                    com['Comisión Base (3%)'] = com['Monto_Venta'] * 0.03
                    
                    c_meta1, c_meta2 = st.columns(2)
                    meta = c_meta1.number_input("Meta de Venta para Bono Extra ($):", value=10000.0)
                    bono_pct = c_meta2.number_input("Porcentaje de Bono sobre excedente (%)", value=5.0) / 100
                    
                    com['Bono Extra'] = com.apply(lambda x: (x['Monto_Venta'] - meta) * bono_pct if x['Monto_Venta'] >= meta else 0, axis=1)
                    com['Premio 1er Lugar'] = com['Usuario'].apply(lambda x: bono_top if x == top_vendedor['Usuario'] else 0.0)
                    com['Total a Pagar'] = com['Comisión Base (3%)'] + com['Bono Extra'] + com['Premio 1er Lugar']
                    
                    st.dataframe(com.style.format({'Monto_Venta': '${:,.2f}', 'Comisión Base (3%)': '${:,.2f}', 'Bono Extra': '${:,.2f}', 'Premio 1er Lugar': '${:,.2f}', 'Total a Pagar': '${:,.2f}'}), use_container_width=True)
            else: 
                st.info("El sistema no cuenta con suficientes registros contables para generar reportes.")

    # 6. MIS VENTAS (Solo Vendedor)
    if t_mis_ventas:
        with t_mis_ventas:
            st.markdown("#### Mis Ventas y Progreso de Bonos")
            if df_full is not None and not df_full.empty:
                vs_all = df_full[df_full['Accion'].str.contains('VENTA')]
                top_user = ""
                if not vs_all.empty:
                    com_all = vs_all.groupby('Usuario')['Monto_Venta'].sum().reset_index()
                    top_user = com_all.loc[com_all['Monto_Venta'].idxmax()]['Usuario']

                vs = df_full[(df_full['Accion'].str.contains('VENTA')) & (df_full['Usuario'] == st.session_state.nombre_usuario)]
                if not vs.empty:
                    tot_v = vs['Monto_Venta'].sum()
                    
                    if st.session_state.nombre_usuario == top_user:
                        st.success("🏆 ¡Felicidades! Actualmente eres el VENDEDOR #1. ¡Mantén el ritmo para llevarte el bono especial!")

                    c_meta1, c_meta2 = st.columns(2)
                    meta = c_meta1.number_input("Mi Meta de Venta asignada ($):", value=10000.0)
                    bono_pct = c_meta2.number_input("Bono sobre excedente (%):", value=5.0) / 100
                    
                    comision_base = tot_v * 0.03
                    bono_extra = (tot_v - meta) * bono_pct if tot_v >= meta else 0
                    bono_primer_lugar = 500.0 if st.session_state.nombre_usuario == top_user else 0.0
                    total_pagar = comision_base + bono_extra + bono_primer_lugar
                    
                    st.metric("Mi Facturación Total", f"${tot_v:,.2f}")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Comisión Base (3%)", f"${comision_base:,.2f}")
                    m2.metric("Bono Extra", f"${bono_extra:,.2f}")
                    m3.metric("Total de Bonos", f"${total_pagar:,.2f}")
                    
                    st.divider()
                    st.markdown("##### Historial de mis ventas")
                    st.dataframe(vs[['Fecha', 'Modelo', 'Cantidad', 'Monto_Venta']], hide_index=True, use_container_width=True)
                else:
                    st.info("Aún no tienes ventas registradas.")
