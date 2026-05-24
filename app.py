import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import ta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import warnings
warnings.filterwarnings('ignore')

# ----------------------------------
# KONFIGURATION
# ----------------------------------
st.set_page_config(
    page_title="TradeScanner Pro - Alle Märkte",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        background-color: #00ff88;
        color: black;
        font-weight: bold;
        border: none;
        padding: 15px;
        border-radius: 10px;
        font-size: 18px;
    }
    .stButton > button:hover {
        background-color: #00cc6a;
    }
    .big-score {
        font-size: 60px;
        font-weight: bold;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------
# SIDEBAR
# ----------------------------------
st.sidebar.title("📊 TradeScanner Pro")
st.sidebar.markdown("---")
st.sidebar.subheader("🌍 Alle Märkte Scanner")
st.sidebar.info("""
**Märkte:**
- S&P 500 (500 Aktien)
- NASDAQ 100 (100 Aktien)
- Russell 2000 (2000 Aktien)
- STOXX Europe 600 (600 Aktien)

**Gesamt: ~3200 Aktien**
""")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Swing-Score Filter")

min_score = st.sidebar.slider("Minimum Swing-Score:", 0, 100, 75)
st.sidebar.caption("Nur Aktien mit Score ≥ diesem Wert")

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Zusätzliche Filter")

min_volume = st.sidebar.number_input("Min. Tagesvolumen ($):", 0, 10000000000, 1000000, 500000)
min_price = st.sidebar.number_input("Min. Preis ($):", 0.0, 100000.0, 5.0)
max_price = st.sidebar.number_input("Max. Preis ($):", 0.0, 100000.0, 1000.0)
rsi_min = st.sidebar.slider("RSI Minimum:", 0, 100, 35)
rsi_max = st.sidebar.slider("RSI Maximum:", 0, 100, 70)
adx_min = st.sidebar.slider("ADX Minimum:", 0, 100, 20)
vol_ratio_min = st.sidebar.slider("Volumen-Ratio Minimum:", 0.5, 5.0, 1.0)

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Cache leeren & neustarten"):
    st.cache_data.clear()
    st.success("Cache geleert!")
    time.sleep(1)
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("⚠️ Keine Finanzberatung!")
st.sidebar.caption("⏱ Scan-Dauer: 15-30 Min für 3200 Aktien")
st.sidebar.caption("📊 Daten: Yahoo Finance (verzögert)")

# ----------------------------------
# TICKER-LADEN (ALLE, OHNE KÜRZUNG)
# ----------------------------------

@st.cache_data(ttl=86400)  # 24 Stunden Cache
def load_all_tickers():
    """Lädt WIRKLICH ALLE Ticker ohne Kürzung"""
    all_tickers = []
    stats = {}
    
    # 1. S&P 500
    try:
        sp500_df = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
        sp500_tickers = sp500_df["Symbol"].tolist()
        sp500_tickers = [t.replace('.', '-').strip() for t in sp500_tickers if str(t).strip()]
        all_tickers.extend(sp500_tickers)
        stats['S&P 500'] = len(sp500_tickers)
    except Exception as e:
        stats['S&P 500'] = f"Fehler: {e}"
    
    # 2. NASDAQ 100
    try:
        nasdaq_tables = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")
        for t in nasdaq_tables:
            if "Ticker" in str(t.columns) or "Symbol" in str(t.columns):
                col_name = [c for c in t.columns if "Ticker" in str(c) or "Symbol" in str(c)][0]
                nasdaq_tickers = t[col_name].tolist()
                nasdaq_tickers = [str(t).replace('.', '-').strip() for t in nasdaq_tickers if str(t).strip() and str(t).lower() != 'nan']
                all_tickers.extend(nasdaq_tickers)
                stats['NASDAQ 100'] = len(nasdaq_tickers)
                break
    except Exception as e:
        stats['NASDAQ 100'] = f"Fehler: {e}"
    
    # 3. Russell 2000
    try:
        russell_url = "https://www.ishares.com/us/products/239710/ishares-russell-2000-etf/1467271812596.ajax?fileType=csv&fileName=IWM_holdings&dataType=fund"
        russell_df = pd.read_csv(russell_url, skiprows=9)
        if "Ticker" in russell_df.columns:
            russell_tickers = russell_df["Ticker"].dropna().tolist()
            russell_tickers = [str(t).strip() for t in russell_tickers if str(t).strip()]
            all_tickers.extend(russell_tickers)
            stats['Russell 2000'] = len(russell_tickers)
    except Exception as e:
        stats['Russell 2000'] = f"Fehler: {e}"
    
    # 4. STOXX Europe 600
    try:
        stoxx_tables = pd.read_html("https://en.wikipedia.org/wiki/STOXX_Europe_600")
        for t in stoxx_tables:
            cols = str(t.columns).lower()
            if "ticker" in cols or "symbol" in cols:
                first_col = t.columns[0]
                stoxx_tickers = t[first_col].tolist()
                stoxx_tickers = [str(t).strip() for t in stoxx_tickers if str(t).strip() and str(t).lower() != 'nan']
                all_tickers.extend(stoxx_tickers)
                stats['STOXX Europe 600'] = len(stoxx_tickers)
                break
    except Exception as e:
        stats['STOXX Europe 600'] = f"Fehler: {e}"
    
    # Duplikate entfernen
    all_unique = list(dict.fromkeys(all_tickers))
    all_unique = [t for t in all_unique if t and len(t) > 0 and str(t).lower() != 'nan']
    
    return all_unique, stats

# ----------------------------------
# INDIKATOREN & SCORE
# ----------------------------------

def calculate_indicators(df):
    """Berechnet alle Indikatoren"""
    if len(df) < 20:
        return None
    try:
        df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
        df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
        df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
        df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14)
        df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        df['MACD'] = ta.trend.macd(df['Close'])
        df['MACD_signal'] = ta.trend.macd_signal(df['Close'])
        df['MACD_hist'] = ta.trend.macd_diff(df['Close'])
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        return df
    except:
        return None

