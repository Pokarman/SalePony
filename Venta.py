import streamlit as st
import pandas as pd
import os
import time
import random
import uuid
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN GENERAL Y ESTILO
# ==========================================
st.set_page_config(page_title="SalePony Gold", page_icon="🦄", layout="wide")

# Estilos CSS Personalizados (Adaptables a Modo Oscuro)
st.markdown("""
    <style>
    /* Títulos Principales en Dorado */
    h1, h2, h3 {
        color: #C5A059 !important; /* Dorado elegante */
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Métricas Responsivas (Se adaptan al tema claro/oscuro) */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color); /* Color de fondo inteligente */
        border-left: 4px solid #C5A059; /* Borde dorado */
        padding: 10px;
        border-radius: 5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Texto de métricas visible en ambos modos */
    div[data-testid="stMetricLabel"] {
        color: var(--text-color) !important;
    }
    div[data-testid="stMetricValue"] {
        color: var(--text-color) !important;
    }

    /* Botones Primarios (Estilo Gold) */
    div.stButton > button:first-child {
        background-color: #111111; /* Fondo negro */
        color: #C5A059; /* Texto dorado */
        border: 1px solid #C5A059;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #C5A059; /* Al pasar mouse, fondo dorado */
        border-color: #FFFFFF;
        color: #000000; /* Texto negro */
    }
    </style>
    """, unsafe_allow_html=True)

# Nombres de archivos
ARCHIVO_INVENTARIO = 'mi_inventario.csv'
ARCHIVO_HISTORIAL = 'historial_movimientos.csv'
ARCHIVO_PEDIDOS = 'pedidos_pendientes.csv'
ARCHIVO_USUARIOS = 'usuarios_seguridad.csv'
ARCHIVO_CONFIG_API = 'config_apis.csv'

# ==========================================
# 2. GESTIÓN DE SEGURIDAD Y USUARIOS
# ==========================================

def cargar_usuarios():
    if not os.path.exists(ARCHIVO_USUARIOS):
        usuarios_defecto = [
            {'Usuario': 'admin', 'Clave': 'admin123', 'Rol': 'Administrador', 'Nombre': 'CEO SalePony'},
            {'Usuario': 'operador', 'Clave': 'op123', 'Rol': 'Vendedor', 'Nombre': 'Operador Logístico'}
        ]
        df = pd.DataFrame(usuarios_defecto)
        df.to_csv(ARCHIVO_USUARIOS, index=False)
        return df
    return pd.read_csv(ARCHIVO_USUARIOS)

def verificar_login(usuario, clave):
    df = cargar_usuarios()
    found = df[(df['Usuario'] == usuario) & (df['Clave'] == clave)]
    return found.iloc[0] if not found.empty else None

if 'sesion_iniciada' not in st.session_state:
    st.session_state.sesion_iniciada = False
    st.session_state.rol_usuario = None
    st.session_state.nombre_usuario = None
    st.session_state.ultimo_ticket = ""

# ==========================================
# 3. LÓGICA DE DATOS Y NEGOCIO
# ==========================================

@st.cache_data(show_spinner=False)
def cargar_csv(archivo, columnas):
    """Carga robusta de CSV."""
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
    """Genera el catálogo inicial de Best Sellers si está vacío."""
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
    """Simula la conexión a APIs de ML y Amazon."""
    nuevos = []
    msgs = ["🔵 Conectando Mercado Libre...", "🟠 Conectando Amazon..."]
    time.sleep(1.5)
    
    if not df_inv.empty and random.random() > 0.6: # 40% chance de venta
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
    return df, None, df # Simplificado para evitar redundancia

# ==========================================
# 4. INTERFAZ GRÁFICA
# ==========================================

# --- LOGIN ---
if not st.session_state.sesion_iniciada:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<h1 style='text-align: center; color: #C5A059;'>🦄 SalePony Gold</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Acceso al Sistema Integral</p>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("INGRESAR", use_container_width=True):
                val = verificar_login(u, p)
                if val is not None:
                    st.session_state.sesion_iniciada = True
                    st.session_state.rol_usuario = val['Rol']
                    st.session_state.nombre_usuario = val['Nombre']
                    st.rerun()
                else: st.error("Acceso Denegado")
        st.caption("Admin: admin/admin123 | Op: operador/op123")

