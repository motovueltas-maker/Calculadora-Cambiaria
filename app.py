import streamlit as st

# Configuración para aprovechar toda la pantalla
st.set_page_config(page_title="Calculadora", layout="wide", initial_sidebar_state="collapsed")

# CSS para reducir espacios y márgenes en móviles
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 0.5rem; padding-right: 0.5rem; }
        h1, h2, h3 { margin: 0px; padding: 0px; }
        div[data-testid="stVerticalBlock"] > div { gap: 0.3rem; }
    </style>
""", unsafe_allow_html=True)

# 1. Tasa BCV Base
tasa_bcv = st.number_input("Tasa BCV:", value=860.1753, step=0.01, format="%.4f")
tasa_intervencion = tasa_bcv * 1.005  # 0.5% comisión

# 2. Dos columnas para ver todo en paralelo
col1, col2 = st.columns(2)

with col1:
    bs_disp = st.number_input("Bs. en cuenta:", value=37887.00, step=100.0)
    usd_adquiridos = bs_disp / tasa_intervencion
    st.success(f"**USD:** ${usd_adquiridos:.2f}")

with col2:
    bs_total = st.number_input("Bs. total a vaciar:", value=38001.12, step=100.0)
    monto_transferir = bs_total / 1.003
    st.success(f"**Transferir:** Bs. {monto_transferir:,.2f}")