def calculate_swing_score(df):
    """Detaillierter Swing-Score 0-100"""
    if df is None or len(df) < 20:
        return 0
    
    try:
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        score = 0
        
        # === TREND (30 Punkte) ===
        trend_points = 0
        
        # SMA Alignment (15 Punkte)
        if pd.notna(latest.get('SMA_20')) and pd.notna(latest.get('SMA_50')) and pd.notna(latest.get('SMA_200')):
            if latest['SMA_20'] > latest['SMA_50'] > latest['SMA_200']:
                trend_points += 15
            elif latest['SMA_20'] > latest['SMA_50']:
                trend_points += 10
            elif latest['Close'] > latest['SMA_50']:
                trend_points += 5
        
        # Kurs über SMA20 (10 Punkte)
        if pd.notna(latest.get('SMA_20')):
            if latest['Close'] > latest['SMA_20']:
                trend_points += 7
                # Kurs nahe SMA20 (Pullback-Setup) = Bonus
                distance = (latest['Close'] - latest['SMA_20']) / latest['SMA_20'] * 100
                if 0 < distance < 3:
                    trend_points += 3
        
        # Höhere Hochs (5 Punkte)
        if len(df) >= 40:
            recent_high = df['High'].iloc[-20:].max()
            older_high = df['High'].iloc[-40:-20].max()
            if recent_high > older_high:
                trend_points += 5
        
        score += min(30, trend_points)
        
        # === MOMENTUM / ADX (25 Punkte) ===
        momentum_points = 0
        
        if pd.notna(latest.get('ADX')):
            adx = latest['ADX']
            if adx > 50: momentum_points += 25
            elif adx > 40: momentum_points += 22
            elif adx > 35: momentum_points += 18
            elif adx > 30: momentum_points += 15
            elif adx > 25: momentum_points += 10
            elif adx > 20: momentum_points += 5
            else: momentum_points += 1
        
        score += min(25, momentum_points)
        
        # === RSI (20 Punkte) ===
        rsi_points = 0
        
        if pd.notna(latest.get('RSI')):
            rsi = latest['RSI']
            rsi_prev = prev.get('RSI') if pd.notna(prev.get('RSI')) else rsi
            
            # Optimaler Long-Bereich
            if 45 <= rsi <= 58:
                rsi_points += 20
            elif 40 <= rsi <= 65:
                rsi_points += 16
            elif 35 <= rsi <= 70:
                rsi_points += 10
            elif rsi < 35:
                rsi_points += 6
            elif rsi > 70:
                rsi_points += 4
            else:
                rsi_points += 2
            
            # RSI steigend = Bonus
            if rsi > rsi_prev:
                rsi_points += 2
        
        score += min(20, rsi_points)
        
        # === VOLUMEN (15 Punkte) ===
        volume_points = 0
        
        if pd.notna(latest.get('Volume_Ratio')):
            vr = latest['Volume_Ratio']
            if 1.3 <= vr <= 2.5:
                volume_points += 15
            elif 1.1 <= vr <= 3.0:
                volume_points += 12
            elif 0.9 <= vr <= 3.5:
                volume_points += 8
            elif vr > 0.7:
                volume_points += 4
            else:
                volume_points += 1
        
        score += min(15, volume_points)
        
        # === MACD (10 Punkte) ===
        macd_points = 0
        
        if pd.notna(latest.get('MACD')) and pd.notna(latest.get('MACD_signal')):
            macd = latest['MACD']
            macd_sig = latest['MACD_signal']
            macd_hist = latest.get('MACD_hist', 0)
            
            if macd > macd_sig and macd > 0:
                macd_points += 7
            elif macd > macd_sig:
                macd_points += 5
            elif macd > 0:
                macd_points += 3
            
            # Histogramm steigend
            if pd.notna(macd_hist):
                prev_hist = prev.get('MACD_hist', 0) if pd.notna(prev.get('MACD_hist')) else 0
                if macd_hist > prev_hist:
                    macd_points += 3
        
        score += min(10, macd_points)
        
        return min(100, score)
    
    except:
        return 0

