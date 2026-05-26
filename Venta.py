import streamlit as st
import pandas as pd
import os
import time
import random
import uuid
import hashlib
import re
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN VISUAL CORPORATIVA
# ==========================================
st.set_page_config(page_title="Tenis Rey | Sport", page_icon="👟", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #B71C1C !important; font-weight: 700 !important; letter-spacing: -0.5px; }
    div[data-testid="stMetric"] { background-color: var(--secondary-background-color); border: 1px solid rgba(128, 128, 128, 0.2); border-left: 4px solid #B71C1C; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stMetricLabel"] { color: var(--text-color) !important; opacity: 0.8; font-weight: 600; }
    div[data-testid="stMetricValue"] { color: var(--text-color) !important; font-weight: 700; }
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea { background-color: var(--secondary-background-color) !important; color: var(--text-color) !important; border: 1px solid rgba(128, 128, 128, 0.3) !important; border-radius: 6px !important; }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus { border-color: #B71C1C !important; box-shadow: 0 0 0 1px #B71C1C !important; }
    div[data-baseweb="select"] span { color: var(--text-color) !important; }
    div.stButton > button { width: 100%; background-color: #B71C1C; color: #ffffff !important; font-weight: 600; border: 1px solid #B71C1C; border-radius: 6px; transition: all 0.2s ease; }
    div.stButton > button:hover { background-color: #D32F2F; border-color: #D32F2F; color: #ffffff !important; transform: translateY(-1px); box-shadow: 0 4px 8px rgba(183, 28, 28, 0.2); }
    .login-card { background-color: var(--secondary-background-color); padding: 2.5rem; border-radius: 12px; border: 1px solid rgba(183, 28, 28, 0.2); box-shadow: 0 8px 24px rgba(0,0,0,0.05); text-align: center; }
    .stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid rgba(128,128,128,0.2); }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { background-color: rgba(183, 28, 28, 0.05); border-bottom: 3px solid #B71C1C; color: #B71C1C !important; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# Archivos de datos
ARCHIVO_INVENTARIO = 'tr_inventario.csv'
ARCHIVO_HISTORIAL = 'tr_historial.csv'
ARCHIVO_PEDIDOS = 'tr_pedidos.csv'
ARCHIVO_USUARIOS = 'tr_usuarios.csv'
ARCHIVO_CRM = 'tr_crm.csv'

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

@st.cache_data(show_spinner=False)
def cargar_csv(archivo, columnas):
    if not os.path.exists(archivo): return pd.DataFrame(columns=columnas)
    try:
        df = pd.read_csv(archivo)
        if df.empty: return pd.DataFrame(columns=columnas)
        for col in columnas:
            if col not in df.columns: 
                df[col] = 0.0 if any(x in col for x in ["Precio", "Costo", "Cantidad", "Minimo"]) else ""
        return df
    except: return pd.DataFrame(columns=columnas)

def cargar_inventario():
    cols = ['SKU', 'Categoria', 'Genero', 'Modelo', 'Talla', 'Tipo', 'Cantidad', 'Stock_Minimo', 'Costo_Unitario', 'Precio_Venta', 'Proveedor']
    df = cargar_csv(ARCHIVO_INVENTARIO, cols)
    if df.empty:
        datos = [
            {'SKU': 'NK-AJ1-RED-27', 'Categoria': 'Calzado', 'Genero': 'Hombre', 'Modelo': 'Nike Air Jordan 1 Rojo', 'Talla': '27', 'Tipo': 'Mayorista', 'Cantidad': 12, 'Stock_Minimo': 3, 'Costo_Unitario': 1200.0, 'Precio_Venta': 2500.0, 'Proveedor': 'Dist Nacional'},
            {'SKU': 'AD-ULB-BLK-26', 'Categoria': 'Calzado', 'Genero': 'Mujer', 'Modelo': 'Adidas Ultraboost Negro', 'Talla': '26', 'Tipo': 'Mayorista', 'Cantidad': 8, 'Stock_Minimo': 2, 'Costo_Unitario': 1500.0, 'Precio_Venta': 3200.0, 'Proveedor': 'Directa'}
        ]
        df = pd.DataFrame(datos)
        df.to_csv(ARCHIVO_INVENTARIO, index=False)
    return df

def guardar_df(df, archivo):
    try:
        df.to_csv(archivo, index=False)
        st.cache_data.clear()
    except: pass

def registrar_historial(accion, sku, modelo, cant, precio=0, costo=0, notas="", metodo_pago="Efectivo"):
    nuevo = {
        'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Usuario': st.session_state.nombre_usuario,
        'Accion': accion, 'SKU': sku, 'Modelo': modelo, 'Cantidad': cant,
        'Monto_Venta': float(precio)*int(cant) if "VENTA" in accion else 0,
        'Costo_Venta': float(costo)*int(cant) if "VENTA" in accion else 0,
        'Monto_Gasto': float(costo)*int(cant) if "ALTA" in accion or "ENTRADA" in accion else 0,
        'Notas': notas, 'Metodo_Pago': metodo_pago
    }
    df_h = pd.DataFrame([nuevo])
    df_h.to_csv(ARCHIVO_HISTORIAL, mode='a', header=not os.path.exists(ARCHIVO_HISTORIAL), index=False)
    st.cache_data.clear()

def generar_ticket(sku, modelo, cant, total, user, metodo):
    return f"""
========================================
         TENIS REY - SUCURSAL
========================================
 Fecha:   {datetime.now().strftime("%d/%m/%Y %H:%M")}
 Cajero:  {user}
 Método:  {metodo}
----------------------------------------
 CANT | DESCRIPCION            | IMPORTE
----------------------------------------
 {str(cant).center(4)} | {modelo[:19]:<19} | ${total:,.2f}
 SKU: {sku}
----------------------------------------
           TOTAL A PAGAR: ${total:,.2f}
========================================
         ¡GRACIAS POR SU COMPRA!
========================================
    """

def calc_stats():
    if not os.path.exists(ARCHIVO_HISTORIAL): return pd.DataFrame()
    try: 
        df = pd.read_csv(ARCHIVO_HISTORIAL)
        df['Fecha_Dt'] = pd.to_datetime(df['Fecha'])
        if 'Monto_Gasto' not in df.columns: df['Monto_Gasto'] = 0.0
        if 'Metodo_Pago' not in df.columns: df['Metodo_Pago'] = "Efectivo"
        return df
    except: return pd.DataFrame()

def sincronizar_ecommerce(df_inv):
    """Simula la conexión con una API externa (Mercado Libre / Amazon) para traer pedidos nuevos"""
    nuevos_pedidos = []
    time.sleep(1) # Simula retraso de red
    stock_disponible = df_inv[df_inv['Cantidad'] > 0]
    
    if not stock_disponible.empty and random.random() > 0.3: # 70% de probabilidad de encontrar nuevos pedidos
        num_pedidos = random.randint(1, 3)
        for _ in range(num_pedidos):
            p = stock_disponible.sample(1).iloc[0]
            if p['Cantidad'] > 0:
                plataforma = random.choice(['Mercado Libre', 'Amazon', 'Tienda Nube'])
                nuevos_pedidos.append({'Plataforma': plataforma, 'SKU': p['SKU'], 'Modelo': p['Modelo'], 'Cantidad': 1})
    return nuevos_pedidos

# ==========================================
# 4. INTERFAZ
# ==========================================
if not st.session_state.sesion_iniciada:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><div class='login-card'><h1 style='margin-bottom: 0;'>👟 TENIS REY</h1><p style='opacity: 0.8; color: #B71C1C;'>Sport & Punto de Venta</p></div><br>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("INICIAR SESIÓN"):
                val = verificar_login(u, p)
                if val is not None:
                    st.session_state.sesion_iniciada = True
                    st.session_state.rol_usuario = val['Rol']
                    st.session_state.nombre_usuario = val['Nombre']
                    st.rerun()
                else: st.error("Credenciales incorrectas.")

else:
    df_inv = cargar_inventario()
    df_ped = cargar_csv(ARCHIVO_PEDIDOS, ['ID_Pedido','Fecha','SKU','Modelo','Cantidad','Plataforma','Estado'])
    df_crm = cargar_csv(ARCHIVO_CRM, ['Tipo', 'Nombre', 'Contacto', 'Mensaje_Nota', 'Fecha'])
    
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.write(f"👤 **{st.session_state.nombre_usuario}** ({st.session_state.rol_usuario})")
        if st.button("🔄 Refrescar Pantalla"): st.cache_data.clear(); st.rerun()
        st.divider()
        
        with st.expander("💵 Arqueo de Caja (Por Separado)", expanded=True):
            df_full = calc_stats()
            if not df_full.empty:
                hoy = datetime.now().date()
                ventas_hoy = df_full[(df_full['Fecha_Dt'].dt.date == hoy) & (df_full['Accion'].str.contains('VENTA'))]
                efectivo = ventas_hoy[ventas_hoy['Metodo_Pago'] == 'Efectivo']['Monto_Venta'].sum()
                tarjeta = ventas_hoy[ventas_hoy['Metodo_Pago'] == 'Tarjeta']['Monto_Venta'].sum()
                transf = ventas_hoy[ventas_hoy['Metodo_Pago'] == 'Transferencia']['Monto_Venta'].sum()
                
                st.write(f"💵 Efectivo: **${efectivo:,.2f}**")
                st.write(f"💳 Tarjeta: **${tarjeta:,.2f}**")
                st.write(f"🏦 Transferencia: **${transf:,.2f}**")
                st.markdown(f"**Total General: ${efectivo+tarjeta+transf:,.2f}**")
            else: st.write("Sin ventas registradas hoy.")

        if st.button("Cerrar Sesión"):
            st.session_state.sesion_iniciada = False; st.rerun()

    # --- ÁREA PRINCIPAL ---
    st.markdown("<h2>👟 Panel de Control</h2>", unsafe_allow_html=True)
    
    tabs = st.tabs(["🛒 TPV (Ventas)", "👟 INVENTARIO", "📦 ÓRDENES (E-commerce)", "📝 CATÁLOGO", "📈 REPORTES & BONOS", "📞 MENSAJES (CRM)"]) if st.session_state.rol_usuario == "Administrador" else st.tabs(["🛒 TPV (Ventas)", "👟 INVENTARIO", "📦 ÓRDENES (E-commerce)"])
    
    t_pos = tabs[0]
    t_inv = tabs[1]
    t_ped = tabs[2]
    t_adm = tabs[3] if len(tabs) > 3 else None
    t_rep = tabs[4] if len(tabs) > 3 else None
    t_crm = tabs[5] if len(tabs) > 3 else None

    # 1. TPV (VENTAS Y COBROS + CÓDIGOS DE BARRAS)
    with t_pos:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### Registro de Venta (Soporta Código de Barras)")
            scan = st.text_input("Escanee o escriba el SKU/Modelo:", placeholder="Pistola láser o teclado...")
            sel = None
            if scan:
                scan = sanitizar_texto(scan)
                f = df_inv[df_inv['SKU'].astype(str).str.upper() == scan.upper()]
                if not f.empty: sel = f.iloc[0]
                else: 
                    fn = df_inv[df_inv['Modelo'].str.contains(scan, case=False)]
                    if not fn.empty: sel = fn.iloc[0]
            
            if sel is None and not df_inv.empty:
                op = df_inv[df_inv['Cantidad']>0].apply(lambda x: f"{x['Modelo']} (Talla: {x['Talla']}) | {x['SKU']}", axis=1)
                s = st.selectbox("O selección manual:", op, index=None, placeholder="Buscar en lista...")
                if s: sel = df_inv[df_inv['SKU'] == s.split(" | ")[1]].iloc[0]
            
            if sel is not None:
                idx = df_inv[df_inv['SKU']==sel['SKU']].index[0]
                stock = int(df_inv.at[idx, 'Cantidad'])
                stock_min = int(df_inv.at[idx, 'Stock_Minimo'])
                
                if stock > stock_min:
                    st.success(f"**{sel['Modelo']}** | Género: {sel['Genero']} | Talla: {sel['Talla']} | Stock Físico: {stock}")
                else:
                    st.warning(f"⚠️ **{sel['Modelo']}** | Género: {sel['Genero']} | Talla: {sel['Talla']} | Stock Físico: {stock} (¡Nivel Bajo de Inventario!)")
                
                if stock > 0:
                    cq, cp, cm = st.columns(3)
                    q = cq.number_input("Cantidad", 1, stock, 1)
                    metodo = cm.selectbox("Método Cobro", ["Efectivo", "Tarjeta", "Transferencia"])
                    tot = sel['Precio_Venta'] * q
                    cp.metric("Cobro Total", f"${tot:,.2f}")
                    
                    if st.button("Cobrar Transacción", type="primary", use_container_width=True):
                        df_inv.at[idx, 'Cantidad'] -= q
                        guardar_df(df_inv, ARCHIVO_INVENTARIO)
                        registrar_historial("VENTA_TPV", sel['SKU'], sel['Modelo'], q, sel['Precio_Venta'], sel['Costo_Unitario'], "Mostrador", metodo)
                        st.session_state.ultimo_ticket = generar_ticket(sel['SKU'], sel['Modelo'], q, tot, st.session_state.nombre_usuario, metodo)
                        st.success("Cobro exitoso. Registrado en Arqueo.")
                        time.sleep(0.5)
                        st.rerun()
                else: st.error("Agotado.")

        with c2:
            st.info("Último Ticket")
            if st.session_state.ultimo_ticket: st.code(st.session_state.ultimo_ticket, language="text")

    # 2. INVENTARIO & REDES SOCIALES
    with t_inv:
        c1, c2 = st.columns([3,1])
        c1.markdown("#### Base de Datos")
        ver_bajo = c2.checkbox("Solo bajo stock")
        df_show = df_inv[df_inv['Cantidad'] <= df_inv['Stock_Minimo']] if ver_bajo else df_inv.copy()
        
        st.dataframe(df_show[['SKU', 'Categoria', 'Genero', 'Modelo', 'Talla', 'Cantidad', 'Precio_Venta']], use_container_width=True)
        
        csv_inv = df_show.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Exportar Inventario Actual (.csv)", data=csv_inv, file_name=f'inventario_{datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv')

        st.markdown("#### 📱 Promover por Redes")
        s_redes = st.selectbox("Selecciona un artículo para generar post:", df_inv[df_inv['Cantidad']>0]['Modelo'].unique(), key="s_redes")
        if s_redes:
            r = df_inv[df_inv['Modelo']==s_redes].iloc[0]
            txt = f"🔥 ¡NUEVO INGRESO! 🔥\n👟 {r['Modelo']}\n📏 Talla: {r['Talla']} ({r['Genero']})\n💰 A solo: ${float(r['Precio_Venta']):,.2f}\n\n📦 Entrega inmediata. ¡Mándanos DM antes de que se agoten!"
            st.code(txt, language="text")
            st.caption("Copia este texto para pegarlo en Facebook, Instagram o WhatsApp.")

        if st.session_state.rol_usuario == "Administrador":
            st.markdown("#### 🚨 Remates de Mercancía Parada")
            remates = df_inv[(df_inv['Cantidad'] >= 5)]
            if not remates.empty:
                st.warning("Se detectaron artículos con alto stock sugeridos para liquidación:")
                for _, rem in remates.iterrows():
                    st.write(f"🔻 **{rem['Modelo']}** (Stock: {rem['Cantidad']}) - Precio Actual: ${rem['Precio_Venta']} -> Sugerido: **${float(rem['Costo_Unitario'])*1.1:,.2f}**")
            else: st.success("Inventario rotando correctamente. No hay mercancía estancada.")

    # 3. ÓRDENES (E-COMMERCE)
    with t_ped:
        c1, c2 = st.columns([3, 1])
        c1.markdown("#### Recepción de Pedidos B2C (Externos)")
        
        # Botón para vincular y sincronizar con servicios externos
        if c2.button("🔄 Sincronizar E-commerce", help="Busca nuevos pedidos en plataformas conectadas"):
            with st.spinner("Conectando con plataformas..."):
                nuevos = sincronizar_ecommerce(df_inv)
                if nuevos:
                    for n in nuevos:
                        idx = df_inv[df_inv['SKU']==n['SKU']].index[0]
                        df_inv.at[idx, 'Cantidad'] -= n['Cantidad'] # Descuenta inventario automáticamente
                        
                        reg = {'ID_Pedido':f"EXT-{int(time.time())}-{random.randint(10,99)}", 'Fecha':datetime.now().strftime("%Y-%m-%d"), 'SKU':n['SKU'], 'Modelo':n['Modelo'], 'Cantidad':n['Cantidad'], 'Plataforma':n['Plataforma'], 'Estado':'Pendiente'}
                        df_ped = pd.concat([df_ped, pd.DataFrame([reg])], ignore_index=True)
                        registrar_historial("VENTA_EXTERNA", n['SKU'], n['Modelo'], n['Cantidad'], 0, 0, f"Orden automática de {n['Plataforma']}", "Transferencia")
                    
                    guardar_df(df_inv, ARCHIVO_INVENTARIO)
                    guardar_df(df_ped, ARCHIVO_PEDIDOS)
                    st.success(f"¡Éxito! Se sincronizaron {len(nuevos)} pedidos nuevos.")
                    time.sleep(1.5)
                    st.rerun()
                else: st.info("Todo al día. No se encontraron pedidos nuevos en las plataformas externas.")

        p = df_ped[df_ped['Estado']=='Pendiente']
        if p.empty: 
            st.success("No hay pedidos pendientes de despacho.")
        else:
            for i, r in p.iterrows():
                cc1, cc2, cc3 = st.columns([4, 2, 2])
                cc1.write(f"**{r['Modelo']}** (SKU: {r['SKU']}) - Cant: {r['Cantidad']}")
                cc2.write(f"Plataforma: {r['Plataforma']} | Ref: {r['ID_Pedido']}")
                if cc3.button("Marcar Despachado", key=r['ID_Pedido']):
                    df_ped.loc[df_ped['ID_Pedido']==r['ID_Pedido'], 'Estado']='Enviado'
                    guardar_df(df_ped, ARCHIVO_PEDIDOS)
                    st.rerun()

    # 4. ADMINISTRACIÓN DE CATÁLOGO (Subir Mercancía)
    if t_adm:
        with t_adm:
            st.markdown("#### Ingresar / Editar Mercancía (Modelos, Números, Géneros)")
            with st.form("form_cat", clear_on_submit=True):
                c1, c2, c3 = st.columns([1,2,1])
                f_sku = c1.text_input("Código de Barras/SKU")
                f_mod = c2.text_input("Nombre del Modelo")
                f_cat = c3.selectbox("Categoría", ["Calzado", "Ropa", "Accesorios"])
                
                c4, c5, c6 = st.columns(3)
                f_talla = c4.text_input("Número / Talla (Ej. 27, M, Única)")
                f_gen = c5.selectbox("Género", ["Hombre", "Mujer", "Unisex", "Niños"])
                f_qty = c6.number_input("Cantidad Física", min_value=0, value=1)
                
                c7, c8, c9 = st.columns(3)
                f_cos = c7.number_input("Costo", min_value=0.0)
                f_pv = c8.number_input("Precio Venta", min_value=0.0)
                f_min = c9.number_input("Stock Mínimo", min_value=1, value=2)

                if st.form_submit_button("Subir Mercancía"):
                    if not f_mod or not f_sku or not f_talla: st.error("Llene SKU, Modelo y Talla obligatoriamente.")
                    else:
                        idx = df_inv.index[df_inv['SKU'] == f_sku].tolist()
                        if idx: # Update
                            i = idx[0]
                            df_inv.at[i, 'Cantidad'] += f_qty
                            df_inv.at[i, 'Precio_Venta'] = f_pv
                            st.success("Inventario actualizado. Se sumó mercancía al SKU existente.")
                        else: # Insert
                            new_d = {'SKU': f_sku, 'Categoria': f_cat, 'Genero': f_gen, 'Modelo': f_mod, 'Talla': f_talla, 'Tipo': 'Retail', 'Cantidad': f_qty, 'Stock_Minimo': f_min, 'Costo_Unitario': f_cos, 'Precio_Venta': f_pv, 'Proveedor': ''}
                            df_inv = pd.concat([df_inv, pd.DataFrame([new_d])], ignore_index=True)
                            st.success("Mercancía subida correctamente.")
                        guardar_df(df_inv, ARCHIVO_INVENTARIO)
                        registrar_historial("SUBIR_MERCANCIA", f_sku, f_mod, f_qty, 0, f_cos, "Carga en Catálogo")
                        time.sleep(0.5); st.rerun()

    # 5. REPORTES Y BONOS
    if t_rep:
        with t_rep:
            df_full = calc_stats()
            if not df_full.empty:
                st.markdown("#### Bonos por Ventas")
                meta = st.number_input("Meta de Venta Mensual ($) para Bono:", value=10000)
                bono_pct = st.number_input("Porcentaje de Bono sobre excedente (%):", value=5.0) / 100
                
                vs = df_full[df_full['Accion'].str.contains('VENTA')]
                if not vs.empty:
                    com = vs.groupby('Usuario')['Monto_Venta'].sum().reset_index()
                    com['Meta Alcanzada'] = com['Monto_Venta'] >= meta
                    com['Bono Extra'] = com.apply(lambda x: (x['Monto_Venta'] - meta) * bono_pct if x['Meta Alcanzada'] else 0, axis=1)
                    com['Pago Total (Venta + Bono)'] = com['Monto_Venta'] + com['Bono Extra']
                    st.dataframe(com.style.format({'Monto_Venta': '${:,.2f}', 'Bono Extra': '${:,.2f}', 'Pago Total (Venta + Bono)': '${:,.2f}'}), use_container_width=True)
                    
                    csv_rep = com.to_csv(index=False).encode('utf-8')
                    st.download_button(label="📥 Descargar Reporte de Bonos (.csv)", data=csv_rep, file_name=f'reporte_bonos_{datetime.now().strftime("%Y%m")}.csv', mime='text/csv')

    # 6. CRM (Mensajes Clientes y Proveedores)
    if t_crm:
        with t_crm:
            st.markdown("#### Libreta de Mensajes y Contactos")
            with st.form("crm_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                tipo = c1.radio("Registro para:", ["Proveedor", "Cliente"])
                nombre = c2.text_input("Nombre de la Persona / Empresa")
                contacto = st.text_input("Teléfono o Correo")
                nota = st.text_area("Mensaje / Petición / Nota")
                
                if st.form_submit_button("Guardar Mensaje"):
                    if nombre and nota:
                        new_crm = {'Tipo': tipo, 'Nombre': nombre, 'Contacto': contacto, 'Mensaje_Nota': nota, 'Fecha': datetime.now().strftime("%Y-%m-%d")}
                        df_crm = pd.concat([df_crm, pd.DataFrame([new_crm])], ignore_index=True)
                        guardar_df(df_crm, ARCHIVO_CRM)
                        st.success("Guardado en el directorio.")
                        time.sleep(0.5); st.rerun()

            st.divider()
            c_cli, c_pro = st.columns(2)
            with c_cli:
                st.markdown("##### Mensajes de Clientes")
                st.dataframe(df_crm[df_crm['Tipo']=='Cliente'][['Fecha', 'Nombre', 'Mensaje_Nota']], hide_index=True)
            with c_pro:
                st.markdown("##### Mensajes de Proveedores")
                st.dataframe(df_crm[df_crm['Tipo']=='Proveedor'][['Fecha', 'Nombre', 'Mensaje_Nota']], hide_index=True)

            st.divider()
            # ==========================================
            # NUEVO: CENTRO DE ENVÍO DE MENSAJES REALES
            # ==========================================
            st.markdown("#### 🚀 Centro de Envío Rápido")
            if not df_crm.empty:
                c_sel, c_acc = st.columns([2, 2])
                with c_sel:
                    contacto_sel = st.selectbox("Seleccione un contacto guardado:", df_crm['Nombre'].unique())
                    datos_contacto = df_crm[df_crm['Nombre'] == contacto_sel].iloc[0]
                    num_correo = str(datos_contacto['Contacto']).strip()
                    st.info(f"**Vía de contacto registrada:** {num_correo}")
                
                with c_acc:
                    st.write("Acciones de Comunicación:")
                    msg_pred = f"Hola {contacto_sel}, te contactamos de la gerencia de Tenis Rey."
                    
                    # Extraer solo números para validación de WhatsApp
                    num_limpio = ''.join(filter(str.isdigit, num_correo))
                    
                    col_wa, col_em = st.columns(2)
                    
                    # Botón dinámico de WhatsApp
                    if num_limpio and len(num_limpio) >= 10:
                        link_wa = f"https://wa.me/{num_limpio}?text={msg_pred.replace(' ', '%20')}"
                        col_wa.link_button("🟢 Enviar WhatsApp", link_wa, use_container_width=True)
                    else:
                        col_wa.button("🟢 Enviar WhatsApp", disabled=True, help="Requiere un número de 10 dígitos", use_container_width=True)
                        
                    # Botón dinámico de Correo Electrónico
                    if "@" in num_correo and "." in num_correo:
                        link_mail = f"mailto:{num_correo}?subject=Seguimiento%20Tenis%20Rey&body={msg_pred.replace(' ', '%20')}"
                        col_em.link_button("📧 Enviar Correo", link_mail, use_container_width=True)
                    else:
                        col_em.button("📧 Enviar Correo", disabled=True, help="Requiere un formato de correo válido (@)", use_container_width=True)
            else:
                st.info("Guarde un contacto en la libreta superior para habilitar el envío rápido de mensajes.")
