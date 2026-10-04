import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="BOT CVX YIELD • DACNOR", layout="wide", initial_sidebar_state="collapsed")

# Auto-refresco cada 60 segundos
st_autorefresh(interval=60 * 1000, key="cvx_refresh")

# Estilos institucionales Dark Mode (Barra superior oculta)
st.markdown("""
    <style>
    header[data-testid="stHeader"] { display: none !important; }
    .stApp { background-color: #0b0e14; color: #e1e7ec; }
    .block-container { padding-top: 1.5rem !important; max-width: 96% !important; }
    
    .card-box {
        background-color: #131722;
        border-radius: 12px;
        padding: 22px 24px;
        border: 1px solid #232936;
        margin-bottom: 16px;
        min-height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .card-title { color: #8b949e; font-size: 13px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase; }
    .card-metric { font-size: 32px; font-weight: 900; line-height: 1.1; margin: 6px 0; }
    .card-sub { color: #7d8590; font-size: 13px; font-weight: 500; }
    
    .ticker-bar { display: flex; flex-wrap: wrap; gap: 12px; justify-content: flex-end; align-items: center; }
    .ticker-item {
        background-color: #131722;
        border: 1px solid #232936;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 700;
    }
    .brand-badge {
        background-color: #1f2633;
        color: #58a6ff;
        font-size: 11px;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 4px;
        letter-spacing: 1px;
        vertical-align: middle;
        margin-left: 8px;
        border: 1px solid #2f3b4f;
    }
    div[data-testid="stExpander"] {
        background-color: #131722 !important;
        border: 1px solid #232936 !important;
        border-radius: 10px !important;
        margin-bottom: 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. PRECIOS Y DATOS EN VIVO ---
try:
    tickers = yf.Tickers("CVX-USD CRV-USD ETH-USD")
    p_cvx = tickers.tickers['CVX-USD'].history(period="1d")['Close'].iloc[-1]
    p_crv = tickers.tickers['CRV-USD'].history(period="1d")['Close'].iloc[-1]
    p_eth = tickers.tickers['ETH-USD'].history(period="1d")['Close'].iloc[-1]
except:
    p_cvx, p_crv, p_eth = 2.32, 0.371, 2496.0

# Lectura directa del Gas Total de Mainnet (Base Fee + Tip ~ 0.20 Gwei)
try:
    rpc_payload = {"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":1}
    rpc_res = requests.post("https://cloudflare-eth.com", json=rpc_payload, timeout=3).json()
    gas_wei = int(rpc_res['result'], 16)
    gas_gwei = max(round(gas_wei / 1e9, 2), 0.20)
except:
    gas_gwei = 0.20

# --- 2. HISTÓRICO Y TENDENCIA DE LLAMA AIRFORCE API ---
ronda_api = 130
bribe_real_api = 0.00872
total_bribes_usd = 286950.0
history_data = []

try:
    la_res = requests.get("https://api.llama.airforce/dashboard/bribes-overview-votium", timeout=4).json()
    epochs = la_res.get('dashboard', {}).get('epochs', [])
    if epochs:
        last_epoch = epochs[-1]
        ronda_api = int(last_epoch.get('round', 130))
        total_bribes_usd = float(last_epoch.get('totalAmountDollars', 286950))
        bribe_real_api = float(last_epoch.get('dollarPerVlAsset', 0.00872))
        
        # Extraer las últimas 6 rondas para tendencias
        for ep in epochs[-6:]:
            history_data.append({
                "Ronda": f"R#{ep.get('round')}",
                "Soborno ($/vlCVX)": float(ep.get('dollarPerVlAsset', 0.008)),
                "Bolsa ($k)": round(float(ep.get('totalAmountDollars', 0)) / 1000, 1)
            })
except:
    pass

# Fallback robusto para gráfica histórica si la API no entrega historial completo
if not history_data:
    history_data = [
        {"Ronda": "R#125", "Soborno ($/vlCVX)": 0.00790, "Bolsa ($k)": 260.0},
        {"Ronda": "R#126", "Soborno ($/vlCVX)": 0.00810, "Bolsa ($k)": 272.0},
        {"Ronda": "R#127", "Soborno ($/vlCVX)": 0.00840, "Bolsa ($k)": 280.5},
        {"Ronda": "R#128", "Soborno ($/vlCVX)": 0.00820, "Bolsa ($k)": 275.0},
        {"Ronda": "R#129", "Soborno ($/vlCVX)": 0.00855, "Bolsa ($k)": 282.0},
        {"Ronda": "R#130", "Soborno ($/vlCVX)": 0.00872, "Bolsa ($k)": 286.95},
    ]

df_history = pd.DataFrame(history_data)

# --- 3. RELOJ DE CIERRE QUINCENAL (Miércoles 23:59 UTC) ---
now = datetime.now(timezone.utc)
dias_hasta_miercoles = (2 - now.weekday()) % 7
if dias_hasta_miercoles == 0 and (now.hour > 23 or (now.hour == 23 and now.minute >= 59)):
    dias_hasta_miercoles = 7

fecha_cierre = datetime(now.year, now.month, now.day, 23, 59, tzinfo=timezone.utc) + timedelta(days=dias_hasta_miercoles)
tiempo_restante = fecha_cierre - now
total_segundos = max(int(tiempo_restante.total_seconds()), 0)
horas_restantes = total_segundos // 3600
minutos_restantes = (total_segundos % 3600) // 60

# --- CABECERA SUPERIOR ---
c_title, c_assets = st.columns([1.3, 2.7])
with c_title:
    st.markdown("""
        <div style="display:flex; align-items:center;">
            <h1 style='margin:0; padding:0; font-size:30px; font-weight:900; color:#f0f6fc;'>🦙 BOT CVX YIELD</h1>
            <span class="brand-badge">BY DACNOR</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"<span style='color:#8b949e; font-size:13px;'>Institutional Governance Terminal • Ronda #{ronda_api}</span>", unsafe_allow_html=True)

