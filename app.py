import streamlit as st
import requests

# Configuración de página
st.set_page_config(page_title="Calculadora Cambiaria", layout="centered", initial_sidebar_state="collapsed")

# --- CSS PARA ESTILO MÓVIL Y OCULTAR ELEMENTOS SUPERIORES ---
st.markdown("""
    <style>
        /* Ocultar barra superior, menú de Streamlit, footer y GitHub */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        div[data-testid="stDecoration"] {display: none;}
        
        /* Ocultar apariciones de barras superiores adicionales */
        .stAppHeader {display: none !important;}
        div[data-testid="stStatusWidget"] {visibility: hidden;}
        .stAppDeployButton {display: none;}

        .block-container { 
            padding-top: 1rem !important; 
            padding-bottom: 1rem !important; 
            padding-left: 0.8rem !important; 
            padding-right: 0.8rem !important; 
        }
        .stNumberInput label {
            font-size: 0.85rem !important;
            font-weight: 600 !important;
        }
        .stAlert {
            padding: 0.5rem !important;
            font-size: 0.9rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIÓN TASA BCV AUTOMÁTICA CON DOBLE FUENTE Y FALLBACK 0 ---
def obtener_tasa_bcv():
    # Intento 1: PyDolarVenezuela
    try:
        url1 = "https://pydolarvenezuela-api.vercel.app/api/v1/dollar?page=bcv"
        res1 = requests.get(url1, timeout=4)
        if res1.status_code == 200:
            data = res1.json()
            return float(data['monedas']['usd']['promedio'])
    except Exception:
        pass

    # Intento 2: DolarApi (Respaldo)
    try:
        url2 = "https://ve.dolarapi.com/v1/dolares/oficial"
        res2 = requests.get(url2, timeout=4)
        if res2.status_code == 200:
            data = res2.json()
            return float(data['promedio'])
    except Exception:
        pass

    # Si todo falla, devuelve 0 para no usar datos viejos por error
    return 0.0

# --- EJECUCIÓN DE LA FUNCIÓN ---
tasa_api = obtener_tasa_bcv()

# --- ENCABEZADO Y TASA BANCARIA ---
st.title("💱 Calculadora Cambiaria")

# Si la tasa falló (es 0.0), mostramos alerta visible
if tasa_api == 0.0:
    st.error("⚠️ No se pudo obtener la tasa oficial en línea. Por favor, ingresa el valor del BCV manualmente.")

# Campo editable para la tasa BCV
tasa_bcv = st.number_input("Tasa BCV del día (Bs.):", value=tasa_api, step=0.01, format="%.4f")
tasa_intervencion = tasa_bcv * 1.005  # BCV + 0.5%

st.caption(f"Tasa Intervención (BCV + 0.5%): **Bs. {tasa_intervencion:,.4f}**")

# ==========================================
# SECCIÓN 1: OPERATIVA DE INTERVENCIÓN
# ==========================================
with st.expander("⚡ **Operativa de Intervención (Compra/Venta)**", expanded=True):
    opcion = st.radio("¿Qué deseas calcular?", ["Quiero USD", "Tengo Bs"], key="op_interv")

    if opcion == "Quiero USD":
        usd_deseados = st.number_input("USD que deseas obtener:", value=100.00, step=10.0)
        bs_necesarios = usd_deseados * tasa_intervencion
        st.info(f"Requieres: **Bs. {bs_necesarios:,.2f}**")
    else:
        bs_disponibles = st.number_input("Bs. que dispones:", value=80000.00, step=500.0)
        usd_obtenidos = bs_disponibles / tasa_intervencion
        st.info(f"Obtienes: **${usd_obtenidos:,.2f} USD**")

    st.divider()

    # Cálculo Tarjeta BPAY
    usd_tarjeta = st.number_input("USD en Tarjeta:", value=500.00, step=10.0)
    comision_banco = st.number_input("% Com. Banco:", value=2.51, step=0.1) / 100
    usd_pasarela = (usd_tarjeta - 1.50) / (1 + comision_banco) if usd_tarjeta > 1.50 else 0.0
    st.success(f"Pasarela BPAY: **${usd_pasarela:.2f}**")

# ==========================================
# SECCIÓN 2: VACIAR CUENTA / TRANSFERIR (INDEPENDIENTE)
# ==========================================
with st.expander("🏦 **Vaciar Cuenta / Transferir Interbancario (Comisión 0.3%)**", expanded=False):
    bs_banco = st.number_input("Bs. Totales que tienes en el Banco:", value=200000.00, step=1000.0, key="v_banco")
    bs_transferir = bs_banco / 1.003
    comision_aplicada = bs_banco - bs_transferir
    
    st.success(f"Monto exacto a transferir: **Bs. {bs_transferir:,.2f}**")
    st.caption(f"Comisión estimada (0.3%): Bs. {comision_aplicada:,.2f}")

# ==========================================
# SECCIÓN 3: CONVERSIÓN SIMPLE BCV
# ==========================================
with st.expander("💱 **Conversión Directa a Tasa BCV**", expanded=False):
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        usd_directo = st.number_input("USD a convertir:", value=100.00, step=10.0, key="conv_usd")
        st.success(f"Equivale a: **Bs. {(usd_directo * tasa_bcv):,.2f}**")
    with col_c2:
        bs_directo = st.number_input("Bs. a convertir:", value=1000.00, step=100.0, key="conv_bs")
        st.info(f"Equivale a: **${(bs_directo / tasa_bcv if tasa_bcv > 0 else 0.0):.2f} USD**")

# ==========================================
# SECCIÓN 4: UTILIDAD P2P BINANCE
# ==========================================
with st.expander("📈 **Calculadora de Utilidad P2P**", expanded=False):
    usd_comprados_banco = st.number_input("USD Comprados en Banco:", value=500.00, step=10.0, key="u_banco")
    comision_banco_u = st.number_input("% Comisión Banco Origen:", value=1.50, step=0.1, key="u_com_b") / 100
    comision_bpay_u = st.number_input("% Pasarela BPay/Binance:", value=4.10, step=0.1, key="u_com_bp") / 100
    
    # 1. Cálculos de Inversión y USDT Netos
    bs_gastados = usd_comprados_banco * tasa_intervencion
    usd_netos_tarjeta = (usd_comprados_banco - 1.50) / (1 + comision_banco_u) if usd_comprados_banco > 1.50 else 0.0
    usdt_recibidos = usd_netos_tarjeta * (1 - comision_bpay_u) if usd_netos_tarjeta > 0 else 0.0
    
    # 2. DATOS DE IMPACTO INMEDIATO: Costo efectivo por USDT en Bs.
    costo_por_usdt = (bs_gastados / usdt_recibidos) if usdt_recibidos > 0 else 0.0

    st.markdown("---")
    st.metric(
        label="🎯 Costo Real de 1 USDT en Binance",
        value=f"Bs. {costo_por_usdt:,.2f} / USDT",
        help="Este es tu punto de equilibrio: cualquier precio P2P por encima de este valor es ganancia neta."
    )
    st.caption(f"• Inversión total: **Bs. {bs_gastados:,.2f}** | Recibes en Binance: **{usdt_recibidos:,.2f} USDT**")
    st.markdown("---")

    # 3. Tasa P2P y Resultados de Utilidad
    tasa_p2p = st.number_input("Tasa Venta P2P (Bs.):", value=967.00, step=0.5, format="%.2f")

    bs_retorno_p2p = usdt_recibidos * tasa_p2p
    utilidad_bs = bs_retorno_p2p - bs_gastados
    utilidad_usd_bcv = utilidad_bs / tasa_bcv if tasa_bcv > 0 else 0.0
    
    # Porcentaje de ganancia sobre la inversión inicial (%)
    porcentaje_utilidad = (utilidad_bs / bs_gastados * 100) if bs_gastados > 0 else 0.0

    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1:
        st.metric("Ganancia (Bs.)", f"Bs. {utilidad_bs:,.2f}")
    with col_u2:
        st.metric("Ganancia (USD BCV)", f"${utilidad_usd_bcv:,.2f}")
    with col_u3:
        st.metric("% Utilidad", f"{porcentaje_utilidad:.2f}%")