def get_tradingview_link(ticker):
    """TradingView Chart Link"""
    ticker_upper = ticker.upper()
    
    if '.DE' in ticker_upper:
        exchange = "XETR"
        clean = ticker_upper.replace('.DE', '')
    elif '.L' in ticker_upper:
        exchange = "LSE"
        clean = ticker_upper.replace('.L', '')
    elif '.PA' in ticker_upper:
        exchange = "EURONEXT"
        clean = ticker_upper.replace('.PA', '')
    elif '.MI' in ticker_upper:
        exchange = "MIL"
        clean = ticker_upper.replace('.MI', '')
    elif '.SW' in ticker_upper:
        exchange = "SWX"
        clean = ticker_upper.replace('.SW', '')
    else:
        exchange = "NASDAQ"
        clean = ticker_upper
    
    return f"https://www.tradingview.com/chart/?symbol={exchange}%3A{clean}&interval=D"

def scan_one_ticker(ticker):
    """Scannt EINEN Ticker"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="3mo", interval="1d")
        
        if df.empty or len(df) < 20:
            return None
        
        avg_vol = df['Volume'].tail(20).mean()
        price = df['Close'].iloc[-1]
        daily_volume_dollar = avg_vol * price
        
        if daily_volume_dollar < 500000:
            return None
        
        df = calculate_indicators(df)
        if df is None:
            return None
        
        score = calculate_swing_score(df)
        latest = df.iloc[-1]
        
        try:
            name = stock.info.get('shortName', ticker)
        except:
            name = ticker
        
        rsi = latest.get('RSI', 50)
        if pd.isna(rsi): rsi = 50
        
        adx = latest.get('ADX', 20)
        if pd.isna(adx): adx = 20
        
        vr = latest.get('Volume_Ratio', 1.0)
        if pd.isna(vr): vr = 1.0
        
        atr = latest.get('ATR', 0)
        if pd.isna(atr) or price == 0:
            atr_pct = 2.0
        else:
            atr_pct = (atr / price) * 100
        
        sma20 = latest.get('SMA_20')
        if pd.isna(sma20):
            sma_status = 'N/A'
        else:
            sma_status = 'Above' if price > sma20 else 'Below'
        
        macd = latest.get('MACD')
        macd_sig = latest.get('MACD_signal')
        if pd.isna(macd) or pd.isna(macd_sig):
            macd_status = 'N/A'
        else:
            macd_status = 'Bullish' if macd > macd_sig else 'Bearish'
        
        return {
            'Ticker': ticker,
            'Name': str(name)[:60],
            'Preis': round(price, 2),
            'Swing-Score': score,
            'RSI': round(rsi, 1),
            'ADX': round(adx, 1),
            'Vol Ratio': round(vr, 2),
            'ATR%': round(atr_pct, 2),
            'SMA20': sma_status,
            'MACD': macd_status,
            'Volumen': round(daily_volume_dollar, 0),
            'Chart': get_tradingview_link(ticker)
        }
    except:
        return None

# ----------------------------------
# HAUPTBEREICH
# ----------------------------------

st.title("🌍 Kompletter Markt-Scanner")
st.markdown("### Alle S&P 500 + NASDAQ 100 + Russell 2000 + STOXX Europe 600")
st.markdown("---")

# Lade Ticker beim Start
with st.spinner("🔄 Lade Ticker-Listen von Wikipedia & iShares..."):
    all_tickers, ticker_stats = load_all_tickers()

# Zeige Statistiken
st.success(f"✅ **{len(all_tickers):,} unique Ticker geladen!**")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("S&P 500", ticker_stats.get('S&P 500', 'N/A'))
with col2:
    st.metric("NASDAQ 100", ticker_stats.get('NASDAQ 100', 'N/A'))
with col3:
    st.metric("Russell 2000", ticker_stats.get('Russell 2000', 'N/A'))
with col4:
    st.metric("STOXX 600", ticker_stats.get('STOXX Europe 600', 'N/A'))

st.markdown("---")
st.markdown(f"**Filter:** Swing-Score ≥ {min_score} | Volumen ≥ ${min_volume:,} | Preis ${min_price}-${max_price} | RSI {rsi_min}-{rsi_max} | ADX ≥ {adx_min}")

# SCAN BUTTON
if st.button("🚀 ALLE AKTIEN SCANNEN (100%)", type="primary", use_container_width=True):
    
    st.markdown("---")
    st.subheader("🔄 Scan läuft...")
    st.caption(f"Scanne {len(all_tickers):,} Aktien - dies kann 15-30 Minuten dauern")
    
    # Fortschritts-Anzeige
    progress_bar = st.progress(0)
    status_text = st.empty()
    time_text = st.empty()
    
    results = []
    total = len(all_tickers)
    completed = 0
    start_time = time.time()
    
    # Paralleler Scan mit 25 Workern
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(scan_one_ticker, ticker): ticker for ticker in all_tickers}
        
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            
            if result is not None:
                results.append(result)
            
            # Update alle 50 Ticker
            if completed % 50 == 0 or completed == total:
                progress = completed / total
                progress_bar.progress(progress)
                
                elapsed = time.time() - start_time
                speed = completed / elapsed if elapsed > 0 else 0
                remaining = (total - completed) / speed if speed > 0 else 0
                
                status_text.text(f"✅ {completed:,}/{total:,} gescannt | 🎯 {len(results):,} Treffer")
                time_text.text(f"⏱ {elapsed:.0f}s | 🏃 {speed:.1f} Aktien/s | ⏳ Noch ~{remaining:.0f}s")
    
    progress_bar.empty()
    status_text.empty()
    time_text.empty()
    
    total_time = time.time() - start_time
    
    # Ergebnisse filtern
    if results:
        df_all = pd.DataFrame(results)
        
        # Filter anwenden
        df_filtered = df_all[
            (df_all['Swing-Score'] >= min_score) &
            (df_all['Volumen'] >= min_volume) &
            (df_all['Preis'] >= min_price) &
            (df_all['Preis'] <= max_price) &
            (df_all['RSI'] >= rsi_min) &
            (df_all['RSI'] <= rsi_max) &
            (df_all['ADX'] >= adx_min) &
            (df_all['Vol Ratio'] >= vol_ratio_min)
        ]
        
        df_filtered = df_filtered.sort_values('Swing-Score', ascending=False)
        
        # ERGEBNISSE
        st.markdown("---")
        st.subheader(f"🎯 {len(df_filtered):,} Aktien mit Score ≥ {min_score}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Gefilterte Treffer", f"{len(df_filtered):,}")
        with col2:
            st.metric("⏱ Gesamtzeit", f"{total_time:.0f}s ({total_time/60:.1f} Min)")
        with col3:
            best = df_filtered['Swing-Score'].max() if not df_filtered.empty else 0
            st.metric("🏆 Bester Score", f"{best}/100")
        with col4:
            avg = df_filtered['Swing-Score'].mean() if not df_filtered.empty else 0
            st.metric("📈 Durchschnitt", f"{avg:.0f}/100")
        
        st.caption(f"{len(df_all):,} Roh-Treffer → {len(df_filtered):,} nach Filtern")
        
        if not df_filtered.empty:
            # Score-Verteilung
            st.markdown("---")
            st.subheader("📊 Score-Verteilung")
            
            score_bins = [75, 80, 85, 90, 95, 100]
            score_labels = ['75-79', '80-84', '85-89', '90-94', '95-100']
            df_filtered['Score-Range'] = pd.cut(df_filtered['Swing-Score'], bins=score_bins, labels=score_labels)
            dist = df_filtered['Score-Range'].value_counts().sort_index()
            
            fig_dist = go.Figure(data=[go.Bar(
                x=dist.index, y=dist.values,
                marker_color=['#ffaa00', '#ffdd00', '#88ff00', '#44ff00', '#00ff88'],
                text=dist.values, textposition='auto'
            )])
            fig_dist.update_layout(height=250, template='plotly_dark', margin=dict(l=0,r=0,t=10,b=0),
                xaxis_title="Score-Bereich", yaxis_title="Anzahl")
            st.plotly_chart(fig_dist, use_container_width=True)
            
            # Tabelle
            st.markdown("---")
            st.subheader("📋 Alle Ergebnisse (📈 = TradingView Chart)")
            
            for i, (_, row) in enumerate(df_filtered.iterrows()):
                score = row['Swing-Score']
                
                if score >= 95:
                    emoji, color = "👑", "#ffd700"
                elif score >= 90:
                    emoji, color = "🌟", "#00ff88"
                elif score >= 85:
                    emoji, color = "✅", "#88ff00"
                elif score >= 80:
                    emoji, color = "👍", "#44ff00"
                else:
                    emoji, color = "📊", "#ffaa00"
                
                macd_color = "#00ff88" if row['MACD'] == 'Bullish' else "#ff4444" if row['MACD'] == 'Bearish' else "gray"
                
                cols = st.columns([0.6, 1.5, 0.8, 0.7, 0.7, 0.7, 0.7, 0.7])
                
                cols[0].markdown(f"<span style='color:{color};font-weight:bold;font-size:16px'>{emoji} {score}</span>", unsafe_allow_html=True)
                cols[1].markdown(f"**{row['Ticker']}**  \n*{row['Name'][:40]}*")
                cols[2].markdown(f"${row['Preis']:.2f}")
                cols[3].markdown(f"RSI {row['RSI']:.1f}")
                cols[4].markdown(f"ADX {row['ADX']:.1f}")
                cols[5].markdown(f"Vol {row['Vol Ratio']:.1f}x")
                cols[6].markdown(f"<span style='color:{macd_color};font-weight:bold'>{row['MACD']}</span>", unsafe_allow_html=True)
                cols[7].markdown(f"[📈 Chart]({row['Chart']})")
                
                if i < len(df_filtered) - 1:
                    st.divider()
            
            # CSV Download
            st.markdown("---")
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                f"📥 {len(df_filtered):,} Ergebnisse als CSV herunterladen",
                csv,
                f"alle_maerkte_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                'text/csv'
            )
            
            # Top 10 Detail-Ansicht
            st.markdown("---")
            st.subheader("🏆 Top 10 Swing-Trading Kandidaten")
            
            top10 = df_filtered.head(10)
            for i, (_, row) in enumerate(top10.iterrows()):
                with st.expander(
                    f"#{i+1} | {row['Ticker']} | Score: {row['Swing-Score']}/100 | ${row['Preis']:.2f}",
                    expanded=(i < 3)
                ):
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("Swing-Score", f"{row['Swing-Score']}/100")
                        st.metric("Preis", f"${row['Preis']:.2f}")
                    with c2:
                        st.metric("RSI", f"{row['RSI']:.1f}")
                        st.metric("ADX", f"{row['ADX']:.1f}")
                    with c3:
                        st.metric("ATR%", f"{row['ATR%']:.2f}%")
                        st.metric("Vol Ratio", f"{row['Vol Ratio']:.2f}x")
                    with c4:
                        st.metric("SMA20", row['SMA20'])
                        st.metric("MACD", row['MACD'])
                    
                    st.markdown(f"[📈 TradingView 1-Tages-Chart öffnen]({row['Chart']})")
                    
                    # Mini-Chart
                    try:
                        mini = yf.Ticker(row['Ticker']).history(period="1mo")
                        if not mini.empty and len(mini) > 5:
                            fig = go.Figure()
                            fig.add_trace(go.Candlestick(
                                x=mini.index, open=mini['Open'], high=mini['High'],
                                low=mini['Low'], close=mini['Close'],
                                increasing_line_color='#00ff88', decreasing_line_color='#ff4444',
                                showlegend=False
                            ))
                            sma = mini['Close'].rolling(20).mean()
                            fig.add_trace(go.Scatter(x=mini.index, y=sma, name='SMA20',
                                line=dict(color='orange', width=1), showlegend=False))
                            fig.update_layout(height=200, margin=dict(l=0,r=0,t=0,b=0),
                                template='plotly_dark', xaxis=dict(showticklabels=False),
                                yaxis=dict(showticklabels=False))
                            st.plotly_chart(fig, use_container_width=True)
                    except:
                        pass
        else:
            st.warning(f"⚠️ Keine Aktien mit Score ≥ {min_score} gefunden.")
            st.markdown("""
            **Versuche:**
            - Score auf 70+ senken
            - Volumen-Filter reduzieren
            - RSI-Bereich erweitern
            - ADX-Minimum senken
            - Andere Tageszeit (Yahoo-Limits)
            """)
    else:
        st.error("❌ Keine Ergebnisse! Yahoo Finance blockt möglicherweise.")
        st.info("Cache leeren & in 5 Minuten neu versuchen.")

st.markdown("---")
st.caption(f"⚠️ Keine Finanzberatung | Daten: Yahoo Finance (verzögert) | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