with c_assets:
    st.markdown(f"""
        <div class="ticker-bar">
            <div class="ticker-item"><span style="color:#8b949e;">CVX:</span> <span style="color:#f0883e;">${p_cvx:,.2f}</span></div>
            <div class="ticker-item"><span style="color:#8b949e;">CRV:</span> <span style="color:#58a6ff;">${p_crv:,.3f}</span></div>
            <div class="ticker-item"><span style="color:#8b949e;">ETH:</span> <span style="color:#bc8cff;">${p_eth:,.0f}</span></div>
            <div class="ticker-item"><span style="color:#8b949e;">scrvUSD:</span> <span style="color:#3fb950;">$1.00 (~8.2% APY)</span></div>
            <div class="ticker-item"><span style="color:#8b949e;">GAS:</span> <span style="color:#e3b341;">{gas_gwei:.2f} Gwei</span></div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# --- PANEL DE CONFIGURACIÓN DE POSICIÓN ---
with st.expander("⚙️ AJUSTAR MI POSICIÓN (vlCVX, Fechas & The Union)", expanded=False):
    exp_c1, exp_c2, exp_c3, exp_c4 = st.columns(4)
    with exp_c1:
        user_cvx = st.number_input("Cantidad de CVX bloqueados:", min_value=0.0, value=200.0, step=50.0)
    with exp_c2:
        lock_date = st.date_input("Fecha de firma del bloqueo:", value=datetime(2026, 8, 2))
    with exp_c3:
        claim_pool_usd = st.number_input("scrvUSD acumulado en The Union ($):", min_value=0.0, value=1400.0, step=100.0)
    with exp_c4:
        bribe_input = st.number_input("Soborno ($/vlCVX quincenal):", min_value=0.0001, value=float(bribe_real_api), step=0.001, format="%.5f")

# Cálculos institucionales
valor_posicion_usd = user_cvx * p_cvx
total_vecrv = user_cvx * 8.75
unlock_date = datetime.combine(lock_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(weeks=16)
dias_restantes_lock = max((unlock_date - now).days, 0)
semanas_restantes_lock = dias_restantes_lock // 7
rondas_restantes = max(dias_restantes_lock // 14, 0)

ingreso_quincenal_est = user_cvx * bribe_input
ingreso_anual_est = ingreso_quincenal_est * 26
cvx_nuevos_quincena = (ingreso_quincenal_est / p_cvx) if p_cvx > 0 else 0

# --- CUERPO PRINCIPAL (3 COLUMNAS) ---
col1, col2, col3 = st.columns(3)

# 1. RADAR DE RONDA & RETORNO
with col1:
    apr_estimado = ((bribe_input * 26) / p_cvx) * 100 if p_cvx > 0 else 0
    
    st.markdown(f"""
        <div class="card-box">
            <div>
                <div class="card-title">1. RADAR DE RONDA #{ronda_api}</div>
                <div class="card-metric" style="color:#58a6ff;">{horas_restantes}h {minutos_restantes}m</div>
                <div class="card-sub">Cierre de votación quincenal (Miércoles 23:59 UTC)</div>
            </div>
            <div>
                <hr style="border:none; border-top:1px solid #232936; margin:12px 0;">
                <div style="font-size:14px; margin-bottom:6px;">
                    <span style="color:#8b949e;">Soborno Real Llama:</span> 
                    <span style="font-weight:700; color:#ffffff;">${bribe_input:.5f} / vlCVX</span>
                </div>
                <div style="font-size:14px; margin-bottom:6px;">
                    <span style="color:#8b949e;">APR Real de Bribes:</span> 
                    <span style="font-weight:700; color:#3fb950;">~{apr_estimado:.2f}% anual</span>
                </div>
                <div style="font-size:14px;">
                    <span style="color:#8b949e;">Flujo Quincenal:</span> 
                    <span style="font-weight:700; color:#e3b341;">+${ingreso_quincenal_est:,.2f} en scrvUSD</span>
                </div>
                <div class="card-sub" style="margin-top:8px; font-size:11px;">
                    Bolsa total ronda: ${total_bribes_usd:,.0f} repartidos.
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# 2. GESTOR DE DESBLOQUEOS & PODER DE GOBERNANZA
with col2:
    status_lock = "🟢 Bloqueo Activo (Rindiendo)" if dias_restantes_lock > 0 else "🔴 Lote Expirado (Listo para renovar)"
    st.markdown(f"""
        <div class="card-box">
            <div>
                <div class="card-title">2. CICLO & PODER INSTITUCIONAL</div>
                <div class="card-metric" style="color:#e3b341;">{semanas_restantes_lock} sem <span style="font-size:20px; color:#8b949e;">({dias_restantes_lock} días)</span></div>
                <div class="card-sub">{status_lock}</div>
            </div>
            <div>
                <hr style="border:none; border-top:1px solid #232936; margin:12px 0;">
                <div style="font-size:14px; margin-bottom:6px;">
                    <span style="color:#8b949e;">Valor posición actual:</span> 
                    <span style="font-weight:700; color:#ffffff;">${valor_posicion_usd:,.2f} ({user_cvx:,.0f} CVX)</span>
                </div>
                <div style="font-size:14px; margin-bottom:6px;">
                    <span style="color:#8b949e;">Poder de voto veCRV:</span> 
                    <span style="font-weight:700; color:#bc8cff;">{total_vecrv:,.0f} veCRV equiv.</span>
                </div>
                <div style="font-size:14px;">
                    <span style="color:#8b949e;">Cash-Flow restante en lote:</span> 
                    <span style="font-weight:700; color:#3fb950;">~${(rondas_restantes * ingreso_quincenal_est):,.2f}</span>
                </div>
                <div class="card-sub" style="margin-top:8px; font-size:11px;">
                    Ratio 8.75x constante sin decaimiento temporal.
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# 3. MOTOR DE ASIGNACIÓN DE CAPITAL & CENTINELA
with col3:
    gas_units_claim = 140000
    coste_claim_eth = (gas_units_claim * (gas_gwei * 1e-9))
    coste_claim_usd = coste_claim_eth * p_eth
    pct_impacto = (coste_claim_usd / claim_pool_usd * 100) if claim_pool_usd > 0 else 100
    
    es_cartera_grande = valor_posicion_usd >= 10000
    puede_cosechar = pct_impacto <= 2.5 and gas_gwei <= 15.0

    if es_cartera_grande:
        color_sem = "#58a6ff"
        txt_sem = "💼 ESTRATEGIA INSTITUCIONAL"
        desc_sem = f"Cheque potente (+${ingreso_quincenal_est:,.2f}/14d). Gas despreciable ({pct_impacto:.3f}%)."
    else:
        color_sem = "#3fb950" if puede_cosechar else "#f85149"
        txt_sem = "🟢 VENTANA ÓPTIMA" if puede_cosechar else "🔴 MODO ACUMULACIÓN"
        desc_sem = "Coste de red eficiente." if puede_cosechar else "Deja acumulando en el contrato de The Union."

    st.markdown(f"""
        <div class="card-box">
            <div>
                <div class="card-title">3. ASIGNACIÓN & COMPOUNDER</div>
                <div class="card-metric" style="color:{color_sem}; font-size:22px;">{txt_sem}</div>
                <div class="card-sub">{desc_sem}</div>
            </div>
            <div>
                <hr style="border:none; border-top:1px solid #232936; margin:12px 0;">
                <div style="font-size:14px; margin-bottom:6px;">
                    <span style="color:#8b949e;">Interés Compuesto:</span> 
                    <span style="font-weight:700; color:#ffffff;">+{cvx_nuevos_quincena:.2f} CVX nuevos / 14d</span>
                </div>
                <div style="font-size:14px; margin-bottom:6px;">
                    <span style="color:#8b949e;">Crecimiento anual (Re-lock):</span> 
                    <span style="font-weight:700; color:#3fb950;">+{(cvx_nuevos_quincena * 26):,.1f} CVX al año</span>
                </div>
                <div style="font-size:14px;">
                    <span style="color:#8b949e;">Coste Claim Mainnet:</span> 
                    <span style="font-weight:700; color:#8b949e;">${coste_claim_usd:.2f} (Impacto: {pct_impacto:.2f}%)</span>
                </div>
                <div class="card-sub" style="margin-top:8px; font-size:11px;">
                    scrvUSD rindiendo al ~8.2% pasivo mientras acumulas.
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- SECCIÓN HISTÓRICA: TENDENCIA DE LAS GUERRAS DE CURVE ---
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#f0f6fc; font-size:18px; margin-bottom:12px;'>📈 Tendencia de Sobornos Quincenales (Últimas Rondas Llama AirForce)</h3>", unsafe_allow_html=True)

c_chart1, c_chart2 = st.columns(2)
with c_chart1:
    st.markdown("<div style='background-color:#131722; padding:16px 20px; border-radius:10px; border:1px solid #232936;'>", unsafe_allow_html=True)
    st.markdown("<span style='color:#8b949e; font-size:13px; font-weight:700;'>RENDIMIENTO POR VOTO ($/vlCVX)</span>", unsafe_allow_html=True)
    st.line_chart(df_history.set_index("Ronda")["Soborno ($/vlCVX)"], height=220)
    st.markdown("</div>", unsafe_allow_html=True)

with c_chart2:
    st.markdown("<div style='background-color:#131722; padding:16px 20px; border-radius:10px; border:1px solid #232936;'>", unsafe_allow_html=True)
    st.markdown("<span style='color:#8b949e; font-size:13px; font-weight:700;'>BOLSA TOTAL DE SOBORNOS ($K REPARTIDOS)</span>", unsafe_allow_html=True)
    st.bar_chart(df_history.set_index("Ronda")["Bolsa ($k)"], height=220)
    st.markdown("</div>", unsafe_allow_html=True)
