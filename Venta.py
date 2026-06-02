import streamlit as st
import pandas as pd
import os
import time
import random
import uuid
import hashlib
import re
import smtplib 
import urllib.parse
import base64
import streamlit.components.v1 as components
import pyotp 
from email.mime.text import MIMEText 
from email.mime.multipart import MIMEMultipart 
from email.mime.image import MIMEImage
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN VISUAL CORPORATIVA (MEJORADA)
# ==========================================
st.set_page_config(page_title="SportKing | Sport", page_icon="👟", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    h1, h2, h3 { 
        background: linear-gradient(135deg, #FF1744 0%, #B71C1C 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important; 
        letter-spacing: -0.5px; 
    }

    div[data-testid="stMetric"] { 
        background: linear-gradient(145deg, var(--secondary-background-color), rgba(183, 28, 28, 0.03));
        border: 1px solid rgba(183, 28, 28, 0.2); 
        border-left: 5px solid #FF1744; 
        border-radius: 12px; 
        padding: 20px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
        transition: all 0.3s ease-in-out;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(255, 23, 68, 0.15);
        border-left: 5px solid #D50000;
    }
    div[data-testid="stMetricLabel"] { color: var(--text-color) !important; opacity: 0.7; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px; }
    div[data-testid="stMetricValue"] { color: var(--text-color) !important; font-weight: 800; font-size: 2rem; }

    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea { 
        background-color: var(--secondary-background-color) !important; 
        color: var(--text-color) !important; 
        border: 1px solid rgba(128, 128, 128, 0.2) !important; 
        border-radius: 8px !important; 
        transition: all 0.3s ease;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within { 
        border-color: #FF1744 !important; 
        box-shadow: 0 0 0 2px rgba(255, 23, 68, 0.2) !important; 
    }
    div[data-baseweb="select"] span { color: var(--text-color) !important; }

    div.stButton > button { 
        width: 100%; 
        background: linear-gradient(135deg, #D50000 0%, #B71C1C 100%); 
        color: #ffffff !important; 
        font-weight: 700; 
        border: none; 
        border-radius: 8px; 
        padding: 0.5rem 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
        box-shadow: 0 4px 6px rgba(183, 28, 28, 0.2);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div.stButton > button:hover { 
        background: linear-gradient(135deg, #FF1744 0%, #D50000 100%); 
        transform: translateY(-2px) scale(1.01); 
        box-shadow: 0 8px 20px rgba(255, 23, 68, 0.4); 
    }
    div.stButton > button:active {
        transform: translateY(1px) scale(0.98);
    }

    .login-card { 
        background: var(--secondary-background-color); 
        padding: 3rem; 
        border-radius: 16px; 
        border: 1px solid rgba(255, 23, 68, 0.15); 
        box-shadow: 0 15px 35px rgba(0,0,0,0.1), 0 0 20px rgba(255, 23, 68, 0.05); 
        text-align: center; 
        backdrop-filter: blur(10px);
    }
    
    .stTabs [data-baseweb="tab-list"] { 
        border-bottom: 2px solid rgba(128,128,128,0.1); 
        gap: 20px;
    }
    .stTabs [data-baseweb="tab-list"] button {
        padding-bottom: 10px !important;
        transition: color 0.3s ease;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { 
        background-color: transparent; 
        border-bottom: 3px solid #FF1744; 
        color: #FF1744 !important; 
        font-weight: 700; 
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="false"]:hover {
        color: #D50000 !important;
    }
    </style>
""", unsafe_allow_html=True)

ARCHIVO_INVENTARIO = 'tr_inventario.csv'
ARCHIVO_HISTORIAL = 'tr_historial.csv'
ARCHIVO_PEDIDOS = 'tr_pedidos.csv'
ARCHIVO_PEDIDOS_MANUALES = 'tr_pedidos_manuales.csv' # NUEVO ARCHIVO
ARCHIVO_USUARIOS = 'tr_usuarios.csv' 
ARCHIVO_CONFIG_API = 'tr_config_apis.csv'
ARCHIVO_CRM = 'tr_crm.csv' 
ARCHIVO_INBOX = 'tr_inbox.csv'
ARCHIVO_CUPONES = 'tr_cupones.csv' 

# ==========================================
# 2. SEGURIDAD Y DATOS
# ==========================================
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def sanitizar_texto(texto):
    if isinstance(texto, str): return re.sub(r'[;,\n\r]', ' ', texto).strip()
    return texto

def image_to_base64(image_file):
    if image_file is not None:
        return base64.b64encode(image_file.read()).decode('utf-8')
    return ""

def cargar_usuarios():
    # CLAVES FIJAS PARA EVITAR REINICIOS
    if not os.path.exists(ARCHIVO_USUARIOS):
        usuarios_defecto = [
            {'Usuario': 'admin', 'Clave': hash_password('admin123'), 'Rol': 'Administrador', 'Nombre': 'Gerencia SportKing', '2FA_Secret': 'JBSWY3DPEHPK3PXP'},
            {'Usuario': 'cajero1', 'Clave': hash_password('caja1'), 'Rol': 'Vendedor', 'Nombre': 'Cajero Uno', '2FA_Secret': 'K5ZWK4DPEHPK3PXP'},
            {'Usuario': 'cajero2', 'Clave': hash_password('caja2'), 'Rol': 'Vendedor', 'Nombre': 'Cajero Dos', '2FA_Secret': 'M5ZWK4DPEHPK3PXP'}
        ]
        df = pd.DataFrame(usuarios_defecto)
        df.to_csv(ARCHIVO_USUARIOS, index=False)
        return df
    
    df = pd.read_csv(ARCHIVO_USUARIOS)
    if '2FA_Secret' not in df.columns:
        df['2FA_Secret'] = ['JBSWY3DPEHPK3PXP' for _ in range(len(df))]
        df.to_csv(ARCHIVO_USUARIOS, index=False)
    return df

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
    st.session_state.ultimo_ticket_html = ""
    st.session_state.carrito = []
    if 'contador_soporte' not in st.session_state: st.session_state.contador_soporte = 0
    if 'busqueda_manual' not in st.session_state: st.session_state.busqueda_manual = "" 
    if 'login_step' not in st.session_state: st.session_state.login_step = 0
    if 'temp_user_data' not in st.session_state: st.session_state.temp_user_data = None

def enviar_correo_soporte(mensaje, adjunto=None):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("alanbdb64@gmail.com", "dxah wqco wygs bjgk".replace(" ", ""))
        msg = MIMEMultipart()
        msg['Subject'] = f"🚨 Alerta de Sistema (SportKing) - {datetime.now().strftime('%H:%M')}"
        nom_reporta = st.session_state.nombre_usuario if st.session_state.nombre_usuario else "Usuario del Sistema (Sin iniciar sesión)"
        msg.attach(MIMEText(f"Usuario reporta: {nom_reporta}\n\nDetalle de la incidencia:\n{mensaje}", 'plain'))
        
        if adjunto is not None:
            img_data = adjunto.read()
            imagen = MIMEImage(img_data, name=adjunto.name)
            msg.attach(imagen)

        server.sendmail("alanbdb64@gmail.com", "alanbdb64@gmail.com", msg.as_string())
        server.quit()
        return True
    except: return False

def enviar_ticket_correo(correo_destino, ticket_texto):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("alanbdb64@gmail.com", "dxah wqco wygs bjgk".replace(" ", ""))
        msg = MIMEMultipart()
        msg['Subject'] = f"🧾 Ticket de Compra - SportKing"
        msg['From'] = "SportKing Tienda"
        msg['To'] = correo_destino
        body = f"Hola,\n\nGracias por tu preferencia y por caminar con nosotros. Aquí tienes tu comprobante de compra:\n\n{ticket_texto}\n\n¡Vuelve pronto!"
        msg.attach(MIMEText(body, 'plain'))
        server.sendmail("alanbdb64@gmail.com", correo_destino, msg.as_string())
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
        df = df.fillna('')
        return df
    except: return pd.DataFrame(columns=columnas)

def cargar_inventario():
    cols = ['SKU', 'Categoria', 'Genero', 'Modelo', 'Talla', 'Tipo', 'Cantidad', 'Stock_Minimo', 'Costo_Unitario', 'Precio_Venta', 'Proveedor', 'Precio_ML', 'Precio_Amazon', 'Imagen_Base64', 'Fecha_Ingreso']
    df = cargar_csv(ARCHIVO_INVENTARIO, cols)
    if df.empty:
        d_viejo_1 = (datetime.now() - timedelta(days=250)).strftime("%Y-%m-%d") 
        d_viejo_2 = (datetime.now() - timedelta(days=220)).strftime("%Y-%m-%d") 
        d_viejo_3 = (datetime.now() - timedelta(days=280)).strftime("%Y-%m-%d") 
        d_nuevo = datetime.now().strftime("%Y-%m-%d") 
        
        datos = [
            {'SKU': 'NK-AJ1-RED-27', 'Categoria': 'Calzado', 'Genero': 'Hombre', 'Modelo': 'Nike Air Jordan 1 Rojo (Nuevo)', 'Talla': '27', 'Tipo': 'Mayorista', 'Cantidad': 12, 'Stock_Minimo': 3, 'Costo_Unitario': 1200.0, 'Precio_Venta': 2500.0, 'Proveedor': 'Distribuidor Nacional', 'Precio_ML': 2800.0, 'Precio_Amazon': 2750.0, 'Imagen_Base64': '', 'Fecha_Ingreso': d_nuevo},
            {'SKU': 'AD-ULB-BLK-26', 'Categoria': 'Calzado', 'Genero': 'Mujer', 'Modelo': 'Adidas Ultraboost Negro (Viejo)', 'Talla': '26', 'Tipo': 'Mayorista', 'Cantidad': 8, 'Stock_Minimo': 2, 'Costo_Unitario': 1500.0, 'Precio_Venta': 3200.0, 'Proveedor': 'Importación Directa', 'Precio_ML': 3500.0, 'Precio_Amazon': 3400.0, 'Imagen_Base64': '', 'Fecha_Ingreso': d_viejo_1},
            {'SKU': 'PM-SUEDE-BLK-28', 'Categoria': 'Calzado', 'Genero': 'Hombre', 'Modelo': 'Puma Suede Clásico (Viejo)', 'Talla': '28', 'Tipo': 'Retail', 'Cantidad': 5, 'Stock_Minimo': 2, 'Costo_Unitario': 800.0, 'Precio_Venta': 1600.0, 'Proveedor': 'Nacional', 'Precio_ML': 1800.0, 'Precio_Amazon': 1750.0, 'Imagen_Base64': '', 'Fecha_Ingreso': d_viejo_2},
            {'SKU': 'NK-AF1-WHT-24', 'Categoria': 'Calzado', 'Genero': 'Mujer', 'Modelo': 'Nike Air Force 1 Blanco (Viejo)', 'Talla': '24', 'Tipo': 'Mayorista', 'Cantidad': 10, 'Stock_Minimo': 3, 'Costo_Unitario': 1100.0, 'Precio_Venta': 2300.0, 'Proveedor': 'Nacional', 'Precio_ML': 2500.0, 'Precio_Amazon': 2450.0, 'Imagen_Base64': '', 'Fecha_Ingreso': d_viejo_3}
        ]
        df = pd.DataFrame(datos)
        df.to_csv(ARCHIVO_INVENTARIO, index=False)
    return df

def cargar_cupones():
    cols = ['Codigo', 'Descuento_Pct', 'Activo']
    df = cargar_csv(ARCHIVO_CUPONES, cols)
    if df.empty:
        df = pd.DataFrame([{'Codigo': 'BIENVENIDA10', 'Descuento_Pct': 10.0, 'Activo': 'Si'}])
        df.to_csv(ARCHIVO_CUPONES, index=False)
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

def registrar_historial(accion, sku, modelo, cant, precio=0, costo=0, notas="", metodo_pago="Efectivo", descuento=0.0):
    nuevo = {
        'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Usuario': st.session_state.nombre_usuario,
        'Accion': accion, 'SKU': sku, 'Modelo': modelo, 'Cantidad': cant,
        'Monto_Venta': float(precio)*int(cant) if "VENTA" in accion else 0,
        'Costo_Venta': float(costo)*int(cant) if "VENTA" in accion else 0,
        'Monto_Gasto': float(costo)*int(cant) if "ALTA" in accion or "ENTRADA" in accion else 0,
        'Descuento': float(descuento),
        'Notas': notas, 'Metodo_Pago': metodo_pago 
    }
    df_h = pd.DataFrame([nuevo])
    try: df_h.to_csv(ARCHIVO_HISTORIAL, mode='a', header=not os.path.exists(ARCHIVO_HISTORIAL), index=False); st.cache_data.clear()
    except: pass

def generar_ticket(carrito_items, total, user, metodo_pago="Efectivo", pago_cliente=0.0, cambio=0.0, desc_global=0.0):
    pago_str = ""
    if desc_global > 0:
        pago_str += f"\n DESCUENTO CUPON: -${desc_global:,.2f}"
    if metodo_pago == "Efectivo":
        pago_str += f"\n EFECTIVO RECIBIDO: ${pago_cliente:,.2f}\n CAMBIO ENTREGADO: ${cambio:,.2f}\n----------------------------------------"
        
    items_str = ""
    items_html = ""
    for item in carrito_items:
        desc_str = f" (-${item.get('Descuento_Unitario', 0.0):.2f})" if item.get('Descuento_Unitario', 0.0) > 0 else ""
        items_str += f" {str(item['Cantidad']).center(4)} | {item['Modelo'][:19]:<19} | ${item['Subtotal']:,.2f}\n"
        items_str += f" SKU: {item['SKU']}{desc_str}\n"
        
        desc_html = f"<br><small style='color: #8e0e0e;'>Ahorro manual: -${item.get('Descuento_Unitario', 0.0):,.2f}/ud</small>" if item.get('Descuento_Unitario', 0.0) > 0 else ""
        items_html += f"<tr><td style='padding: 5px 0; border-bottom: 1px dashed #ccc;'>{item['Cantidad']}x</td><td style='padding: 5px 0; border-bottom: 1px dashed #ccc;'>{item['Modelo']}<br><small style='color: #666;'>SKU: {item['SKU']}</small>{desc_html}</td><td style='text-align: right; padding: 5px 0; border-bottom: 1px dashed #ccc;'>${item['Subtotal']:,.2f}</td></tr>"

    pago_html = ""
    if desc_global > 0:
        pago_html += f"<tr><td colspan='2'>Cupón Descuento:</td><td style='text-align: right; color: red;'>-${desc_global:,.2f}</td></tr>"
    if metodo_pago == "Efectivo":
        pago_html += f"<tr><td>Efectivo Recibido:</td><td colspan='2' style='text-align: right;'>${pago_cliente:,.2f}</td></tr><tr><td>Cambio:</td><td colspan='2' style='text-align: right;'>${cambio:,.2f}</td></tr>"
        
    ticket_txt = f"""
========================================
         SPORTKING - SUCURSAL
========================================
 Fecha:   {datetime.now().strftime("%d/%m/%Y %H:%M")}
 Cajero:  {user}
 Pago:    {metodo_pago}
----------------------------------------
 CANT | DESCRIPCION             | IMPORTE
----------------------------------------
{items_str}----------------------------------------
            TOTAL A PAGAR: ${total:,.2f}{pago_str}
========================================
         ¡GRACIAS POR SU COMPRA!
       Conserve su ticket para 
        cualquier aclaración.
========================================
    """

    ticket_html = f"""
    <html><head><style>
        body {{ font-family: 'Courier New', Courier, monospace; width: 300px; margin: auto; padding: 20px; color: #000; background: #fff; }}
        h2 {{ text-align: center; font-size: 18px; margin-bottom: 5px; }}
        p {{ font-size: 12px; margin: 2px 0; }}
        .center {{ text-align: center; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 10px; margin-bottom: 10px; }}
        th {{ border-bottom: 1px solid #000; text-align: left; padding-bottom: 5px; }}
        .total {{ font-weight: bold; font-size: 14px; margin-top: 10px; text-align: right; border-top: 1px solid #000; padding-top: 5px; }}
    </style></head><body>
        <h2>SPORTKING</h2>
        <p class="center">SUCURSAL PRINCIPAL</p>
        <p>-----------------------------------</p>
        <p>Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        <p>Cajero: {user}</p>
        <p>Pago: {metodo_pago}</p>
        <p>-----------------------------------</p>
        <table>
            <thead><tr><th>Cant</th><th>Descripción</th><th style="text-align:right;">Importe</th></tr></thead>
            <tbody>{items_html}</tbody>
        </table>
        <div class="total">TOTAL FINAL: ${total:,.2f}</div>
        <table style="margin-top: 5px; border-top: none;"><tbody>{pago_html}</tbody></table>
        <p>-----------------------------------</p>
        <p class="center" style="margin-top: 10px;">¡GRACIAS POR SU COMPRA!</p>
        <p class="center" style="font-size: 10px; color: #666;">Conserve este comprobante para aclaraciones.</p>
        <script>window.onload = function() {{ window.print(); }}</script>
    </body></html>
    """
    return ticket_txt, ticket_html

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
    if 'Metodo_Pago' not in df.columns: df['Metodo_Pago'] = "Efectivo"
    if 'Descuento' not in df.columns: df['Descuento'] = 0.0
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
                <h1 style='text-align: center; margin-bottom: 0;'>👟 SPORTKING</h1>
                <p style='text-align: center; opacity: 0.8; font-weight: 600; color: #B71C1C;'>Sport & Punto de Venta</p>
                <hr style='border-color: rgba(255, 23, 68, 0.15);'>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.session_state.login_step == 0:
            with st.form("login"):
                u = st.text_input("Identificador de Usuario", placeholder="Ingrese su usuario")
                p = st.text_input("Contraseña", type="password", placeholder="••••••••")
                if st.form_submit_button("SIGUIENTE"):
                    val = verificar_login(u, p)
                    if val is not None:
                        # --- CÓDIGO ORIGINAL COMENTADO (2FA) ---
                        # st.session_state.temp_user_data = val
                        # st.session_state.login_step = 1
                        # st.rerun()

                        # --- BYPASS ACTIVO: ENTRADA DIRECTA ---
                        st.session_state.sesion_iniciada = True
                        st.session_state.rol_usuario = val['Rol']
                        st.session_state.nombre_usuario = val['Nombre']
                        st.session_state.usuario_id = val['Usuario']
                        st.rerun()
                    else: 
                        st.error("Autenticación fallida. Verifique sus credenciales.")
            
            with st.expander("¿Olvidaste tu contraseña?"):
                st.write("Se enviará una alerta urgente de restablecimiento al administrador del sistema.")
                u_recup = st.text_input("Tu Usuario de acceso:", key="user_recup")
                if st.button("Solicitar nueva contraseña"):
                    if u_recup:
                        enviar_correo_soporte(f"El empleado con usuario '{u_recup}' ha olvidado su contraseña y solicita un restablecimiento. Por favor, genere una clave temporal en el sistema y contáctelo a la brevedad.")
                        st.success("Solicitud enviada exitosamente. El administrador te contactará pronto.")
                    else:
                        st.warning("Ingresa tu usuario primero para buscarte en el sistema.")

        elif st.session_state.login_step == 1:
            # --- CÓDIGO ORIGINAL COMENTADO (2FA) ---
            user_val = st.session_state.temp_user_data
            st.info("🔐 Autenticación en dos pasos requerida")
            st.caption(f"Si es tu primera vez iniciando sesión, vincula esta clave secreta en **Microsoft Authenticator**: `{user_val['2FA_Secret']}`")
            
            with st.form("2fa_form"):
                codigo_2fa = st.text_input("Ingresa el código de Microsoft Authenticator (6 dígitos):", placeholder="123456")
                if st.form_submit_button("VERIFICAR E INICIAR SESIÓN"):
                    # totp = pyotp.TOTP(user_val['2FA_Secret'])
                    # if totp.verify(codigo_2fa):
                    st.session_state.sesion_iniciada = True
                    st.session_state.rol_usuario = user_val['Rol']
                    st.session_state.nombre_usuario = user_val['Nombre']
                    st.session_state.usuario_id = user_val['Usuario']
                    st.session_state.login_step = 0
                    st.session_state.temp_user_data = None
                    st.rerun()
                    # else:
                    #     st.error("Código incorrecto o expirado. Intente de nuevo.")
            
            if st.button("Volver atrás"):
                st.session_state.login_step = 0
                st.session_state.temp_user_data = None
                st.rerun()

else:
    df_inv = cargar_inventario()
    df_ped = cargar_csv(ARCHIVO_PEDIDOS, ['ID_Pedido','Fecha','SKU','Modelo','Cantidad','Plataforma','Estado'])
    df_crm = cargar_csv(ARCHIVO_CRM, ['Tipo', 'Nombre', 'Contacto', 'Mensaje_Nota', 'Fecha'])
    
    if df_crm.empty:
        df_crm = pd.DataFrame([{'Tipo': 'Proveedor', 'Nombre': 'Alan (Soporte Técnico)', 'Contacto': '5576562718 / alanbdb64@gmail.com', 'Mensaje_Nota': 'Contacto principal del sistema.', 'Fecha': datetime.now().strftime("%Y-%m-%d")}])
        guardar_df(df_crm, ARCHIVO_CRM)
    
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
                gan = v - (c + e) - (v * 0.15) 
                if gan > 0: st.success(f"Utilidad Proyectada: ${gan:,.2f}")
                else: st.error(f"Pérdida Proyectada: ${gan:,.2f}")

        with st.expander("💵 Arqueo de Caja"):
            raw, _, df_full = calc_stats()
            esperado = 0.0
            if df_full is not None and not df_full.empty:
                hoy = datetime.now().date()
                mask = (df_full['Fecha_Dt'].dt.date == hoy) & (df_full['Accion'].str.contains('VENTA')) & (df_full['Usuario'] == st.session_state.nombre_usuario)
                ventas_hoy = df_full[mask]
                
                efectivo = ventas_hoy[ventas_hoy['Metodo_Pago'] == 'Efectivo']['Monto_Venta'].sum()
                tarjeta = ventas_hoy[ventas_hoy['Metodo_Pago'] == 'Tarjeta']['Monto_Venta'].sum()
                transf = ventas_hoy[ventas_hoy['Metodo_Pago'] == 'Transferencia']['Monto_Venta'].sum()
                esperado = efectivo 
                
                st.write(f"💵 Efectivo en Sistema: **${efectivo:,.2f}**")
                st.write(f"💳 Tarjetas: ${tarjeta:,.2f}")
                st.write(f"🏦 Transferencias: ${transf:,.2f}")
                st.markdown(f"**Total General Registrado:** ${(efectivo+tarjeta+transf):,.2f}")
            else:
                st.write("Sin ventas hoy.")

            real = st.number_input("Efectivo Físico en Caja:", 0.0)
            if st.button("Realizar Arqueo"):
                diff = real - esperado
                if diff == 0: st.success("✅ Cuadre de caja correcto.")
                else: st.warning(f"Diferencia en EFECTIVO detectada: ${diff:,.2f}")

        if st.session_state.rol_usuario == "Administrador":
            with st.expander("👤 Gestión de Usuarios (Accesos)", expanded=False):
                st.write("Restablece contraseñas de vendedores u otros administradores.")
                df_usrs = cargar_usuarios()
                with st.form("reset_pass_form"):
                    usr_sel = st.selectbox("Seleccione un usuario", df_usrs['Usuario'].tolist())
                    new_pw = st.text_input("Nueva contraseña", type="password")
                    if st.form_submit_button("Actualizar Contraseña"):
                        if new_pw.strip():
                            idx = df_usrs[df_usrs['Usuario'] == usr_sel].index[0]
                            df_usrs.at[idx, 'Clave'] = hash_password(new_pw)
                            df_usrs.to_csv(ARCHIVO_USUARIOS, index=False)
                            st.success(f"Clave actualizada para {usr_sel}.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("La contraseña no puede estar vacía.")

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
                        registrar_historial("VENTA_AUTO", n['SKU'], n['Modelo'], n['Cantidad'], 0, 0, "Orden B2C Generada", "Transferencia")
                    guardar_df(df_inv, ARCHIVO_INVENTARIO)
                    guardar_df(df_ped, ARCHIVO_PEDIDOS)
                    st.success(f"Se procesaron {len(news)} órdenes nuevas.")
                    time.sleep(1)
                    st.rerun()
                else: st.info("Inventario y órdenes sincronizadas. Sin novedades.")

        with st.expander("🛠️ Reportar Incidencia", expanded=False):
            key_din = f"txt_soporte_{st.session_state.contador_soporte}"
            msg_err = st.text_area("Describa el error del sistema:", key=key_din)
            archivo_adjunto = st.file_uploader("Adjuntar captura de pantalla (Opcional)", type=['png', 'jpg', 'jpeg'], key=f"adjunto_{st.session_state.contador_soporte}")
            
            if st.button("Enviar Ticket de Soporte"):
                if msg_err:
                    with st.spinner("Enviando reporte..."):
                        if enviar_correo_soporte(msg_err, archivo_adjunto):
                            st.success("Ticket enviado al administrador.")
                            st.session_state.contador_soporte += 1
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Hubo un error al enviar el reporte. Verifique la conexión.")
                else:
                    st.warning("Debe describir el error para poder enviarlo.")

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
    st.markdown("<h2 style='margin-bottom: 0;'>👟 Panel de Control - SportKing</h2>", unsafe_allow_html=True)
    
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

    tabs = st.tabs(["📦 ÓRDENES E-COMMERCE", "🛒 Vender o Salida de Mercancía", "👟 INVENTARIO", "📝 INGRESAR O EDITAR CATÁLOGO", "📊 REPORTES FINANCIEROS", "📞 CRM & MENSAJES"]) if st.session_state.rol_usuario == "Administrador" else st.tabs(["📦 ÓRDENES", "🛒 TPV", "👟 INVENTARIO", "📊 MIS VENTAS", "📞 CRM & MENSAJES"])
    t_ped, t_pos, t_inv = tabs[0], tabs[1], tabs[2]
    
    if st.session_state.rol_usuario == "Administrador":
        t_adm, t_rep, t_crm = tabs[3], tabs[4], tabs[5]
    else:
        t_adm, t_rep, t_crm = None, tabs[3], tabs[4]

    # 1. ÓRDENES (E-COMMERCE Y MANUALES)
    with t_ped:
        st.markdown("### 🛒 Órdenes E-Commerce (Automáticas)")
        p = df_ped[df_ped['Estado']=='Pendiente']
        if p.empty: st.success("No hay órdenes pendientes de despacho.")
        else:
            for i, r in p.iterrows():
                with st.container():
                    c_img, c2, c3, c4 = st.columns([0.5, 3, 2, 1.5])
                    
                    img_b64 = ""
                    f_inv = df_inv[df_inv['SKU'] == r['SKU']]
                    if not f_inv.empty: img_b64 = f_inv.iloc[0].get('Imagen_Base64', '')
                    
                    if img_b64:
                        c_img.markdown(f'<img src="data:image/jpeg;base64,{img_b64}" style="width:50px; border-radius:5px;">', unsafe_allow_html=True)
                    else:
                        icon = "👕" if "Ropa" in r['Modelo'] or "Playera" in r['Modelo'] else "👟"
                        c_img.markdown(f"<h4>{icon}</h4>", unsafe_allow_html=True)
                        
                    c2.markdown(f"**{r['Modelo']}**")
                    c2.caption(f"SKU: {r['SKU']} | Unidades: **{r['Cantidad']}**")
                    c3.write(f"Ref. Externa: {r['ID_Pedido']}")
                    if c4.button("Confirmar Despacho", key=r['ID_Pedido']):
                        df_ped.loc[df_ped['ID_Pedido']==r['ID_Pedido'], 'Estado']='Enviado'
                        guardar_df(df_ped, ARCHIVO_PEDIDOS)
                        st.rerun()
                    st.divider()
        
        st.markdown("---")
        st.markdown("### 📝 Gestión de Pedidos Manuales")
        df_pm = cargar_csv(ARCHIVO_PEDIDOS_MANUALES, ['ID', 'Fecha', 'Cliente', 'Detalle', 'Estado'])
        
        c_add_pm, c_list_pm = st.columns([1, 2])
        
        with c_add_pm:
            with st.form("form_pedido_manual", clear_on_submit=True):
                st.markdown("##### Nuevo Pedido Manual")
                cliente_pm = st.text_input("Nombre del Cliente")
                detalle_pm = st.text_area("Detalle del Pedido (Modelos, Tallas, Notas)")
                if st.form_submit_button("Registrar Pedido"):
                    if cliente_pm and detalle_pm:
                        nuevo_pm = {
                            'ID': f"PM-{int(time.time())}",
                            'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M"),
                            'Cliente': cliente_pm,
                            'Detalle': detalle_pm,
                            'Estado': 'Pendiente'
                        }
                        df_pm = pd.concat([df_pm, pd.DataFrame([nuevo_pm])], ignore_index=True)
                        guardar_df(df_pm, ARCHIVO_PEDIDOS_MANUALES)
                        st.success("Pedido manual registrado exitosamente.")
                        time.sleep(0.5); st.rerun()
                    else:
                        st.error("Llene todos los campos para registrar el pedido.")
        
        with c_list_pm:
            st.markdown("##### Checklist de Pedidos Pendientes")
            pendientes_pm = df_pm[df_pm['Estado'] == 'Pendiente']
            if pendientes_pm.empty:
                st.info("¡Excelente! No hay pedidos manuales pendientes.")
            else:
                for idx_pm, row_pm in pendientes_pm.iterrows():
                    with st.container():
                        col_text_pm, col_btn_pm = st.columns([4, 1])
                        col_text_pm.markdown(f"**{row_pm['Cliente']}** - {row_pm['Fecha']}<br><small>{row_pm['Detalle']}</small>", unsafe_allow_html=True)
                        if col_btn_pm.button("✅ Entregado", key=f"btn_pm_{row_pm['ID']}"):
                            df_pm.loc[df_pm['ID'] == row_pm['ID'], 'Estado'] = 'Entregado'
                            guardar_df(df_pm, ARCHIVO_PEDIDOS_MANUALES)
                            st.rerun()
                        st.divider()
            
            with st.expander("📊 Ver Reporte Histórico de Pedidos Manuales"):
                st.dataframe(df_pm, hide_index=True, use_container_width=True)

    # 2. TPV (PUNTO DE VENTA)
    with t_pos:
        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.markdown("#### Búsqueda de Artículo")
            with st.form("form_buscar_tpv", clear_on_submit=False):
                col_search, col_btn = st.columns([4, 1])
                scan_input = col_search.text_input("Búsqueda de Artículo:", placeholder="Escanee código de barras o ingrese SKU/descripción...", label_visibility="collapsed")
                submit_search = col_btn.form_submit_button("🔍 Buscar")
            
            scan = scan_input if submit_search else st.session_state.busqueda_manual
            st.session_state.busqueda_manual = scan_input 
            
            sel = None
            if scan:
                scan = sanitizar_texto(scan)
                f = df_inv[df_inv['SKU'].astype(str).str.upper() == scan.upper()]
                if not f.empty: sel = f.iloc[0]
                else: 
                    fn = df_inv[df_inv['Modelo'].str.contains(scan, case=False)]
                    if not fn.empty: sel = fn.iloc[0]
            
            if sel is None and not df_inv.empty:
                op = df_inv[df_inv['Cantidad']>0].apply(lambda x: f"{x['Modelo']} (Talla: {x['Talla'] if str(x['Talla']) != '' else 'Única'}) | {x['SKU']}", axis=1)
                s = st.selectbox("Selección desde Catálogo:", op, index=None, placeholder="Elija un producto...", label_visibility="collapsed")
                if s: sel = df_inv[df_inv['SKU'] == s.split(" | ")[1]].iloc[0]
            
            if sel is not None:
                idx = df_inv[df_inv['SKU']==sel['SKU']].index[0]
                
                col_info1, col_info2 = st.columns([1, 4])
                img_str = sel.get('Imagen_Base64', '')
                if img_str:
                    col_info1.markdown(f'<img src="data:image/jpeg;base64,{img_str}" style="width:100%; border-radius:8px;">', unsafe_allow_html=True)
                else:
                    col_info1.markdown("<h1>👟</h1>", unsafe_allow_html=True)
                
                with col_info2:
                    qty_in_cart = sum(item['Cantidad'] for item in st.session_state.carrito if item['SKU'] == sel['SKU'])
                    stock_real = int(df_inv.at[idx, 'Cantidad']) - qty_in_cart
                    stock_min = int(df_inv.at[idx, 'Stock_Minimo'])
                    
                    fecha_ingreso_str = sel.get('Fecha_Ingreso', '')
                    if pd.isna(fecha_ingreso_str) or fecha_ingreso_str == '':
                        fecha_ingreso_str = datetime.now().strftime("%Y-%m-%d")
                    fecha_ing = pd.to_datetime(fecha_ingreso_str).date()
                    dias_antiguedad = (datetime.now().date() - fecha_ing).days
                    
                    if dias_antiguedad > 210:
                        st.error(f"🚨 **PRODUCTO REZAGADO (>7 meses).** Sugerencia: Aplicar descuento de liquidación.")
                    
                    if stock_real <= stock_min:
                        st.warning(f"⚠️ **{sel['Modelo']}** | Disponible: {stock_real} (Nivel Bajo)")
                    else:
                        st.info(f"**{sel['Modelo']}** | Disponible: {stock_real} unidades")
                
                if stock_real > 0:
                    cq, cp = st.columns(2)
                    q = cq.number_input("Cantidad a añadir", 1, stock_real, 1)
                    
                    precio_final = float(sel['Precio_Venta'])
                    descuento_unitario = 0.0
                    
                    usar_descuento = st.checkbox("🔑 Autorizar Descuento Especial Manual (Cualquier Artículo)")
                    if usar_descuento:
                        col_desc1, col_desc2 = st.columns(2)
                        precio_especial = col_desc1.number_input("Nuevo Precio Final ($)", min_value=0.0, value=float(sel['Precio_Venta']), max_value=float(sel['Precio_Venta']), step=50.0)
                        codigo_auth = col_desc2.text_input("Código de Autorización (2FA de Admin)", type="password")

                    tot_item = precio_final * q if not usar_descuento else precio_especial * q
                    cp.metric("Subtotal Artículo", f"${tot_item:,.2f}")
                    
                    if st.button("🛒 AÑADIR AL CARRITO", use_container_width=True):
                        if usar_descuento and precio_especial < sel['Precio_Venta']:
                            df_usrs = cargar_usuarios()
                            admin_secrets = df_usrs[df_usrs['Rol'] == 'Administrador']['2FA_Secret'].tolist()
                            
                            # --- VALIDACIÓN 2FA COMENTADA (BYPASS TEMPORAL) ---
                            # autorizado = any(pyotp.TOTP(secret).verify(codigo_auth) for secret in admin_secrets)
                            autorizado = True # Bypass forzado para que siempre autorice
                            
                            if not autorizado:
                                st.error("Código de autorización 2FA inválido. Solicite el código a un Administrador.")
                                st.stop()
                            else:
                                precio_final = precio_especial
                                descuento_unitario = float(sel['Precio_Venta']) - precio_especial

                        st.session_state.carrito.append({
                            'SKU': sel['SKU'],
                            'Modelo': sel['Modelo'],
                            'Cantidad': q,
                            'Precio_Venta': precio_final,
                            'Costo_Unitario': sel['Costo_Unitario'],
                            'Subtotal': tot_item,
                            'Descuento_Unitario': descuento_unitario
                        })
                        st.session_state.busqueda_manual = "" 
                        st.success(f"{q}x {sel['Modelo']} añadido al carrito.")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.error("Artículo agotado o ya agregaste todo el stock al carrito.")
                    st.button("🛒 AÑADIR AL CARRITO", disabled=True, key="btn_agotado")

        with c2:
            st.markdown("#### Carrito de Compras")
            if not st.session_state.carrito:
                st.info("El carrito está vacío. Agregue artículos para cobrar.")
                
                if st.session_state.ultimo_ticket:
                    with st.expander("🧾 Ver / Imprimir Última Transacción", expanded=True):
                        st.code(st.session_state.ultimo_ticket, language="text")
                        
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            st.download_button(
                                label="📥 Descargar (TXT)",
                                data=st.session_state.ultimo_ticket,
                                file_name=f"Ticket_SportKing_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        with col_d2:
                            b64_html = base64.b64encode(st.session_state.ultimo_ticket_html.encode("utf-8")).decode("utf-8")
                            components.html(
                                f"""
                                <button onclick="var w=window.open('','_blank','width=400,height=600');w.document.write(atob('{b64_html}'));w.document.close();" 
                                style="width: 100%; background-color: #B71C1C; color: white; padding: 0.5rem; border-radius: 6px; border: none; font-weight: 600; cursor: pointer; font-family: sans-serif; font-size: 1rem;">
                                    🖨️ Imprimir / PDF
                                </button>
                                """,
                                height=45
                            )
                        
                        st.markdown("#### 📤 Enviar Ticket al Cliente")
                        send_method = st.radio("Método de envío", ["WhatsApp", "Correo Electrónico"], horizontal=True, label_visibility="collapsed")
                        
                        if send_method == "WhatsApp":
                            num_wa = st.text_input("Número de WhatsApp (10 dígitos)", placeholder="Ej: 5512345678")
                            if num_wa and len(num_wa) >= 10:
                                ticket_encoded = urllib.parse.quote(st.session_state.ultimo_ticket)
                                wa_link = f"https://wa.me/52{num_wa}?text={ticket_encoded}"
                                st.link_button("🟢 Enviar por WhatsApp", wa_link, use_container_width=True)
                        
                        elif send_method == "Correo Electrónico":
                            correo_envio = st.text_input("Correo electrónico del cliente", placeholder="cliente@correo.com")
                            if st.button("📧 Enviar por Correo"):
                                if "@" in correo_envio and "." in correo_envio:
                                    with st.spinner("Enviando correo..."):
                                        if enviar_ticket_correo(correo_envio, st.session_state.ultimo_ticket):
                                            st.success("Ticket enviado al correo del cliente.")
                                        else:
                                            st.error("Error al enviar el correo. Verifique la conexión.")
                                else:
                                    st.warning("Ingrese un correo válido.")
            else:
                df_carrito = pd.DataFrame(st.session_state.carrito)
                st.dataframe(
                    df_carrito[['Modelo', 'Cantidad', 'Subtotal']], 
                    use_container_width=True,
                    column_config={"Subtotal": st.column_config.NumberColumn(format="$%.2f")}
                )
                
                if st.button("🗑️ Vaciar Carrito"):
                    st.session_state.carrito = []
                    st.rerun()
                    
                tot_carrito = sum(item['Subtotal'] for item in st.session_state.carrito)
                
                # --- SISTEMA DE CUPONES ---
                df_cupones = cargar_cupones()
                cupon_input = st.text_input("🎟️ Código de Cupón (Opcional):", placeholder="Ingrese código aquí").upper()
                descuento_cupon_pct = 0.0
                if cupon_input:
                    match_cupon = df_cupones[(df_cupones['Codigo'] == cupon_input) & (df_cupones['Activo'] == 'Si')]
                    if not match_cupon.empty:
                        descuento_cupon_pct = float(match_cupon.iloc[0]['Descuento_Pct'])
                        st.success(f"Cupón aplicado: {descuento_cupon_pct}% de descuento en el total.")
                    else:
                        st.error("Cupón inválido o inactivo.")
                
                monto_descuento_global = 0.0
                if descuento_cupon_pct > 0:
                    monto_descuento_global = tot_carrito * (descuento_cupon_pct / 100)
                    tot_carrito = tot_carrito - monto_descuento_global
                    st.markdown(f"### Total (con descuento): ${tot_carrito:,.2f}")
                else:
                    st.markdown(f"### Total: ${tot_carrito:,.2f}")
                
                metodo = st.selectbox("Método de Pago", ["Efectivo", "Tarjeta", "Transferencia"])
                
                pago_cliente = tot_carrito
                cambio = 0.0
                if metodo == "Efectivo":
                    pago_cliente = st.number_input("Efectivo Recibido ($)", min_value=0.0, value=float(tot_carrito), step=50.0)
                    cambio = pago_cliente - tot_carrito
                    if cambio >= 0:
                        st.success(f"💵 Cambio a entregar: **${cambio:,.2f}**")
                    else:
                        st.error(f"Faltan **${abs(cambio):,.2f}** para completar el pago.")

                disable_btn = True if (metodo == "Efectivo" and pago_cliente < tot_carrito) else False
                
                if st.button("✅ PROCESAR TRANSACCIÓN MULTIPLE", type="primary", use_container_width=True, disabled=disable_btn):
                    for item in st.session_state.carrito:
                        idx_inv = df_inv[df_inv['SKU']==item['SKU']].index[0]
                        df_inv.at[idx_inv, 'Cantidad'] -= item['Cantidad']
                        
                        desc_extra = item['Subtotal'] * (descuento_cupon_pct / 100)
                        desc_total = (item.get('Descuento_Unitario', 0.0) * item['Cantidad']) + desc_extra
                        
                        registrar_historial("VENTA", item['SKU'], item['Modelo'], item['Cantidad'], item['Precio_Venta'], item['Costo_Unitario'], "Venta Múltiple TPV", metodo, desc_total)
                        
                    guardar_df(df_inv, ARCHIVO_INVENTARIO)
                    txt_ticket, html_ticket = generar_ticket(st.session_state.carrito, tot_carrito, st.session_state.nombre_usuario, metodo, pago_cliente, cambio, monto_descuento_global)
                    st.session_state.ultimo_ticket = txt_ticket
                    st.session_state.ultimo_ticket_html = html_ticket
                    st.session_state.carrito = [] 
                    st.session_state.busqueda_manual = "" 
                    st.success("Transacción registrada correctamente.")
                    time.sleep(0.5)
                    st.rerun()

            st.markdown("---")
            if st.session_state.rol_usuario == "Administrador":
                with st.expander("🎫 GESTIÓN DE CUPONES DE DESCUENTO (Configuración)", expanded=True):
                    st.markdown("Administra los códigos promocionales para que los cajeros los apliquen en el carrito.")
                    df_cup = cargar_cupones()
                    
                    c_crear, c_eliminar = st.columns(2)
                    
                    with c_crear:
                        with st.form("form_cupones", clear_on_submit=True):
                            st.markdown("##### Crear Nuevo Cupón")
                            n_cup = st.text_input("Código del Cupón (Ej. VERANO20)").upper()
                            n_pct = st.number_input("Descuento (%)", min_value=1.0, max_value=100.0, value=10.0)
                            if st.form_submit_button("Crear Cupón"):
                                if n_cup:
                                    if not df_cup.empty and n_cup in df_cup['Codigo'].values:
                                        st.error("Ese código de cupón ya existe.")
                                    else:
                                        nuevo_cup = {'Codigo': n_cup, 'Descuento_Pct': n_pct, 'Activo': 'Si'}
                                        df_cup = pd.concat([df_cup, pd.DataFrame([nuevo_cup])], ignore_index=True)
                                        guardar_df(df_cup, ARCHIVO_CUPONES)
                                        st.success(f"Cupón {n_cup} creado exitosamente.")
                                        time.sleep(1); st.rerun()
                    
                    with c_eliminar:
                        if not df_cup.empty:
                            st.markdown("##### Gestionar Cupón")
                            cupon_sel = st.selectbox("Seleccione el cupón a gestionar:", df_cup['Codigo'].tolist(), key="sel_cup")
                            
                            estado_actual = df_cup.loc[df_cup['Codigo'] == cupon_sel, 'Activo'].iloc[0]
                            
                            c_btn1, c_btn2 = st.columns(2)
                            with c_btn1:
                                if estado_actual == 'Si':
                                    if st.button("⏸️ Pausar", use_container_width=True):
                                        df_cup.loc[df_cup['Codigo'] == cupon_sel, 'Activo'] = 'No'
                                        guardar_df(df_cup, ARCHIVO_CUPONES)
                                        st.success(f"Cupón {cupon_sel} pausado.")
                                        time.sleep(0.5); st.rerun()
                                else:
                                    if st.button("▶️ Reactivar", use_container_width=True):
                                        df_cup.loc[df_cup['Codigo'] == cupon_sel, 'Activo'] = 'Si'
                                        guardar_df(df_cup, ARCHIVO_CUPONES)
                                        st.success(f"Cupón {cupon_sel} reactivado.")
                                        time.sleep(0.5); st.rerun()
                                        
                            with c_btn2:
                                if st.button("🗑️ Eliminar", use_container_width=True):
                                    df_cup = df_cup[df_cup['Codigo'] != cupon_sel]
                                    guardar_df(df_cup, ARCHIVO_CUPONES)
                                    st.success(f"Cupón {cupon_sel} eliminado.")
                                    time.sleep(0.5); st.rerun()
                        else:
                            st.info("No hay cupones registrados.")

                    if not df_cup.empty:
                        st.markdown("##### Lista de Cupones Registrados")
                        st.dataframe(df_cup, hide_index=True, use_container_width=True)

    # 3. INVENTARIO
    with t_inv:
        st.markdown("#### Base de Datos de Artículos")
        ver_bajo = st.checkbox("Mostrar únicamente artículos con alerta de stock") 
        
        df_show = df_inv.copy()
        if ver_bajo:
            df_show = df_show[df_show['Cantidad'] <= df_show['Stock_Minimo']]
            
        st.dataframe(
            df_show[['SKU', 'Categoria', 'Genero', 'Modelo', 'Talla', 'Cantidad', 'Costo_Unitario', 'Precio_Venta']], 
            use_container_width=True,
            column_config={
                "Cantidad": st.column_config.ProgressColumn("Unidades Disponibles", format="%d", min_value=0, max_value=int(df_inv['Cantidad'].max() if not df_inv.empty else 100)),
                "Costo_Unitario": st.column_config.NumberColumn("Costo Base", format="$%.2f"),
                "Precio_Venta": st.column_config.NumberColumn("Precio Público", format="$%.2f")
            }
        )
        
        csv_inv = df_show.drop(columns=['Imagen_Base64']).to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Exportar Inventario (.csv)", data=csv_inv, file_name=f'inventario_{datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv')

        st.divider()
        c_redes, c_remate = st.columns(2)
        with c_redes:
            st.markdown("#### 📱 Promover por Redes")
            s_redes = st.selectbox("Generar post para:", df_inv[df_inv['Cantidad']>0]['Modelo'].unique(), key="s_redes")
            if s_redes:
                r = df_inv[df_inv['Modelo']==s_redes].iloc[0]
                talla_str = r.get('Talla', 'Única')
                gen_str = r.get('Genero', 'Unisex')
                txt = f"🔥 ¡NUEVO INGRESO! 🔥\n👟 {r['Modelo']}\n📏 Talla: {talla_str} ({gen_str})\n💰 A solo: ${float(r['Precio_Venta']):,.2f}\n\n📦 Entrega inmediata. ¡Mándanos DM!"
                
                c_img_r, c_txt_r = st.columns([1,3])
                img_str = r.get('Imagen_Base64', '')
                if img_str: c_img_r.markdown(f'<img src="data:image/jpeg;base64,{img_str}" style="width:100%; border-radius:8px;">', unsafe_allow_html=True)
                c_txt_r.code(txt, language="text")

        with c_remate:
            if st.session_state.rol_usuario == "Administrador":
                st.markdown("#### 🚨 Alerta de Remates (Alto Stock)")
                remates = df_inv[(df_inv['Cantidad'] >= 5)]
                if not remates.empty:
                    for _, rem in remates.iterrows():
                        st.write(f"🔻 **{rem['Modelo']}** (Quedan {rem['Cantidad']}) - Sugerido: **${float(rem['Costo_Unitario'])*1.1:,.2f}**")
                else: st.success("Inventario rotando bien. Sin alto stock.")
                
                st.markdown("#### 🧠 Inteligencia: Mercancía Rezagada (>7 meses)")
                
                cinco_meses_atras = pd.Timestamp.now() - pd.DateOffset(months=7)
                df_inv['Fecha_Dt_Ing'] = pd.to_datetime(df_inv['Fecha_Ingreso'], errors='coerce')
                
                rezagados = df_inv[df_inv['Fecha_Dt_Ing'] < cinco_meses_atras]
                
                if not rezagados.empty:
                    st.warning("⚠️ Artículos detectados como rezagados en el sistema:")
                    for _, r in rezagados.iterrows():
                        desc = float(r['Precio_Venta']) * 0.8 
                        margen = desc - float(r['Costo_Unitario'])
                        if margen > 0:
                            st.write(f"📉 **{r['Modelo']}** - 20% Off Sugerido: **${desc:,.2f}** (Aún ganas ${margen:,.2f})")
                        else:
                            st.write(f"📉 **{r['Modelo']}** - Remate: **${float(r['Costo_Unitario'])*1.05:,.2f}** (Costo + 5%)")
                else:
                    st.success("✅ Excelente rotación. Sin mercancía rezagada.")

    # 4. ADMINISTRACIÓN DE CATÁLOGO
    if t_adm:
        with t_adm:
            st.markdown("#### Gestión Profesional de Inventario")
            act = st.radio("Tipo de Operación", ["Registro Nuevo", "Duplicar Registro", "Modificar Datos", "Ajuste de Existencias", "Eliminar Artículo"], horizontal=True)
            d_sku, d_mod, d_qty, d_min, d_cost, d_pv = "", "", 1, 2, 0.0, 0.0
            d_cat, d_link, d_ml, d_amz, d_img = "Calzado", "", 0.0, 0.0, ""
            d_talla, d_gen = "", "Unisex"
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
                d_talla = r.get('Talla', '')
                d_gen = r.get('Genero', 'Unisex')
                d_img = r.get('Imagen_Base64', '')

            if act == "Eliminar Artículo" and idx_e != -1:
                st.warning(f"¿Desea eliminar permanentemente '{d_mod}' (SKU: {d_sku}) del catálogo?")
                if st.button("Confirmar Eliminación", type="primary"):
                    df_inv = df_inv.drop(idx_e).reset_index(drop=True)
                    guardar_df(df_inv, ARCHIVO_INVENTARIO)
                    registrar_historial("BAJA_INV", d_sku, d_mod, d_qty, 0, d_cost, "Eliminación del catálogo", "Ninguno")
                    st.success("Artículo eliminado de la base de datos.")
                    time.sleep(1)
                    st.rerun()
            else:
                st.markdown("##### Especificaciones Técnicas (Tenis/Ropa)")
                c_img_up, c_form_data = st.columns([1, 2])
                
                with c_img_up:
                    if d_img and act != "Registro Nuevo":
                        st.markdown(f'<img src="data:image/jpeg;base64,{d_img}" style="width:100%; border-radius:8px; margin-bottom:10px;">', unsafe_allow_html=True)
                    
                    img_mode = st.radio("Cargar Imagen desde:", ["Archivo", "Cámara"], horizontal=True)
                    img_file = None
                    if img_mode == "Archivo":
                        img_file = st.file_uploader("Sube foto del producto", type=['png', 'jpg', 'jpeg'])
                    else:
                        img_file = st.camera_input("Tomar foto")
                        if img_file:
                            st.success("✅ Foto capturada. Haz clic en 'Aplicar Cambios...' para guardarla.")

                with c_form_data:
                    with st.form("adm", clear_on_submit=(act=="Registro Nuevo")):
                        c1, c2 = st.columns(2)
                        f_sku = c1.text_input("Código de Barras / SKU", d_sku, disabled=(act in ["Modificar Datos", "Ajuste de Existencias"]))
                        f_mod = c2.text_input("Descripción Comercial", d_mod, disabled=(act=="Ajuste de Existencias"))
                        
                        c3, c_talla, c_gen = st.columns(3)
                        f_cat = c3.selectbox("Línea de Producto", ["Calzado", "Ropa", "Accesorios"], index=["Calzado", "Ropa", "Accesorios"].index(d_cat) if d_cat in ["Calzado", "Ropa", "Accesorios"] else 0) 
                        f_talla = c_talla.text_input("Número / Talla", d_talla)
                        f_gen = c_gen.selectbox("Género", ["Hombre", "Mujer", "Unisex", "Niños"], index=["Hombre", "Mujer", "Unisex", "Niños"].index(d_gen) if d_gen in ["Hombre", "Mujer", "Unisex", "Niños"] else 2)
                        
                        c4, c5 = st.columns(2)
                        f_qty = c4.number_input("Unidades Físicas Ingresadas", value=d_qty)
                        f_min = c5.number_input("Punto de Reorden (Stock Mínimo)", value=d_min) 
                        
                        st.markdown("##### Parámetros de Rentabilidad")
                        c6, c7, c8 = st.columns(3)
                        f_cos = c6.number_input("Costo de Adquisición Unitario", value=d_cost)
                        f_pv = c7.number_input("Precio de Venta Sugerido", value=d_pv)
                        f_lnk = c8.text_input("Identificador de Proveedor", d_link)
                        
                        c9, c10 = st.columns(2)
                        f_ml = c9.number_input("Precio Mercado Libre", value=d_ml) 
                        f_amz = c10.number_input("Precio Amazon", value=d_amz) 
                        
                        if st.form_submit_button("Aplicar Cambios en Base de Datos"):
                            if not f_mod or not f_talla: st.error("La descripción y la talla son obligatorias.")
                            else:
                                f_mod = sanitizar_texto(f_mod)
                                f_sku = sanitizar_texto(f_sku)
                                if not f_sku: f_sku = f"TR-{str(uuid.uuid4())[:6].upper()}"
                                
                                final_img = image_to_base64(img_file) if img_file else d_img
                                fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                                
                                new_d = {'SKU': f_sku, 'Categoria': f_cat, 'Genero': f_gen, 'Modelo': f_mod, 'Talla': f_talla, 'Tipo': 'Retail', 'Cantidad': f_qty, 'Stock_Minimo': f_min, 'Costo_Unitario': f_cos, 'Precio_Venta': f_pv, 'Proveedor': f_lnk, 'Precio_ML': f_ml, 'Precio_Amazon': f_amz, 'Imagen_Base64': final_img, 'Fecha_Ingreso': fecha_hoy}
                                
                                if act in ["Modificar Datos", "Ajuste de Existencias"] and idx_e != -1:
                                    diff = f_qty - df_inv.at[idx_e, 'Cantidad']
                                    for k,v in new_d.items(): 
                                        if k != 'Fecha_Ingreso': # No modificar la fecha original
                                            df_inv.at[idx_e, k] = v
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

    # 5. REPORTES FINANCIEROS Y BONOS
    if t_rep:
        with t_rep:
            if st.session_state.rol_usuario == "Administrador":
                st.markdown("#### Análisis Comercial")
                freq = st.radio("Período de Agrupación:", ["Diario", "Mensual"], horizontal=True)
                
                if df_full is not None and not df_full.empty:
                    df_c = df_full.copy()
                    grp = df_c['Fecha_Dt'].dt.date if freq=="Diario" else df_c['Fecha_Dt'].dt.strftime('%Y-%m')
                    
                    st.markdown("### Estado de Resultados")
                    tab = df_c.groupby(grp)[['Monto_Venta', 'Monto_Gasto']].sum()
                    tab.columns = ['Ingresos Brutos', 'Costo de Adquisición/Gastos']
                    tab['Utilidad Operativa'] = tab['Ingresos Brutos'] - tab['Costo de Adquisición/Gastos']
                    st.dataframe(tab.style.format("${:,.2f}"), use_container_width=True)
                    
                    csv = tab.to_csv().encode('utf-8')
                    st.download_button(label="📥 Exportar Reporte (.csv)", data=csv, file_name='reporte_financiero_sk.csv', mime='text/csv')

                    st.divider()
                    st.markdown("### Indicadores de Desempeño")
                    c1, c2 = st.columns(2)
                    imp_pct = c1.number_input("Carga Impositiva (%)", 16.0) / 100
                    com_pct = c2.number_input("Costos Logísticos/TPV (%)", 4.0) / 100
                    
                    vs = df_c[df_c['Accion'].str.contains('VENTA')]
                    if not vs.empty:
                        tot_v = vs['Monto_Venta'].sum()
                        tot_c = vs['Costo_Venta'].sum() 
                        tot_d = vs['Descuento'].sum()
                        bruta = tot_v - tot_c
                        gastos_variables = tot_v * (imp_pct + com_pct)
                        neta = bruta - gastos_variables
                        num_transacciones = len(vs)
                        ticket_promedio = tot_v / num_transacciones if num_transacciones > 0 else 0
                        
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Facturación Total", f"${tot_v:,.2f}")
                        m2.metric("CMV", f"-${tot_c:,.2f}")
                        m3.metric("Descuentos Autorizados", f"-${tot_d:,.2f}")
                        m4.metric("Utilidad Bruta", f"${bruta:,.2f}")
                        
                        m5, m6, m7, _ = st.columns(4)
                        m5.metric("Deducciones", f"-${gastos_variables:,.2f}")
                        m6.metric("Utilidad Neta", f"${neta:,.2f}")
                        m7.metric("Margen Neto (%)", f"{(neta/tot_v)*100:.2f}%" if tot_v > 0 else "0.00%")
                        st.info(f"💡 Se han realizado **{num_transacciones}** ventas. Ticket promedio: **${ticket_promedio:,.2f}**.")
                    
                    st.divider()
                    st.markdown("##### Rendimiento por Asesor y Bonos")
                    if not vs.empty:
                        com = vs.groupby('Usuario').agg({'Monto_Venta': 'sum', 'Descuento': 'sum'}).reset_index()
                        
                        # --- NUEVO: TOP VENDEDOR ---
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
                        
                        st.dataframe(com.style.format({'Monto_Venta': '${:,.2f}', 'Descuento': '${:,.2f}', 'Comisión Base (3%)': '${:,.2f}', 'Bono Extra': '${:,.2f}', 'Premio 1er Lugar': '${:,.2f}', 'Total a Pagar': '${:,.2f}'}), use_container_width=True)
            else:
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
                        tot_d = vs['Descuento'].sum()
                        
                        if st.session_state.nombre_usuario == top_user:
                            st.success("🏆 ¡Felicidades! Actualmente eres el VENDEDOR #1. ¡Mantén el ritmo para llevarte el bono especial!")
                            
                        c_meta1, c_meta2 = st.columns(2)
                        meta = c_meta1.number_input("Mi Meta de Venta para Bono Extra ($):", value=10000.0)
                        bono_pct = c_meta2.number_input("Mi Porcentaje de Bono sobre excedente (%):", value=5.0) / 100
                        
                        comision_base = tot_v * 0.03
                        bono_extra = (tot_v - meta) * bono_pct if tot_v >= meta else 0
                        bono_primer_lugar = 500.0 if st.session_state.nombre_usuario == top_user else 0.0
                        total_pagar = comision_base + bono_extra + bono_primer_lugar
                        
                        st.metric("Mi Facturación Total", f"${tot_v:,.2f}")
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Comisión Base (3%)", f"${comision_base:,.2f}")
                        m2.metric("Bono Extra", f"${bono_extra:,.2f}")
                        m3.metric("Premio 1er Lugar", f"${bono_primer_lugar:,.2f}")
                        m4.metric("Total a Recibir", f"${total_pagar:,.2f}")
                        st.info(f"Has otorgado **${tot_d:,.2f}** en descuentos autorizados.")
                        
                        st.divider()
                        st.markdown("##### Historial de mis ventas")
                        st.dataframe(vs[['Fecha', 'Modelo', 'Cantidad', 'Monto_Venta', 'Descuento', 'Metodo_Pago']], hide_index=True, use_container_width=True)
                    else:
                        st.info("Aún no tienes ventas registradas en el sistema.")

    # 6. CRM Y CENTRO DE ENVÍO
    if t_crm:
        with t_crm:
            crm_tabs = st.tabs(["👥 Directorio de Contactos", "💬 Bandeja de Entrada (Chats)", "⚙️ Configuración APIs (Webhooks)"])
            
            # --- Pestaña 1: Directorio (Lo que ya tenías) ---
            with crm_tabs[0]:
                c_form, c_action = st.columns([1, 1])
                
                with c_form:
                    st.markdown("#### 📖 Guardar Contacto")
                    with st.form("crm_form", clear_on_submit=True):
                        tipo = st.radio("Clasificación:", ["Cliente", "Proveedor"], horizontal=True)
                        nombre = st.text_input("Nombre / Empresa")
                        contacto = st.text_input("Teléfono (Ej. 5576562718) o Correo")
                        nota = st.text_area("Nota o Petición")
                        if st.form_submit_button("Guardar"):
                            if nombre and contacto:
                                new_crm = {'Tipo': tipo, 'Nombre': nombre, 'Contacto': contacto, 'Mensaje_Nota': nota, 'Fecha': datetime.now().strftime("%Y-%m-%d")}
                                df_crm = pd.concat([df_crm, pd.DataFrame([new_crm])], ignore_index=True)
                                guardar_df(df_crm, ARCHIVO_CRM)
                                st.success("Guardado.")
                                time.sleep(0.5); st.rerun()

                with c_action:
                    st.markdown("#### 🚀 Gestión y Acción Rápida")
                    if not df_crm.empty:
                        contacto_sel = st.selectbox("Seleccione a quién contactar / editar:", df_crm['Nombre'].unique())
                        datos_contacto = df_crm[df_crm['Nombre'] == contacto_sel].iloc[0]
                        
                        accion_crm = st.radio("Acción:", ["Contactar", "Editar", "Eliminar"], horizontal=True)
                        
                        if accion_crm == "Contactar":
                            num_correo = str(datos_contacto['Contacto']).strip()
                            st.info(f"**Contacto:** {num_correo}\n\n**Nota:** {datos_contacto['Mensaje_Nota']}")
                            
                            msg_pred = f"Hola {contacto_sel}, te contactamos de la gerencia de SportKing."
                            num_limpio = ''.join(filter(str.isdigit, num_correo))
                            
                            if num_limpio and len(num_limpio) >= 10:
                                link_wa = f"https://wa.me/52{num_limpio}?text={msg_pred.replace(' ', '%20')}"
                                st.link_button("🟢 Enviar WhatsApp Web", link_wa, use_container_width=True)
                            
                            if "@" in num_correo and "." in num_correo:
                                link_mail = f"mailto:{num_correo}?subject=Seguimiento%20SportKing&body={msg_pred.replace(' ', '%20')}"
                                st.link_button("📧 Redactar Correo Electrónico", link_mail, use_container_width=True)
                        
                        elif accion_crm == "Editar":
                            with st.form("edit_crm_form"):
                                e_tipo = st.radio("Clasificación:", ["Cliente", "Proveedor"], index=0 if datos_contacto['Tipo']=='Cliente' else 1, horizontal=True)
                                e_contacto = st.text_input("Teléfono o Correo", value=datos_contacto['Contacto'])
                                e_nota = st.text_area("Nota o Petición", value=datos_contacto['Mensaje_Nota'])
                                if st.form_submit_button("Guardar Cambios"):
                                    idx_c = df_crm[df_crm['Nombre'] == contacto_sel].index[0]
                                    df_crm.at[idx_c, 'Tipo'] = e_tipo
                                    df_crm.at[idx_c, 'Contacto'] = e_contacto
                                    df_crm.at[idx_c, 'Mensaje_Nota'] = e_nota
                                    guardar_df(df_crm, ARCHIVO_CRM)
                                    st.success("Contacto actualizado.")
                                    time.sleep(0.5); st.rerun()
                                    
                        elif accion_crm == "Eliminar":
                            st.warning(f"¿Desea eliminar a {contacto_sel} permanentemente?")
                            if st.button("Confirmar Eliminación", type="primary"):
                                df_crm = df_crm[df_crm['Nombre'] != contacto_sel]
                                guardar_df(df_crm, ARCHIVO_CRM)
                                st.success("Contacto eliminado.")
                                time.sleep(0.5); st.rerun()
                    else:
                        st.info("Directorio vacío.")
                
                st.divider()
                c_cli, c_pro = st.columns(2)
                
                df_crm_sorted = df_crm.sort_values(by='Fecha', ascending=False)
                
                with c_cli:
                    st.markdown("##### Clientes")
                    st.dataframe(df_crm_sorted[df_crm_sorted['Tipo']=='Cliente'][['Fecha', 'Nombre', 'Contacto', 'Mensaje_Nota']], hide_index=True)
                with c_pro:
                    st.markdown("##### Proveedores")
                    st.dataframe(df_crm_sorted[df_crm_sorted['Tipo']=='Proveedor'][['Fecha', 'Nombre', 'Contacto', 'Mensaje_Nota']], hide_index=True)
            
            # --- Pestaña 2: Bandeja de Entrada (Preparación para Webhook) ---
            with crm_tabs[1]:
                st.markdown("#### 💬 Mensajes Recibidos Automáticamente")
                st.info("💡 **Aviso:** Streamlit requiere un servidor secundario (como Flask) para recibir Webhooks. Cuando el servidor externo reciba un mensaje de la API de Meta, lo escribirá en el archivo 'tr_inbox.csv' y aparecerá aquí.")
                
                df_inbox = cargar_csv(ARCHIVO_INBOX, ['Fecha', 'Plataforma', 'Remitente', 'Mensaje'])
                
                if df_inbox.empty:
                    st.write("No hay mensajes nuevos en tu bandeja.")
                    if st.button("Simular mensaje entrante (Prueba)"):
                        nuevo_msg = {'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M"), 'Plataforma': 'WhatsApp', 'Remitente': '5576562718', 'Mensaje': 'Hola, ¿tienen disponibilidad de la talla 27?'}
                        df_inbox = pd.concat([df_inbox, pd.DataFrame([nuevo_msg])], ignore_index=True)
                        df_inbox.to_csv(ARCHIVO_INBOX, index=False)
                        st.rerun()
                else:
                    if st.button("Limpiar Bandeja"):
                        if os.path.exists(ARCHIVO_INBOX): os.remove(ARCHIVO_INBOX)
                        st.rerun()
                    
                    st.divider()
                    for _, msg in df_inbox.iterrows():
                        with st.chat_message("user", avatar="💬"):
                            st.write(f"**{msg['Remitente']}** vía {msg['Plataforma']} - {msg['Fecha']}")
                            st.write(f"_{msg['Mensaje']}_")

            # --- Pestaña 3: Configuración APIs ---
            with crm_tabs[2]:
                st.markdown("#### ⚙️ Credenciales de Integración (Meta for Developers)")
                st.write("Llena estos datos con la información de tu app en Meta. El servidor Flask usará estas claves para conectarse.")
                
                df_config = cargar_csv(ARCHIVO_CONFIG_API, ['WA_TOKEN', 'WA_PHONE_ID', 'WEBHOOK_TOKEN'])
                val_token = df_config.iloc[0]['WA_TOKEN'] if not df_config.empty else ""
                val_phone = df_config.iloc[0]['WA_PHONE_ID'] if not df_config.empty else ""
                val_webhk = df_config.iloc[0]['WEBHOOK_TOKEN'] if not df_config.empty else ""
                
                with st.form("api_config_form"):
                    wa_token = st.text_input("WhatsApp Business API Token (Permanent o Temporal)", value=val_token, type="password")
                    wa_phone_id = st.text_input("Phone Number ID", value=val_phone)
                    wa_webhook_token = st.text_input("Webhook Verify Token (El que pondrás en tu script Flask)", value=val_webhk)
                    
                    if st.form_submit_button("Guardar Credenciales"):
                        nuevo_config = {'WA_TOKEN': wa_token, 'WA_PHONE_ID': wa_phone_id, 'WEBHOOK_TOKEN': wa_webhook_token}
                        pd.DataFrame([nuevo_config]).to_csv(ARCHIVO_CONFIG_API, index=False)
                        st.success("Credenciales de API guardadas correctamente para uso del servidor.")
