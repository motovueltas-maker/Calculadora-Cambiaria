import streamlit as st
import requests

# Configuración de página compacta para móvil
st.set_page_config(page_title="Calculadora Cambiaria", layout="wide", initial_sidebar_state="collapsed")

# CSS para optimizar el espacio y márgenes en móviles
st.markdown("""
    <style>
        .block-container { padding-top: 0.5rem; padding-bottom: 0rem; padding-left: 0.5rem; padding-right: 0.5rem; }
        div[data-testid="stVerticalBlock"] > div { gap: 0.2rem; }
        .stNumberInput { margin-bottom: 0px; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { padding-top: 4px; padding-bottom: 4px; }
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
    return 860.1753  # Tasa de respaldo

tasa_api = obtener_tasa_bcv()

# Tasa BCV Global
tasa_bcv = st.number_input("Tasa BCV (Bs.):", value=tasa_api, step=0.01, format="%.4f")
tasa_intervencion = tasa_bcv * 1.005  # BCV + 0,5%

# Pestañas principales
tab1, tab2 = st.tabs(["⚡ Operativa Rápida", "📈 Calculadora de Utilidad"])

# ==========================================
# PESTAÑA 1: OPERATIVA RÁPIDA (IGUAL A LA ANTERIOR)
# ==========================================
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        # A. USD requeridos -> Calcular Bs.
        usd_deseados = st.number_input("USD que quiero comprar:", value=300.00, step=10.0)
        bs_necesarios = usd_deseados * tasa_intervencion
        st.info(f"**Requiere:** Bs. {bs_necesarios:,.2f}")

        # C. Calculadora BPAY (USD Tarjeta -> USD Pasarela)
        usd_tarjeta = st.number_input("USD en Tarjeta (BPAY):", value=500.64, step=10.0)
        comision_banco = st.number_input("% Comisión Banco:", value=2.51, step=0.1) / 100
        usd_pasarela = (usd_tarjeta - 1.50) / (1 + comision_banco) if usd_tarjeta > 1.50 else 0.0
        st.success(f"**Ingresar en BPAY:** ${usd_pasarela:.2f}")

    with col2:
        # B. Bs. disponibles -> Calcular USD
        bs_disponibles = st.number_input("Bs. que dispongo:", value=80699.00, step=500.0)
        usd_obtenidos = bs_disponibles / tasa_intervencion
        st.info(f"**Obtiene:** ${usd_obtenidos:.2f}")

        # D. Vaciar Cuenta (Comisión Interbancaria 0,3%)
        bs_banco = st.number_input("Bs. totales en Banco:", value=216000.00, step=500.0)
        bs_transferir = bs_banco / 1.003
        st.success(f"**Transferir a otro banco:** Bs. {bs_transferir:,.2f}")


# ==========================================
# PESTAÑA 2: CALCULADORA DE UTILIDAD TOTAL
# ==========================================
with tab2:
    col_a, col_b = st.columns(2)

    with col_a:
        usd_comprados_banco = st.number_input("USD comprados en Banco:", value=500.00, step=10.0, key="u_banco")
        comision_banco_u = st.number_input("% Comisión Banco origen:", value=1.50, step=0.1, key="u_com_banco") / 100
        comision_bpay_u = st.number_input("% Pasarela BPay/Binance:", value=4.10, step=0.1, key="u_com_bpay") / 100

        # Cálculo de Bs. utilizados en la compra inicial (Intervención)
        bs_gastados_intervencion = usd_comprados_banco * tasa_intervencion
        st.info(f"**Inversión inicial:** Bs. {bs_gastados_intervencion:,.2f}")

    with col_b:
        tasa_p2p = st.number_input("Tasa Venta P2P Binance (Bs.):", value=967.00, step=0.5, format="%.2f")

        # 1. USD netos en tarjeta tras recargo del banco (fórmula de raspado)
        usd_netos_tarjeta = (usd_comprados_banco - 1.50) / (1 + comision_banco_u) if usd_comprados_banco > 1.50 else 0.0

        # 2. USDT finales que ingresan a Binance tras comisión Bpay
        usdt_recibidos = usd_netos_tarjeta * (1 - comision_bpay_u) if usd_netos_tarjeta > 0 else 0.0

        st.warning(f"**USDT a recibir en Binance:** {usdt_recibidos:.2f} USDT")

    # Resultados y Utilidad Final
    bs_retorno_p2p = usdt_recibidos * tasa_p2p
    utilidad_bs = bs_retorno_p2p - bs_gastados_intervencion
    utilidad_usd_bcv = utilidad_bs / tasa_bcv if tasa_bcv > 0 else 0.0

    st.markdown("---")
    st.success(f"**Retorno Total P2P:** Bs. {bs_retorno_p2p:,.2f}")
    
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric(label="Utilidad Neta (Bs.)", value=f"Bs. {utilidad_bs:,.2f}")
    with col_res2:
        st.metric(label="Utilidad Neta (USD a BCV)", value=f"${utilidad_usd_bcv:,.2f}")
