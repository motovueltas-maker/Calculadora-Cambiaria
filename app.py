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

# --- OCULTAR MENÚ DE STREAMLIT Y ENLACES A GITHUB ---
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stAppHeader {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


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
  st.warning(
      "⚠️ Ingresa una tasa BCV válida en la barra lateral para realizar los"
      " cálculos."
  )
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
        st.caption(
            f"Desglose: {monto_bs:,.2f} Bs / {tasa_intervencion:,.4f} VES"
        )

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
        st.caption(
            f"Desglose: ${usd_objetivo:,.2f} USD × {tasa_intervencion:,.4f} VES"
        )

  # ==========================================
  # CALCULADORA 2: DEPÓSITO FIAT EN BINANCE (BPAY) & INTERBANCARIA
  # ==========================================
  with col2:
    st.subheader("🟡 2. Depósito Fiat en Binance & Transferencia")

    tab_bpay, tab_inter = st.tabs(
        ["💳 Pasarela Binance Bpay", "💸 Transferencia Interbancaria (0.3%)"]
    )

    # Pestaña A: Cálculo inverso para Bpay de Binance
    with tab_bpay:
      st.caption(
          "Calcula cuánto debes ingresar en Bpay según tu neto deseado y"
          " comisiones."
      )

      usd_neto_deseado = st.number_input(
          "USD netos que deseas recibir en Binance:",
          min_value=0.0,
          value=500.0,
          step=10.0,
          format="%.2f",
          key="usd_neto_input",
      )

      comision_banco_pct = st.number_input(
          "Comisión del Banco (%):",
          min_value=0.0,
          max_value=100.0,
          value=2.55,
          step=0.05,
          format="%.2f",
          help="Porcentaje que cobra tu banco local por la transacción.",
          key="comision_banco_input",
      )

      COMISION_BINANCE_PCT = 4.1  # 4.1% fijado por Binance

      if usd_neto_deseado > 0:
        # Inverso: Para que llegue 'usd_neto_deseado' después del 4.1% de Binance:
        # monto_post_banco * (1 - 0.041) = usd_neto_deseado
        monto_post_banco = usd_neto_deseado / (1 - (COMISION_BINANCE_PCT / 100))
        comision_binance = monto_post_banco - usd_neto_deseado

        # Y para que resulte 'monto_post_banco' después de la comisión del banco local:
        # monto_debitado / factor_banco = monto_post_banco  =>  monto_debitado = monto_post_banco * factor_banco
        factor_banco = 1 + (comision_banco_pct / 100)
        monto_debitado = monto_post_banco * factor_banco
        comision_banco = monto_debitado - monto_post_banco

        st.success(
            "🎯 Debes ingresar en Bpay de Binance: **$"
            f" {monto_debitado:,.2f} USD**"
        )
        st.markdown(
            f"""
            * **Monto a Ingresar en Bpay:** `${monto_debitado:,.2f} USD`
            * **Comisión Banco ({comision_banco_pct}%):** `${comision_banco:,.2f} USD`
            * **Comisión Binance (4.1%):** `${comision_binance:,.2f} USD`
            * **Total Neto a Recibir:** `${usd_neto_deseado:,.2f} USD`
            """
        )

    # Pestaña B: Cálculo de Transferencia Interbancaria con comisión del 0.3%
    with tab_inter:
      st.caption(
          "Calcula cuánto transferir interbancariamente descontando el 0.3%:"
      )

      disponible_cuenta_bs = st.number_input(
          "Monto total disponible en cuenta (Bs.):",
          min_value=0.0,
          value=100000.0,
          step=1000.0,
          format="%.2f",
          key="disponible_inter_input",
      )

      COMISION_INTERBANCARIA_PCT = 0.3  # 0.3%

      if disponible_cuenta_bs > 0:
        # Si tienes X disponible y el banco debita el 0.3% sobre la transferencia (o del total):
        # Monto a transferir (T) tal que T * (1 + 0.003) = disponible  ó  si se descuenta del disponible:
        # Lo común al raspar/vaciar cuenta con comisión deducida del monto: Transferir Monto = Disponible / (1 + 0.003)
        # O si el banco cobra el 0.3% adicional sobre el monto enviado:
        factor_inter = 1 + (COMISION_INTERBANCARIA_PCT / 100)
        monto_a_transferir = disponible_cuenta_bs / factor_inter
        comision_interbancaria = disponible_cuenta_bs - monto_a_transferir

        st.success(
            "💸 Monto exacto a transferir: **Bs. {monto_a_transferir:,.2f}**"
        )
        st.markdown(
            f"""
            * **Monto Disponible en Cuenta:** `Bs. {disponible_cuenta_bs:,.2f}`
            * **Monto a Enviar / Transferir:** `Bs. {monto_a_transferir:,.2f}`
            * **Comisión Interbancaria (0.3%):** `Bs. {comision_interbancaria:,.2f}`
            * **Saldo Final en Cuenta:** `Bs. 0,00` (Cuenta raspada / vacía)
            """
        )