# --- APP ---
else:
    df_inv = cargar_inventario()
    df_ped = cargar_csv(ARCHIVO_PEDIDOS, ['ID_Pedido', 'Fecha', 'SKU', 'Modelo', 'Cantidad', 'Plataforma', 'Estado'])
    
    # --- SIDEBAR ---
    st.sidebar.markdown(f"### 👤 {st.session_state.nombre_usuario}")
    st.sidebar.caption(f"Rol: {st.session_state.rol_usuario}")
    st.sidebar.divider()
    
    # 1. Calculadora Importación
    with st.sidebar.expander("🇨🇳 Calc. Importación"):
        costo = st.number_input("Costo China ($)", 0.0, step=10.0)
        envio = st.number_input("Envío/Impuestos ($)", 0.0, step=10.0)
        venta = st.number_input("Precio Venta ($)", 0.0, step=10.0)
        if st.button("Calcular"):
            total = costo + envio
            comision = venta * 0.15 # ML fee aprox
            ganancia = venta - total - comision
            if ganancia > 0: st.success(f"Ganancia: ${ganancia:,.2f}")
            else: st.error(f"Pérdida: ${ganancia:,.2f}")

    # 2. Corte de Caja
    with st.sidebar.expander("💰 Corte de Caja"):
        raw, _, df_full = calcular_stats()
        esperado = 0.0
        if df_full is not None and not df_full.empty:
            hoy = datetime.now().date()
            mask = (df_full['Fecha_Dt'].dt.date == hoy) & (df_full['Accion'].str.contains('VENTA')) & (df_full['Usuario'] == st.session_state.nombre_usuario)
            esperado = df_full[mask]['Monto_Venta'].sum()
        st.write(f"Esperado: ${esperado:,.2f}")
        real = st.number_input("Efectivo:", 0.0)
        if st.button("Validar"):
            diff = real - esperado
            if diff == 0: st.success("Exacto")
            elif diff > 0: st.warning(f"Sobra ${diff}")
            else: st.error(f"Falta ${abs(diff)}")

    # 3. Configuración API (Solo Admin)
    if st.session_state.rol_usuario == "Administrador":
        with st.sidebar.expander("🔌 Conexiones API"):
            st.text_input("Mercado Libre ID", type="password")
            st.text_input("Amazon Token", type="password")
            st.caption("Tokens guardados en sesión segura.")

    if st.sidebar.button("🔄 Sincronizar Marketplaces", type="primary"):
        with st.spinner("Conectando..."):
            news, logs = sincronizar_marketplaces(df_inv)
            for l in logs: st.toast(l)
            if news:
                for n in news:
                    idx = df_inv[df_inv['SKU']==n['SKU']].index[0]
                    df_inv.at[idx, 'Cantidad'] -= n['Cantidad']
                    new_p = {'ID_Pedido':f"ORD-{int(time.time())}", 'Fecha':datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'SKU':n['SKU'], 'Modelo':n['Modelo'], 'Cantidad':n['Cantidad'], 'Plataforma':n['Plataforma'], 'Estado':'Pendiente'}
                    df_ped = pd.concat([df_ped, pd.DataFrame([new_p])], ignore_index=True)
                    registrar_historial("VENTA_AUTO", n['SKU'], n['Modelo'], n['Cantidad'], 0, 0, f"Venta {n['Plataforma']}")
                guardar_df(df_inv, ARCHIVO_INVENTARIO)
                guardar_df(df_ped, ARCHIVO_PEDIDOS)
                st.success(f"{len(news)} Pedidos nuevos!")
                time.sleep(1)
                st.rerun()

    if st.sidebar.button("Salir"):
        st.session_state.sesion_iniciada = False
        st.rerun()

    # --- DASHBOARD ---
    st.title("🦄 SalePony Gold Edition")
    
    # KPIs
    pend = df_ped[df_ped['Estado']=='Pendiente'].shape[0]
    low = df_inv[df_inv['Cantidad'] <= df_inv['Stock_Minimo']].shape[0]
    
    raw, _, df_full = calcular_stats()
    ventas_hoy = 0
    if df_full is not None and not df_full.empty:
        hoy = datetime.now().date()
        m = df_full[(df_full['Fecha_Dt'].dt.date == hoy) & (df_full['Accion'].str.contains('VENTA'))]
        ventas_hoy = m['Monto_Venta'].sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ventas Hoy (Global)", f"${ventas_hoy:,.2f}")
    k2.metric("Pedidos Web", pend, delta_color="inverse" if pend>0 else "normal")
    k3.metric("Stock Crítico", low, delta_color="inverse")
    k4.metric("Marketplaces", "En Línea 🟢")

    st.divider()

    # PESTAÑAS
    tabs = st.tabs(["📦 Pedidos Web", "🛒 Punto de Venta", "📱 Inventario", "📝 Admin", "📊 Reportes"]) if st.session_state.rol_usuario == "Administrador" else st.tabs(["📦 Pedidos Web", "🛒 Punto de Venta", "📱 Consultar"])
    
    t_ped, t_pos, t_inv = tabs[0], tabs[1], tabs[2]
    t_adm = tabs[3] if len(tabs) > 3 else None
    t_rep = tabs[4] if len(tabs) > 3 else None

    # 1. PEDIDOS WEB
    with t_ped:
        st.subheader("Gestión de Envíos (ML / Amazon)")
        p_list = df_ped[df_ped['Estado']=='Pendiente']
        if p_list.empty: st.info("✅ Todo despachado.")
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
                        st.toast("Actualizado")
                        time.sleep(0.5)
                        st.rerun()
                    st.divider()

    # 2. PUNTO DE VENTA
    with t_pos:
        c_izq, c_der = st.columns([2, 1])
        with c_izq:
            st.subheader("Venta Mostrador")
            scan = st.text_input("🔫 Escáner SKU", placeholder="Clic y escanear...")
            sel = None
            
            if scan:
                f = df_inv[df_inv['SKU'].astype(str) == scan]
                if not f.empty:
                    sel = f.iloc[0]
                    st.success(f"Producto: {sel['Modelo']}")
                else: st.warning("SKU no encontrado")
            
            if not df_inv.empty:
                ok = df_inv[df_inv['Cantidad'] > 0]
                if sel is None:
                    op = ok.apply(lambda x: f"{x['Modelo']} | {x['SKU']}", axis=1)
                    s = st.selectbox("Búsqueda Manual", op)
                    sel = df_inv[df_inv['SKU'] == s.split(" | ")[1]].iloc[0] if s else None
                
                if sel is not None:
                    idx = df_inv[df_inv['SKU'] == sel['SKU']].index[0]
                    item = df_inv.iloc[idx]
                    stock_real_actual = int(item['Cantidad']) # Candado de stock
                    
                    st.markdown(f"**{item['Modelo']}** | Disp: {item['Cantidad']}")
                    cq, cp = st.columns(2)
                    q = cq.number_input("Cantidad", 1, max(1, stock_real_actual), 1)
                    tot = item['Precio_Venta'] * q
                    cp.metric("Total", f"${tot:,.2f}")
                    
                    if st.button("COBRAR", type="primary", use_container_width=True):
                        # --- VERIFICACIÓN DE SEGURIDAD FINAL ---
                        if q > stock_real_actual:
                            st.error(f"⛔ ERROR: Intentas vender {q} pero solo hay {stock_real_actual} en existencia. Actualiza la página.")
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
        st.subheader("Inventario y Proveedores")
        cols = ['SKU', 'Modelo', 'Cantidad', 'Stock_Minimo', 'Link_AliExpress', 'Precio_ML', 'Precio_Amazon']
        st.dataframe(df_inv[cols], use_container_width=True, column_config={"Link_AliExpress": st.column_config.LinkColumn("Comprar China")})

    # 4. ADMIN (Solo Admin)
    if t_adm:
        with t_adm:
            st.subheader("Gestión de Productos")
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
                    if not f_mod: st.error("Nombre requerido")
                    else:
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

    # 5. REPORTES (Solo Admin)
    if t_rep:
        with t_rep:
            st.subheader("Inteligencia de Negocio")
            
            # Introducción educativa para finanzas
            with st.expander("📚 Ayuda: ¿Cómo entender mis números?"):
                st.markdown("""
                **1. Flujo de Caja (Dinero Real):** Muestra si entró o salió dinero de tu cuenta hoy.  
                *Ingresos (Ventas) - Egresos (Compras de Mercancía).*
                
                **2. Rentabilidad (Ganancia del Producto):** Muestra si estás ganando dinero en cada venta, ignorando si compraste stock hoy o el mes pasado.  
                *Precio Venta - Costo Producto - Impuestos - Comisiones.*
                """)

            freq = st.radio("Agrupar:", ["Día", "Mes"], horizontal=True)
            if df_full is not None and not df_full.empty:
                df_c = df_full.copy()
                grp = df_c['Fecha_Dt'].dt.date if freq=="Día" else df_c['Fecha_Dt'].dt.strftime('%Y-%m')
                
                # --- SECCIÓN 1: Flujo de Caja ---
                st.markdown("### 1. Flujo de Dinero (Entradas vs Salidas)")
                tab = df_c.groupby(grp)[['Monto_Venta', 'Monto_Gasto']].sum()
                tab.columns = ['Ventas ($)', 'Compras Stock ($)']
                tab['Flujo Neto'] = tab['Ventas ($)'] - tab['Compras Stock ($)']
                st.dataframe(tab.style.format("${:,.2f}"), use_container_width=True)
                
                st.divider()
                
                # --- SECCIÓN 2: Rentabilidad Real ---
                st.markdown("### 2. Rentabilidad Real (Ganancia Libre)")
                
                # Inputs interactivos para calcular ganancia neta
                c1, c2 = st.columns(2)
                imp_pct = c1.number_input("Impuestos (%)", value=16.0) / 100
                com_pct = c2.number_input("Comisión Plataforma (%)", value=15.0) / 100
                
                ventas_solo = df_c[df_c['Accion'].str.contains('VENTA')]
                if not ventas_solo.empty:
                    # Calculamos totales
                    total_vendido = ventas_solo['Monto_Venta'].sum()
                    costo_vendido = ventas_solo['Costo_Venta'].sum()
                    
                    # Matemática financiera
                    ganancia_bruta = total_vendido - costo_vendido
                    gastos_imuestos = total_vendido * imp_pct
                    gastos_comis = total_vendido * com_pct
                    ganancia_neta = ganancia_bruta - gastos_imuestos - gastos_comis
                    
                    # Mostrar resultados claros
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Venta Total", f"${total_vendido:,.2f}")
                    m2.metric("Costo Mercancía", f"-${costo_vendido:,.2f}")
                    m3.metric("Utilidad Bruta", f"${ganancia_bruta:,.2f}")
                    
                    m4, m5, m6 = st.columns(3)
                    m4.metric("Impuestos/Comis.", f"-${gastos_imuestos + gastos_comis:,.2f}")
                    m5.metric("💰 Ganancia LIBRE", f"${ganancia_neta:,.2f}", delta="Tu dinero real")
                    if total_vendido > 0:
                        margen = (ganancia_neta / total_vendido) * 100
                        m6.metric("Margen Neto", f"{margen:.1f}%")
                else:
                    st.info("No hay ventas para calcular rentabilidad.")

                st.divider()
                st.markdown("##### Comisiones Empleados")
                if not ventas_solo.empty:
                    com = ventas_solo.groupby('Usuario')['Monto_Venta'].sum().reset_index()
                    com['Pago (3%)'] = com['Monto_Venta'] * 0.03
                    st.dataframe(com.style.format({'Monto_Venta': '${:,.2f}', 'Pago (3%)': '${:,.2f}'}), use_container_width=True)
            else: st.info("Sin datos.")
