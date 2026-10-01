import streamlit as st
import requests

# Configuración de página compacta para móvil
st.set_page_config(page_title="Calculadora Cambiaria", layout="wide", initial_sidebar_state="collapsed")

# CSS para eliminar espacios blancos excesivos
st.markdown("""
    <style>
        .block-container { padding-top: 0.5rem; padding-bottom: 0rem; padding-left: 0.5rem; padding-right: 0.5rem; }
        div[data-testid="stVerticalBlock"] > div { gap: 0.2rem; }
        .stNumberInput { margin-bottom: 0px; }
    </style>
""", unsafe_allow_html=True)

# Función para obtener la tasa del BCV automáticamente
@st.cache_data(ttl=3600)
def obtener_tasa_bcv():
    try:
        url = "https://pydolarvenezuela-api.vercel.app/api/v1/dollar?page=bcv"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return float(data['monedas']['usd']['promedio'])
    except Exception:
        pass
    return 860.1753  # Valor de respaldo si falla la conexión

tasa_api = obtener_tasa_bcv()

# 1. Tasa BCV (Editable y Automatizada)
tasa_bcv = st.number_input("Tasa BCV (Bs.):", value=tasa_api, step=0.01, format="%.4f")
tasa_intervencion = tasa_bcv * 1.005  # BCV + 0,5%

# Contenedor con columnas compactas
col1, col2 = st.columns(2)

with col1:
    # A. USD requeridos -> Calcular Bs.
    usd_deseados = st.number_input("USD que quiero comprar:", value=100.00, step=10.0)
    bs_necesarios = usd_deseados * tasa_intervencion
    st.info(f"**Requiere:** Bs. {bs_necesarios:,.2f}")

    # C. Calculadora BPAY (USD Tarjeta -> USD Pasarela)
    usd_tarjeta = st.number_input("USD en Tarjeta (BPAY):", value=100.00, step=10.0)
    comision_banco = st.number_input("% Comisión Banco:", value=1.50, step=0.1) / 100
    usd_pasarela = (usd_tarjeta - 1.50) / (1 + comision_banco) if usd_tarjeta > 1.50 else 0.0
    st.success(f"**Ingresar en BPAY:** ${usd_pasarela:.2f}")

with col2:
    # B. Bs. disponibles -> Calcular USD
    bs_disponibles = st.number_input("Bs. que dispongo:", value=38000.00, step=500.0)
    usd_obtenidos = bs_disponibles / tasa_intervencion
    st.info(f"**Obtiene:** ${usd_obtenidos:.2f}")

    # D. Vaciar Cuenta (Comisión Interbancaria 0,3%)
    bs_banco = st.number_input("Bs. totales en Banco:", value=38000.00, step=500.0)
    bs_transferir = bs_banco / 1.003
    st.success(f"**Transferir a otro banco:** Bs. {bs_transferir:,.2f}")
