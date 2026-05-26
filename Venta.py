import streamlit as st
import pandas as pd
import barcode
from barcode.writer import ImageWriter
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ERP Total SalePony", layout="wide")

# --- ESTADO INICIAL ---
if 'inventario' not in st.session_state:
    st.session_state.inventario = pd.DataFrame(columns=["ID", "Modelo", "Stock", "Precio", "Fecha Ingreso", "Costo"])
if 'ventas' not in st.session_state:
    st.session_state.ventas = pd.DataFrame(columns=["Fecha", "Modelo", "Cantidad", "Total", "Vendedor", "Metodo"])

# --- FUNCIONES ---
def generar_codigo_barras(sku):
    ean = barcode.get('ean13', str(sku).zfill(12), writer=ImageWriter())
    return ean.save(f"sku_{sku}")

# --- INTERFAZ ---
st.title("🏭 ERP Total: SalePony Management")

menu = st.sidebar.selectbox("Módulos", ["Inventario", "Ventas/Cobros", "Remates", "CRM/Mensajes", "Bonos/Comisiones"])

if menu == "Inventario":
    st.header("Gestión de Inventario")
    with st.form("nuevo_producto"):
        modelo = st.text_input("Modelo")
        stock = st.number_input("Stock Inicial", min_value=0)
        precio = st.number_input("Precio Venta")
        submitted = st.form_submit_button("Subir Mercancía")
        if submitted:
            new_row = {"ID": len(st.session_state.inventario)+1, "Modelo": modelo, "Stock": stock, "Precio": precio, "Fecha Ingreso": datetime.date.today(), "Costo": precio*0.6}
            st.session_state.inventario = pd.concat([st.session_state.inventario, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Producto {modelo} registrado.")
    st.table(st.session_state.inventario)

elif menu == "Ventas/Cobros":
    st.header("Punto de Venta")
    modelo_vta = st.selectbox("Seleccionar Modelo", st.session_state.inventario["Modelo"].tolist())
    cant = st.number_input("Cantidad", min_value=1)
    metodo = st.selectbox("Método de Pago", ["Efectivo", "Tarjeta", "Transferencia", "Pagos Móviles"])
    vendedor = st.text_input("Nombre Vendedor")
    
    if st.button("Registrar Venta"):
        total = cant * st.session_state.inventario[st.session_state.inventario["Modelo"] == modelo_vta]["Precio"].values[0]
        st.session_state.ventas = pd.concat([st.session_state.ventas, pd.DataFrame([{"Fecha": datetime.datetime.now(), "Modelo": modelo_vta, "Cantidad": cant, "Total": total, "Vendedor": vendedor, "Metodo": metodo}])], ignore_index=True)
        st.success(f"Venta registrada por ${total}")

elif menu == "Remates":
    st.header("Liquidación de Mercancía Parada")
    st.write("Productos con más de 30 días en inventario:")
    # Lógica de remate: si fecha ingreso es vieja, mostrar aquí
    st.warning("Próximamente: Integración con base de datos de fechas.")

elif menu == "CRM/Mensajes":
    st.header("Mensajería Proveedores/Clientes")
    tipo = st.radio("Destinatario", ["Cliente", "Proveedor"])
    msg = st.text_area("Mensaje rápido")
    if st.button("Enviar Mensaje"):
        st.info(f"Enviando mensaje a {tipo}: {msg}")

elif menu == "Bonos/Comisiones":
    st.header("Calculadora de Bonos")
    st.write("Comisiones calculadas automáticamente al 5% sobre el total vendido por vendedor.")
    if not st.session_state.ventas.empty:
        resumen = st.session_state.ventas.groupby("Vendedor")["Total"].sum() * 0.05
        st.table(resumen)
