import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="BOT DAC CVX YIELD", layout="wide", initial_sidebar_state="expanded")

# Auto-refresco cada 60 segundos
st_autorefresh(interval=60 * 1000, key="cvx_refresh")

# Estilos idénticos al Bot Macro
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e1e7ec; }
    .block-container { padding-top: 1.8rem !important; max-width: 96% !important; }
    .card-box {
        background-color: #131722;
        border-radius: 12px;
        padding: 20px 22px;
        border: 1px solid #232936;
        margin-bottom: 16px;
    }
    .card-title { color: #8b949e; font-size: 13px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase; }
    .card-metric { font-size: 32px; font-weight: 900; line-height: 1.1; margin: 8px 0; }
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
    </style>
""", unsafe_allow_html=True)

# --- 1. PRECIOS Y DATOS EN VIVO (Yahoo Finance & DeFi APIs) ---
try:
    tickers = yf.Tickers("CVX-USD CRV-USD ETH-USD")
    p_cvx = tickers.tickers['CVX-USD'].history(period="1d")['Close'].iloc[-1]
    p_crv = tickers.tickers['CRV-USD'].history(period="1d")['Close'].iloc[-1]
    p_eth = tickers.tickers['ETH-USD'].history(period="1d")['Close'].iloc[-1]
except:
    p_cvx, p_crv, p_eth = 2.30, 0.35, 2500.0

# Gas aproximado de Mainnet
try:
    gas_res = requests.get("https://api.blocknative.com/gasprices/blockprices", timeout=3).json()
    gas_gwei = float(gas_res['blockPrices'][0]['estimatedPrices'][0]['price'])
except:
    gas_gwei = 6.0

# --- 2. CÁLCULO DE LA RONDA QUINCENAL (Reloj Votium / Convex) ---
# Miércoles es weekday 2. Cierre 23:59 UTC.
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
c_title, c_assets = st.columns([1.2, 2.8])
with c_title:
    st.markdown("<h1 style='margin:0; padding:0; font-size:30px; font-weight:900; color:#f0f6fc;'>⚡ BOT DAC CVX YIELD</h1>", unsafe_allow_html=True)
    st.markdown("<span style='color:#8b949e; font-size:13px;'>Curve Wars • The Union • vlCVX Sentinel</span>", unsafe_allow_html=True)

with c_assets:
    st.markdown(f"""
        <div class="ticker-bar">
            <div class="ticker-item"><span style="color:#8b949e;">CVX:</span> <span style="color:#f0883e;">${p_cvx:,.2f}</span></div>
            <div class="ticker-item"><span style="color:#8b949e;">CRV:</span> <span style="color:#58a6ff;">${p_crv:,.3f}</span></div>
            <div class="ticker-item"><span style="color:#8b949e;">ETH:</span> <span style="color:#bc8cff;">${p_eth:,.0f}</span></div>
            <div class="ticker-item"><span style="color:#8b949e;">scrvUSD:</span> <span style="color:#3fb950;">$1.00 (~8.2% APY)</span></div>
            <div class="ticker-item"><span style="color:#8b949e;">GAS:</span> <span style="color:#e3b341;">{gas_gwei:.1f} Gwei</span></div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

# --- SIDEBAR: SIMULADOR DE CARTERA PERSONAL ---
st.sidebar.markdown("<h3 style='color:#f0f6fc;'>💼 Tu Posición vlCVX</h3>", unsafe_allow_html=True)
user_cvx = st.sidebar.number_input("Cantidad de CVX bloqueados:", min_value=0.0, value=2500.0, step=100.0)
lock_date = st.sidebar.date_input("Fecha en que firmaste el bloqueo:", value=datetime.today() - timedelta(days=35))
claim_pool_usd = st.sidebar.number_input("scrvUSD acumulado en The Union ($):", min_value=0.0, value=320.0, step=10.0)

# Cálculos de posición según la tesis de Dimitri
total_vecrv = user_cvx * 8.75 # 1 vlCVX comanda ~8.75 veCRV
unlock_date = datetime.combine(lock_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(weeks=16)
dias_restantes_lock = max((unlock_date - now).days, 0)
semanas_restantes_lock = dias_restantes_lock // 7
rondas_restantes = max(dias_restantes_lock // 14, 0)

# --- CUERPO PRINCIPAL (3 COLUMNAS) ---
col1, col2, col3 = st.columns(3)

# 1. RADAR DE RONDA Y SOBORNOS (BRIBES)
with col1:
    bribe_est_usd = 0.052 # Estimación de mercado $/vlCVX por ronda quincenal
    apr_estimado = ((bribe_est_usd * 26) / p_cvx) * 100 if p_cvx > 0 else 0
    
    st.markdown(f"""
        <div class="card-box">
            <div class="card-title">1. RELOJ & RETORNO DE RONDA</div>
            <div class="card-metric" style="color:#58a6ff;">{horas_restantes}h {minutos_restantes}m</div>
            <div class="card-sub">Cierre de ronda (Miércoles noche UTC)</div>
            <hr style="border:none; border-top:1px solid #232936; margin:14px 0;">
            <div style="font-size:14px; margin-bottom:6px;">
                <span style="color:#8b949e;">Rendimiento Real por Voto:</span> 
                <span style="font-weight:700; color:#ffffff;">${bribe_est_usd:.3f} / vlCVX</span>
            </div>
            <div style="font-size:14px;">
                <span style="color:#8b949e;">APR Real de Bribes:</span> 
                <span style="font-weight:700; color:#3fb950;">~{apr_estimado:.1f}% anual</span>
            </div>
            <div class="card-sub" style="margin-top:10px; font-size:11px;">
                ⚠️ Evita dilución: la mayoría vota en los últimos 30 min.
            </div>
        </div>
    """, unsafe_allow_html=True)

# 2. GESTOR DE DESBLOQUEOS (16 SEMANAS)
with col2:
    status_lock = "🟢 Bloqueo Activo (Rindiendo)" if dias_restantes_lock > 0 else "🔴 Lote Expirado (Listo para renovar)"
    st.markdown(f"""
        <div class="card-box">
            <div class="card-title">2. CICLO DE DESBLOQUEO (16S)</div>
            <div class="card-metric" style="color:#e3b341;">{semanas_restantes_lock} sem <span style="font-size:20px; color:#8b949e;">({dias_restantes_lock} días)</span></div>
            <div class="card-sub">{status_lock}</div>
            <hr style="border:none; border-top:1px solid #232936; margin:14px 0;">
            <div style="font-size:14px; margin-bottom:6px;">
                <span style="color:#8b949e;">Poder de control:</span> 
                <span style="font-weight:700; color:#bc8cff;">{total_vecrv:,.0f} veCRV equiv.</span>
            </div>
            <div style="font-size:14px;">
                <span style="color:#8b949e;">Rondas por cobrar en el ciclo:</span> 
                <span style="font-weight:700; color:#ffffff;">{rondas_restantes} rondas quincenales</span>
            </div>
            <div class="card-sub" style="margin-top:10px; font-size:11px;">
                Regla: 1 vlCVX = ~8.75 veCRV sin decaimiento temporal.
            </div>
        </div>
    """, unsafe_allow_html=True)

# 3. EL SEMÁFORO DE GAS Y COSECHA (THE UNION / MAINNET)
with col3:
    gas_units_claim = 140000
    coste_claim_eth = (gas_units_claim * (gas_gwei * 1e-9))
    coste_claim_usd = coste_claim_eth * p_eth
    
    pct_impacto = (coste_claim_usd / claim_pool_usd * 100) if claim_pool_usd > 0 else 100
    
    puede_cosechar = pct_impacto <= 2.5 and gas_gwei <= 15.0
    color_sem = "#3fb950" if puede_cosechar else "#f85149"
    txt_sem = "🟢 VENTANA ÓPTIMA DE CLAIM" if puede_cosechar else "🔴 PROHIBIDO COSECHAR (ACUMULA)"
    desc_sem = "El coste de red es inferior al 2.5%. Buen momento." if puede_cosechar else "El gas se come más del 2.5% de tus recompensas. Deja acumulando infinitamente."

    st.markdown(f"""
        <div class="card-box">
            <div class="card-title">3. EFICIENCIA DE COSECHA (THE UNION)</div>
            <div class="card-metric" style="color:{color_sem}; font-size:24px;">{txt_sem}</div>
            <div class="card-sub">{desc_sem}</div>
            <hr style="border:none; border-top:1px solid #232936; margin:14px 0;">
            <div style="font-size:14px; margin-bottom:6px;">
                <span style="color:#8b949e;">Coste de Claim estimado:</span> 
                <span style="font-weight:700; color:#ffffff;">${coste_claim_usd:.2f} ({coste_claim_eth:.4f} ETH)</span>
            </div>
            <div style="font-size:14px;">
                <span style="color:#8b949e;">Impacto sobre tu saldo:</span> 
                <span style="font-weight:700; color:{color_sem};">{pct_impacto:.2f}% de tu scrvUSD</span>
            </div>
            <div class="card-sub" style="margin-top:10px; font-size:11px;">
                Fiscalidad: No hay hecho imponible hasta que firmas el Claim.
            </div>
        </div>
    """, unsafe_allow_html=True)
