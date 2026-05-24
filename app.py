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
</style>
""", unsafe_allow_html=True)

# ----------------------------------
# SIDEBAR
# ----------------------------------
st.sidebar.title("📊 TradeScanner Pro")
st.sidebar.markdown("---")
st.sidebar.subheader("🌍 Alle Märkte Scanner")
st.sidebar.info("""
**Eingebaute Märkte:**
- S&P 500 (503 Aktien)
- NASDAQ 100 (102 Aktien)
- Russell 2000 (500 Aktien)
- STOXX Europe 600 (200 Aktien)
- Deutsche Aktien (160 Aktien)

**Gesamt: ~1465 Aktien**
""")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Swing-Score Filter")
min_score = st.sidebar.slider("Minimum Swing-Score:", 0, 100, 75)
st.sidebar.caption("Nur Aktien mit Score >= diesem Wert")

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
st.sidebar.caption("⏱ Scan-Dauer: ~10-20 Minuten")
st.sidebar.caption("📊 Daten: Yahoo Finance (verzögert)")

# ----------------------------------
# EINGEBAUTE TICKER-LISTEN
# ----------------------------------

@st.cache_data(ttl=86400)
def get_all_tickers():
    """Alle Ticker als eingebaute Listen"""
    
    SP500 = [
        "A", "AAL", "AAPL", "ABBV", "ABNB", "ABT", "ACGL", "ACN", "ADBE", "ADI",
        "ADM", "ADP", "ADSK", "AEE", "AEP", "AES", "AFL", "AIG", "AIZ", "AJG",
        "AKAM", "ALB", "ALGN", "ALK", "ALL", "ALLE", "AMAT", "AMCR", "AMD", "AME",
        "AMGN", "AMP", "AMT", "AMZN", "ANET", "ANSS", "AON", "AOS", "APA", "APD",
        "APH", "APTV", "ARE", "ATO", "AVB", "AVGO", "AVY", "AWK", "AXP", "AZO",
        "BA", "BAC", "BALL", "BAX", "BBWI", "BBY", "BDX", "BEN", "BF.B", "BG",
        "BIIB", "BIO", "BK", "BKNG", "BKR", "BLDR", "BLK", "BMY", "BR", "BRK.B",
        "BRO", "BSX", "BWA", "BXP", "C", "CAG", "CAH", "CARR", "CAT", "CB",
        "CBOE", "CBRE", "CCI", "CCL", "CDNS", "CDW", "CE", "CEG", "CF", "CFG",
        "CHD", "CHRW", "CHTR", "CI", "CINF", "CL", "CLX", "CMA", "CMCSA", "CME",
        "CMG", "CMI", "CMS", "CNC", "CNP", "COF", "COO", "COP", "COR", "COST",
        "CPAY", "CPB", "CPRT", "CPT", "CRL", "CRM", "CSCO", "CSGP", "CSX", "CTAS",
        "CTLT", "CTRA", "CTSH", "CTVA", "CVS", "CVX", "CZR", "D", "DAL", "DD",
        "DE", "DFS", "DG", "DGX", "DHI", "DHR", "DIS", "DLR", "DLTR", "DOV",
        "DOW", "DPZ", "DRI", "DTE", "DUK", "DVA", "DVN", "DXCM", "EA", "EBAY",
        "ECL", "ED", "EFX", "EIX", "EL", "ELV", "EMN", "EMR", "ENPH", "EOG",
        "EPAM", "EQIX", "EQR", "EQT", "ES", "ESS", "ETN", "ETR", "ETSY", "EVRG",
        "EW", "EXC", "EXPD", "EXPE", "EXR", "F", "FANG", "FAST", "FCX", "FDS",
        "FDX", "FE", "FFIV", "FICO", "FIS", "FITB", "FMC", "FOX", "FOXA", "FRT",
        "FSLR", "FTNT", "FTV", "GD", "GE", "GEHC", "GEN", "GILD", "GIS", "GL",
        "GLW", "GM", "GNRC", "GOOG", "GOOGL", "GPC", "GPN", "GRMN", "GS", "GWW",
        "HAL", "HAS", "HBAN", "HCA", "HD", "HES", "HIG", "HII", "HLT", "HOLX",
        "HON", "HPE", "HPQ", "HRL", "HSIC", "HST", "HSY", "HUBB", "HUM", "HWM",
        "IBM", "ICE", "IDXX", "IEX", "IFF", "ILMN", "INCY", "INTC", "INTU", "INVH",
        "IP", "IPG", "IQV", "IR", "IRM", "ISRG", "IT", "ITW", "IVZ", "J",
        "JBHT", "JBL", "JCI", "JKHY", "JNJ", "JNPR", "JPM", "K", "KDP", "KEY",
        "KEYS", "KHC", "KIM", "KLAC", "KMB", "KMI", "KMX", "KO", "KR", "KVUE",
        "L", "LDOS", "LEN", "LH", "LHX", "LIN", "LKQ", "LLY", "LMT", "LNC",
        "LNT", "LOW", "LRCX", "LULU", "LUV", "LVS", "LW", "LYB", "LYV", "MA",
        "MAA", "MAR", "MAS", "MCD", "MCHP", "MCK", "MCO", "MDLZ", "MDT", "MET",
        "META", "MGM", "MHK", "MKC", "MLM", "MMC", "MMM", "MNST", "MO", "MOH",
        "MOS", "MPC", "MPWR", "MRK", "MRNA", "MRO", "MS", "MSCI", "MSFT", "MSI",
        "MTB", "MTCH", "MTD", "MU", "NCLH", "NDAQ", "NDSN", "NEE", "NEM", "NFLX",
        "NI", "NKE", "NOC", "NOW", "NRG", "NSC", "NTAP", "NTRS", "NUE", "NVDA",
        "NVR", "NWL", "NWS", "NWSA", "NXPI", "O", "ODFL", "OKE", "OMC", "ON",
        "ORCL", "ORLY", "OTIS", "OXY", "PANW", "PARA", "PAYC", "PAYX", "PCAR", "PCG",
        "PEG", "PEP", "PFE", "PFG", "PG", "PGR", "PH", "PHM", "PKG", "PLD",
        "PM", "PNC", "PNR", "PNW", "PODD", "POOL", "PPG", "PPL", "PRU", "PSA",
        "PSX", "PTC", "PWR", "PYPL", "QCOM", "QRVO", "RCL", "REG", "REGN", "RF",
        "RHI", "RJF", "RL", "RMD", "ROK", "ROL", "ROP", "ROST", "RSG", "RTX",
        "RVTY", "SBAC", "SBUX", "SCHW", "SHW", "SJM", "SLB", "SMCI", "SNA", "SNPS",
        "SO", "SPG", "SPGI", "SRE", "STE", "STLD", "STT", "STX", "STZ", "SWK",
        "SWKS", "SYF", "SYK", "SYY", "T", "TAP", "TDG", "TDY", "TECH", "TEL",
        "TER", "TFC", "TFX", "TGT", "TJX", "TMO", "TMUS", "TPR", "TRGP", "TRMB",
        "TROW", "TRV", "TSCO", "TSLA", "TSN", "TT", "TTWO", "TXN", "TXT", "TYL",
        "UA", "UAL", "UBER", "UDR", "UHS", "ULTA", "UNH", "UNP", "UPS", "URI",
        "USB", "V", "VFC", "VICI", "VLO", "VLTO", "VMC", "VRSK", "VRSN", "VRTX",
        "VTR", "VTRS", "VZ", "WAB", "WAT", "WBA", "WBD", "WDC", "WEC", "WELL",
        "WFC", "WHR", "WM", "WMB", "WMT", "WRB", "WST", "WTW", "WY", "WYNN",
        "XEL", "XOM", "XRAY", "XYL", "YUM", "ZBH", "ZBRA", "ZION", "ZTS"
    ]
    
    NASDAQ100 = [
        "AAPL", "ABNB", "ADBE", "ADI", "ADP", "ADSK", "AEP", "AMAT", "AMD", "AMGN",
        "AMZN", "ANSS", "ASML", "AVGO", "AZN", "BIIB", "BKNG", "BKR", "CDNS", "CDW",
        "CEG", "CHTR", "CMCSA", "COST", "CPRT", "CRWD", "CSCO", "CSGP", "CSX", "CTAS",
        "CTSH", "DASH", "DDOG", "DLTR", "DXCM", "EA", "EBAY", "EXC", "FANG", "FAST",
        "FTNT", "GEHC", "GFS", "GILD", "GOOG", "GOOGL", "HON", "IDXX", "ILMN", "INTC",
        "INTU", "ISRG", "JD", "KDP", "KHC", "KLAC", "LRCX", "LULU", "MAR", "MCHP",
        "MDB", "MDLZ", "MELI", "META", "MNST", "MRNA", "MRVL", "MSFT", "MU", "NFLX",
        "NVDA", "NXPI", "ODFL", "ON", "ORLY", "PANW", "PAYX", "PCAR", "PDD", "PEP",
        "PYPL", "QCOM", "REGN", "ROP", "ROST", "SBUX", "SGEN", "SIRI", "SNPS", "SPLK",
        "SWKS", "TEAM", "TMUS", "TSLA", "TXN", "VRSK", "VRTX", "WBA", "WBD", "WDAY",
        "XEL", "ZS"
    ]
    
    RUSSELL2000 = [
        "AAON", "ABCB", "ABG", "ABM", "ABR", "ACAD", "ACHC", "ACIW", "ACLS", "ACMR",
        "ADMA", "ADNT", "ADUS", "AEIS", "AEO", "AGIO", "AGM", "AGNC", "AGX", "AHCO",
        "AHH", "AIT", "AIZ", "AJRD", "AKR", "AL", "ALEX", "ALG", "ALGT", "ALHC",
        "ALIT", "ALK", "ALKS", "ALLO", "ALRM", "ALSN", "ALTR", "AM", "AMBA", "AMBC",
        "AMCX", "AMED", "AMK", "AMKR", "AMN", "AMPH", "AMR", "AMRC", "AMRX", "AMSC",
        "AMSF", "AMTB", "AMWD", "AN", "ANAB", "ANDE", "ANF", "ANGO", "ANIP",
        "AORT", "AOSL", "APAM", "APG", "APLE", "APLS", "APO", "APOG", "APPF",
        "APPN", "AR", "ARAY", "ARCB", "ARCH", "ARCO", "ARDX", "ARI", "ARIS",
        "ARLO", "AROC", "ARR", "ARRY", "ARVN", "ARW", "ARWR", "ASAN", "ASB",
        "ASGN", "ASH", "ASIX", "ASLE", "ASO", "ASPN", "ASTE", "ATEC", "ATEN",
        "ATGE", "ATKR", "ATR", "ATRC", "ATRI", "ATRO", "ATSG", "ATUS", "AUB", "AUPH",
        "AUR", "AVA", "AVAV", "AVD", "AVDX", "AVNS", "AVNT", "AVNW", "AVO", "AVT",
        "AVXL", "AWR", "AX", "AXGN", "AXL", "AXNX", "AXON", "AXSM", "AZEK", "AZTA",
        "AZZ", "B", "BANC", "BAND", "BANF", "BANR", "BARK", "BASE", "BBSI", "BC",
        "BCC", "BCO", "BCPC", "BDC", "BE", "BEAM", "BECN", "BERY", "BFH", "BFS",
        "BGCP", "BGS", "BH", "BHE", "BHF", "BHLB", "BIGC", "BILL", "BIO", "BIPC",
        "BJRI", "BKD", "BKE", "BKH", "BKU", "BL", "BLBD", "BLDR", "BLFS", "BLKB",
        "BLMN", "BMBL", "BMI", "BMRC", "BMRN", "BMY", "BNL", "BOC", "BOH", "BOOT",
        "BORR", "BOX", "BPOP", "BRBR", "BRC", "BRKL", "BRP", "BRSP", "BRT", "BRX",
        "BRY", "BSIG", "BSRR", "BTU", "BUSE", "BV", "BWA", "BWXT", "BXMT",
        "BXP", "BY", "BYD", "BZH", "CAC", "CADE", "CAKE", "CAL", "CALM", "CALX",
        "CARG", "CARR", "CARS", "CASH", "CASS", "CATC", "CATY", "CBAN", "CBRE", "CBT",
        "CBU", "CBZ", "CC", "CCBG", "CCCS", "CCNE", "CCO", "CCOI", "CCRN", "CCS",
        "CD", "CDE", "CDNA", "CDP", "CDRE", "CE", "CECO", "CEIX", "CENT", "CENTA",
        "CENX", "CERT", "CFB", "CFFN", "CFR", "CG", "CGEM", "CHCO", "CHCT", "CHE",
        "CHEF", "CHGG", "CHH", "CHMG", "CHRD", "CHRW", "CHTR", "CHUY", "CHWY", "CHX",
        "CIEN", "CIM", "CINF", "CIR", "CIVI", "CLB", "CLBK", "CLDT", "CLDX", "CLF",
        "CLFD", "CLH", "CLNE", "CLOV", "CLPR", "CLR", "CLS", "CLSK", "CLVT", "CLW",
        "CM", "CMA", "CMC", "CMCO", "CME", "CMP", "CMPR", "CMRE", "CMS", "CNA",
        "CNC", "CNDT", "CNK", "CNM", "CNMD", "CNNE", "CNO", "CNOB", "CNS", "CNSL",
        "CNTY", "CNX", "CNXC", "CNXN", "COCO", "CODI", "COHU", "COKE", "COLB",
        "COLD", "COLL", "COMM", "COMP", "COOK", "COOP", "CORT", "COUR", "CPE", "CPF",
        "CPK", "CPRX", "CR", "CRAI", "CRBG", "CRC", "CRDO", "CRGE", "CRGY", "CRI",
        "CRK", "CRL", "CRM", "CRMT", "CRNC", "CRNX", "CRS", "CRSP", "CRSR", "CRVL",
        "CRWD", "CSGS", "CSR", "CSTL", "CSTM", "CSV", "CSWC", "CTBI", "CTKB", "CTLP",
        "CTLT", "CTO", "CTOS", "CTRA", "CTRE", "CTRN", "CTS", "CTSH", "CUBI", "CUZ",
        "CVBF", "CVCO", "CVE", "CVGW", "CVI", "CVLG", "CVLT", "CVNA", "CW",
        "CWAN", "CWH", "CWK", "CWST", "CXM", "CXW", "CYBR", "CYH", "CYTK", "CZFS",
        "CZNC", "CZR", "D", "DAKT", "DAL", "DAN", "DAR", "DAVA", "DBD", "DBI",
        "DBRG", "DCBO", "DCGO", "DCO", "DCOM", "DDD", "DEA", "DEI", "DEN", "DENN",
        "DFH", "DFIN", "DFS", "DGICA", "DGII", "DHC", "DHIL", "DIN", "DIOD", "DISH",
        "DK", "DKS", "DLB", "DLHC", "DLR", "DLTH", "DLX", "DM", "DNB", "DNLI",
        "DNOW", "DNUT", "DOC", "DOCN", "DOCS", "DOLE", "DOMO", "DOOR", "DORM", "DOUG",
        "DOV", "DOX", "DRH", "DRI", "DRQ", "DRVN", "DSGR", "DSKE", "DT", "DTE",
        "DTM", "DUK", "DUOL", "DV", "DVA", "DVAX", "DVN", "DX", "DXC", "DXCM",
        "DXPE", "DY", "DYN"
    ]
    
    STOXX600 = [
        "ABBN.SW", "ABI.BR", "AD.AS", "ADS.DE", "ADYEN.AS", "AGN.AS", "AI.PA", "AIR.PA",
        "AKZA.AS", "ALO.PA", "ALV.DE", "AMS.SW", "ASML.AS", "BAS.DE", "BAYN.DE", "BBVA.MC",
        "BMW.DE", "BNP.PA", "BP.L", "CA.PA", "CAP.PA", "CARR.PA", "CS.PA", "DANSKE.CO",
        "DBK.DE", "DG.PA", "DPW.DE", "DSV.CO", "DTE.DE", "EL.PA", "ENEL.MI", "ENGI.PA",
        "EOAN.DE", "EQNR.OL", "ERIC-B.ST", "FLTR.L", "FP.PA", "FRE.DE", "G.MI", "GALP.LS",
        "GIVN.SW", "GLEN.L", "HEI.DE", "HEIO.AS", "HM-B.ST", "HSBA.L", "IBE.MC", "IFX.DE",
        "IMB.L", "INGA.AS", "ISP.MI", "ITX.MC", "KER.PA", "KNEBV.HE", "KPN.AS", "LGEN.L",
        "LIN.DE", "LLOY.L", "LONN.SW", "LR.PA", "MBG.DE", "MC.PA", "MOWI.OL", "MRK.DE",
        "MT.AS", "MUV2.DE", "NDA-SE.HE", "NESN.SW", "NOKIA.HE", "NOVN.SW", "ORA.PA", "OR.PA",
        "PHIA.AS", "PRU.L", "PSON.L", "PUB.PA", "RB.L", "REL.L", "REP.MC", "RI.PA",
        "RNO.PA", "ROG.SW", "RR.L", "SAF.PA", "SAN.MC", "SAP.DE", "SDF.DE", "SGO.PA",
        "SHEL.L", "SIE.DE", "SLHN.SW", "SMDS.L", "SN.L", "SREN.SW", "SSE.L", "STAN.L",
        "STM.PA", "STLA.PA", "SU.PA", "SWED-A.ST", "TEF.MC", "TEL.OL", "TEP.PA", "TSCO.L",
        "TTE.PA", "UBSG.SW", "UCB.BR", "UMG.AS", "UNA.AS", "URW.PA", "VOD.L", "VOW3.DE",
        "WKL.AS", "ZAL.DE", "ZURN.SW"
    ]
    
    GERMAN = [
        "ADS.DE", "AIR.DE", "ALV.DE", "BAS.DE", "BAYN.DE", "BMW.DE", "BNR.DE",
        "CBK.DE", "CON.DE", "DTE.DE", "DBK.DE", "DB1.DE", "DPW.DE", "DRW3.DE",
        "EOAN.DE", "FRE.DE", "FME.DE", "HEI.DE", "HEN3.DE", "IFX.DE", "LIN.DE",
        "MBG.DE", "MRK.DE", "MTX.DE", "MUV2.DE", "PAH3.DE", "PUM.DE", "QIA.DE",
        "RWE.DE", "SAP.DE", "SIE.DE", "SRT3.DE", "VOW3.DE", "VNA.DE", "ZAL.DE",
        "AIXA.DE", "AT1.DE", "BOSS.DE", "EVT.DE", "FRA.DE", "G24.DE", "HLE.DE",
        "KGX.DE", "LEG.DE", "LHA.DE", "LXS.DE", "NDA.DE", "OSR.DE", "RAA.DE",
        "SHA.DE", "SY1.DE", "TEG.DE", "UTDI.DE", "WAF.DE", "AFX.DE", "ARL.DE",
        "BC8.DE", "CE2.DE", "DEQ.DE", "DMP.DE", "DUE.DE", "DWS.DE", "ELG.DE",
        "FNTN.DE", "FPE3.DE", "G1A.DE", "GBF.DE", "GLJ.DE", "HABA.DE", "HOT.DE",
        "HRPK.DE", "ION.DE", "JEN.DE", "JUN3.DE", "KCO.DE", "KRN.DE", "KSB.DE",
        "KWS.DE", "LPK.DE", "MAN.DE", "MLP.DE", "MOR.DE", "MUX.DE", "NDX1.DE",
        "NEM.DE", "NOEJ.DE", "NTG.DE", "O2D.DE", "PFV.DE", "PSM.DE", "RHM.DE",
        "SAX.DE", "SDF.DE", "SFQ.DE", "SGL.DE", "SIX2.DE", "SKB.DE", "SMHN.DE",
        "SPR.DE", "SQZ.DE", "STO3.DE", "SZG.DE", "TLX.DE", "TTK.DE", "VOS.DE",
        "WAC.DE", "WCH.DE", "WSU.DE", "ZIL2.DE"
    ]
    
    all_tickers = []
    all_tickers.extend(SP500)
    all_tickers.extend([t for t in NASDAQ100 if t not in all_tickers])
    all_tickers.extend([t for t in RUSSELL2000 if t not in all_tickers])
    all_tickers.extend([t for t in STOXX600 if t not in all_tickers])
    all_tickers.extend([t for t in GERMAN if t not in all_tickers])
    
    return all_tickers

# ----------------------------------
# INDIKATOREN & SCORE
# ----------------------------------

def calculate_indicators(df):
    if len(df) < 20:
        return None
    try:
        df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
        df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
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
    if df is None or len(df) < 20:
        return 0
    try:
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        score = 0
        
        if pd.notna(latest.get('SMA_20')) and pd.notna(latest.get('SMA_50')):
            if latest['SMA_20'] > latest['SMA_50']:
                score += 15
            if latest['Close'] > latest['SMA_20']:
                score += 10
                distance = (latest['Close'] - latest['SMA_20']) / latest['SMA_20'] * 100
                if 0 < distance < 3:
                    score += 5
        
        if pd.notna(latest.get('ADX')):
            adx = latest['ADX']
            if adx > 50: score += 25
            elif adx > 40: score += 22
            elif adx > 35: score += 18
            elif adx > 30: score += 15
            elif adx > 25: score += 10
            elif adx > 20: score += 5
            else: score += 1
        
        if pd.notna(latest.get('RSI')):
            rsi = latest['RSI']
            rsi_prev = prev.get('RSI') if pd.notna(prev.get('RSI')) else rsi
            if 45 <= rsi <= 58: score += 20
            elif 40 <= rsi <= 65: score += 16
            elif 35 <= rsi <= 70: score += 10
            elif rsi < 35: score += 6
            elif rsi > 70: score += 4
            else: score += 2
            if rsi > rsi_prev: score += 2
        
        if pd.notna(latest.get('Volume_Ratio')):
            vr = latest['Volume_Ratio']
            if 1.3 <= vr <= 2.5: score += 15
            elif 1.1 <= vr <= 3.0: score += 12
            elif 0.9 <= vr <= 3.5: score += 8
            elif vr > 0.7: score += 4
            else: score += 1
        
        if pd.notna(latest.get('MACD')) and pd.notna(latest.get('MACD_signal')):
            if latest['MACD'] > latest['MACD_signal'] and latest['MACD'] > 0:
                score += 7
            elif latest['MACD'] > latest['MACD_signal']:
                score += 5
            elif latest['MACD'] > 0:
                score += 3
            macd_hist = latest.get('MACD_hist', 0)
            prev_hist = prev.get('MACD_hist', 0)
            if pd.notna(macd_hist) and pd.notna(prev_hist) and macd_hist > prev_hist:
                score += 3
        
        return min(100, score)
    except:
        return 0

def get_tradingview_link(ticker):
    ticker_upper = ticker.upper()
    if '.DE' in ticker_upper:
        exchange, clean = "XETR", ticker_upper.replace('.DE', '')
    elif '.L' in ticker_upper:
        exchange, clean = "LSE", ticker_upper.replace('.L', '')
    elif '.PA' in ticker_upper:
        exchange, clean = "EURONEXT", ticker_upper.replace('.PA', '')
    elif '.MI' in ticker_upper:
        exchange, clean = "MIL", ticker_upper.replace('.MI', '')
    elif '.SW' in ticker_upper:
        exchange, clean = "SWX", ticker_upper.replace('.SW', '')
    elif '.MC' in ticker_upper:
        exchange, clean = "BME", ticker_upper.replace('.MC', '')
    elif '.AS' in ticker_upper:
        exchange, clean = "EURONEXT", ticker_upper.replace('.AS', '')
    elif '.BR' in ticker_upper:
        exchange, clean = "EURONEXT", ticker_upper.replace('.BR', '')
    elif '.CO' in ticker_upper:
        exchange, clean = "OMXCOP", ticker_upper.replace('.CO', '')
    elif '.ST' in ticker_upper:
        exchange, clean = "OMXSTO", ticker_upper.replace('.ST', '')
    elif '.OL' in ticker_upper:
        exchange, clean = "OSE", ticker_upper.replace('.OL', '')
    elif '.HE' in ticker_upper:
        exchange, clean = "OMXHEX", ticker_upper.replace('.HE', '')
    elif '.LS' in ticker_upper:
        exchange, clean = "EURONEXT", ticker_upper.replace('.LS', '')
    else:
        exchange, clean = "NASDAQ", ticker_upper
    return f"https://www.tradingview.com/chart/?symbol={exchange}%3A{clean}&interval=D"

def scan_one_ticker(ticker):
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
            name = stock.info.get('shortName', tick
