from datetime import date
import requests
import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="Calculadora Cambiaria & Bancaria",
    page_icon="🧮",
    layout="wide",
)

st.title("🧮 Calculadora de Intervención & Depósito Fiat")


# --- FUNCIÓN PARA OBTENER TASA BCV AUTOMÁTICA ---
def obtener_tasa_bcv():
    try:
        url = "https://rates.dolarvzla.com/bcv/current.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return float(data["current"]["usd"])
    except Exception:
        pass
    return None


# --- GESTIÓN DEL ESTADO PERSISTENTE (st.session_state) ---
hoy_str = str(date.today())

if "fecha_guardada" not in st.session_state:
    st.session_state.fecha_guardada = hoy_str

if "tasa_bcv" not in st.session_state:
    tasa_api = obtener_tasa_bcv()
    st.session_state.tasa_bcv = tasa_api if tasa_api else 0.0

if st.session_state.fecha_guardada != hoy_str:
    tasa_api = obtener_tasa_bcv()
    if tasa_api:
        st.session_state.tasa_bcv = tasa_api
    st.session_state.fecha_guardada = hoy_str

# --- BARRA LATERAL: CONFIGURACIÓN BASE DE TASA BCV ---
st.sidebar.header("⚙️ Configuración de Tasa Base")
st.sidebar.info(f"Fecha del día: **{st.session_state.fecha_guardada}**")

tasa_input = st.sidebar.number_input(
    "Tasa USD BCV (Bs.):",
    min_value=0.0,
    value=float(st.session_state.tasa_bcv),
    step=0.01,
    format="%.4f",
    help="Puedes modificar este valor manualmente.",
)

st.sidebar.button(
    "🔄 Refrescar Tasa vía API",
    on_click=lambda: st.session_state.update(
        tasa_bcv=obtener_tasa_bcv() or st.session_state.tasa_bcv
    ),
)
st.session_state.tasa_bcv = tasa_input
tasa_bcv = st.session_state.tasa_bcv

if tasa_bcv <= 0:
    st.warning("⚠️ Ingresa una tasa BCV válida en la barra lateral para realizar los cálculos.")
else:
    # CÁLCULO DE INTERVENCIÓN (+ 0.5% de comisión bancaria)
    COMISION_INTERVENCION = 0.005  # 0.5%
    tasa_intervencion = tasa_bcv * (1 + COMISION_INTERVENCION)

    # --- PANTALLA PRINCIPAL: DOS COLUMNAS DE CALCULADORAS ---
    col1, col2 = st.columns(2)

    # ==========================================
    # CALCULADORA 1: INTERVENCIÓN CAMBIARIA (BIDIRECCIONAL)
    # ==========================================
    with col1:
        st.subheader("🏦 1. Intervención Cambiaria")
        st.markdown(
            f"""
        * **Tasa BCV Base:** `{tasa_bcv:,.4f} VES`
        * **Comisión Bancaria:** `0.5%`
        * **Tasa Intervención Efectiva:** `{tasa_intervencion:,.4f} VES`
        """
        )

        # Usamos pestañas para cambiar el sentido del cálculo
        tab_bs_to_usd, tab_usd_to_bs = st.tabs(["💵 De Bs. a USD", "🇻🇪 De USD a Bs."])

        # Sentido 1: Tengo Bolívares -> ¿Cuántos USD puedo comprar?
        with tab_bs_to_usd:
            st.caption("Ingresa los Bolívares disponibles en tu cuenta:")
            monto_bs = st.number_input(
                "Monto disponible en Bs.:",
                min_value=0.0,
                value=480000.0,
                step=1000.0,
                format="%.2f",
                key="monto_bs_input",
            )
            if monto_bs > 0:
                usd_comprados = monto_bs / tasa_intervencion
                st.success(f"💰 Puedes adquirir: **${usd_comprados:,.2f} USD**")
                st.caption(f"Desglose: {monto_bs:,.2f} Bs / {tasa_intervencion:,.4f} VES")

        # Sentido 2: Quiero comprar N Dólares -> ¿Cuántos Bolívares necesito?
        with tab_usd_to_bs:
            st.caption("Ingresa cuántos USD deseas comprar:")
            usd_objetivo = st.number_input(
                "Dólares a comprar (USD):",
                min_value=0.0,
                value=500.0,
                step=10.0,
                format="%.2f",
                key="usd_objetivo_input",
            )
            if usd_objetivo > 0:
                bs_necesarios = usd_objetivo * tasa_intervencion
                st.success(f"🇻🇪 Necesitas disponer de: **Bs. {bs_necesarios:,.2f}**")
                st.caption(f"Desglose: ${usd_objetivo:,.2f} USD × {tasa_intervencion:,.4f} VES")

    # ==========================================
    # CALCULADORA 2: DEPÓSITO FIAT EN BINANCE
    # ==========================================
    with col2:
        st.subheader("🟡 2. Depósito Fiat en Binance")
        st.caption("Calcula cuánto puedes depositar según la comisión de tu banco.")

        usd_disponibles = st.number_input(
            "USD disponibles en tu cuenta bancaria:",
            min_value=0.0,
            value=500.0,
            step=10.0,
            format="%.2f",
            key="usd_disponibles_input",
        )

        comision_banco_pct = st.number_input(
            "Comisión del Banco (%):",
            min_value=0.0,
            max_value=100.0,
            value=2.55,
            step=0.05,
            format="%.2f",
            help="Edita este porcentaje según las políticas de tu banco.",
            key="comision_banco_input",
        )

        if usd_disponibles > 0:
            factor_comision = 1 + (comision_banco_pct / 100)
            usd_netos_binance = usd_disponibles / factor_comision
            comision_cobrada = usd_disponibles - usd_netos_binance

            st.success(f"📥 Puedes ingresar a Binance: **${usd_netos_binance:,.2f} USD**")
            st.markdown(
                f"""
            * **Monto Total Debitados:** `${usd_disponibles:,.2f} USD`
            * **Comisión del Banco ({comision_banco_pct}%):** `${comision_cobrada:,.2f} USD`
            * **Neto a Recibir en Binance:** `${usd_netos_binance:,.2f} USD`
            """
            )
