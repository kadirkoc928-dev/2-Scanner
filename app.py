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

st.set_page_config(page_title="TradeScanner Pro - 3100+ Aktien", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .stButton > button {
        width: 100%; background-color: #00ff88; color: black;
        font-weight: bold; border: none; padding: 15px; border-radius: 10px; font-size: 18px;
    }
    .stButton > button:hover { background-color: #00cc6a; }
</style>
""", unsafe_allow_html=True)

# SIDEBAR
st.sidebar.title("📊 TradeScanner Pro")
st.sidebar.info("S&P 500 + NASDAQ 100 + Russell 2000\n+ STOXX 600 + DEUTSCHLAND\n\n**3100+ Aktien**")

min_score = st.sidebar.slider("Min. Swing-Score:", 0, 100, 75)
min_volume = st.sidebar.number_input("Min. Volumen ($):", 0, 10000000000, 1000000, 500000)
min_price = st.sidebar.number_input("Min. Preis ($):", 0.0, 100000.0, 5.0)
max_price = st.sidebar.number_input("Max. Preis ($):", 0.0, 100000.0, 1000.0)
rsi_min = st.sidebar.slider("RSI Min:", 0, 100, 35)
rsi_max = st.sidebar.slider("RSI Max:", 0, 100, 70)
adx_min = st.sidebar.slider("ADX Min:", 0, 100, 20)
vol_ratio_min = st.sidebar.slider("Vol Ratio Min:", 0.5, 5.0, 1.0)

if st.sidebar.button("🗑️ Cache leeren"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption("⚠️ Keine Finanzberatung!")
st.sidebar.caption("⏱ ~20-35 Min für 3100+ Aktien")
st.sidebar.caption("📊 Yahoo Finance (verzögert)")

# TICKER-LISTEN (3100+)
@st.cache_data(ttl=86400)
def get_all_tickers():
    SP500 = ["A","AAL","AAPL","ABBV","ABNB","ABT","ACGL","ACN","ADBE","ADI","ADM","ADP","ADSK","AEE","AEP","AES","AFL","AIG","AIZ","AJG","AKAM","ALB","ALGN","ALK","ALL","ALLE","AMAT","AMCR","AMD","AME","AMGN","AMP","AMT","AMZN","ANET","ANSS","AON","AOS","APA","APD","APH","APTV","ARE","ATO","AVB","AVGO","AVY","AWK","AXP","AZO","BA","BAC","BALL","BAX","BBWI","BBY","BDX","BEN","BF.B","BG","BIIB","BIO","BK","BKNG","BKR","BLDR","BLK","BMY","BR","BRK.B","BRO","BSX","BWA","BXP","C","CAG","CAH","CARR","CAT","CB","CBOE","CBRE","CCI","CCL","CDNS","CDW","CE","CEG","CF","CFG","CHD","CHRW","CHTR","CI","CINF","CL","CLX","CMA","CMCSA","CME","CMG","CMI","CMS","CNC","CNP","COF","COO","COP","COR","COST","CPAY","CPB","CPRT","CPT","CRL","CRM","CSCO","CSGP","CSX","CTAS","CTLT","CTRA","CTSH","CTVA","CVS","CVX","CZR","D","DAL","DD","DE","DFS","DG","DGX","DHI","DHR","DIS","DLR","DLTR","DOV","DOW","DPZ","DRI","DTE","DUK","DVA","DVN","DXCM","EA","EBAY","ECL","ED","EFX","EIX","EL","ELV","EMN","EMR","ENPH","EOG","EPAM","EQIX","EQR","EQT","ES","ESS","ETN","ETR","ETSY","EVRG","EW","EXC","EXPD","EXPE","EXR","F","FANG","FAST","FCX","FDS","FDX","FE","FFIV","FICO","FIS","FITB","FMC","FOX","FOXA","FRT","FSLR","FTNT","FTV","GD","GE","GEHC","GEN","GILD","GIS","GL","GLW","GM","GNRC","GOOG","GOOGL","GPC","GPN","GRMN","GS","GWW","HAL","HAS","HBAN","HCA","HD","HES","HIG","HII","HLT","HOLX","HON","HPE","HPQ","HRL","HSIC","HST","HSY","HUBB","HUM","HWM","IBM","ICE","IDXX","IEX","IFF","ILMN","INCY","INTC","INTU","INVH","IP","IPG","IQV","IR","IRM","ISRG","IT","ITW","IVZ","J","JBHT","JBL","JCI","JKHY","JNJ","JNPR","JPM","K","KDP","KEY","KEYS","KHC","KIM","KLAC","KMB","KMI","KMX","KO","KR","KVUE","L","LDOS","LEN","LH","LHX","LIN","LKQ","LLY","LMT","LNC","LNT","LOW","LRCX","LULU","LUV","LVS","LW","LYB","LYV","MA","MAA","MAR","MAS","MCD","MCHP","MCK","MCO","MDLZ","MDT","MET","META","MGM","MHK","MKC","MLM","MMC","MMM","MNST","MO","MOH","MOS","MPC","MPWR","MRK","MRNA","MRO","MS","MSCI","MSFT","MSI","MTB","MTCH","MTD","MU","NCLH","NDAQ","NDSN","NEE","NEM","NFLX","NI","NKE","NOC","NOW","NRG","NSC","NTAP","NTRS","NUE","NVDA","NVR","NWL","NWS","NWSA","NXPI","O","ODFL","OKE","OMC","ON","ORCL","ORLY","OTIS","OXY","PANW","PARA","PAYC","PAYX","PCAR","PCG","PEG","PEP","PFE","PFG","PG","PGR","PH","PHM","PKG","PLD","PM","PNC","PNR","PNW","PODD","POOL","PPG","PPL","PRU","PSA","PSX","PTC","PWR","PYPL","QCOM","QRVO","RCL","REG","REGN","RF","RHI","RJF","RL","RMD","ROK","ROL","ROP","ROST","RSG","RTX","RVTY","SBAC","SBUX","SCHW","SHW","SJM","SLB","SMCI","SNA","SNPS","SO","SPG","SPGI","SRE","STE","STLD","STT","STX","STZ","SWK","SWKS","SYF","SYK","SYY","T","TAP","TDG","TDY","TECH","TEL","TER","TFC","TFX","TGT","TJX","TMO","TMUS","TPR","TRGP","TRMB","TROW","TRV","TSCO","TSLA","TSN","TT","TTWO","TXN","TXT","TYL","UA","UAL","UBER","UDR","UHS","ULTA","UNH","UNP","UPS","URI","USB","V","VFC","VICI","VLO","VLTO","VMC","VRSK","VRSN","VRTX","VTR","VTRS","VZ","WAB","WAT","WBA","WBD","WDC","WEC","WELL","WFC","WHR","WM","WMB","WMT","WRB","WST","WTW","WY","WYNN","XEL","XOM","XRAY","XYL","YUM","ZBH","ZBRA","ZION","ZTS"]
    
    NASDAQ100 = ["AAPL","ABNB","ADBE","ADI","ADP","ADSK","AEP","AMAT","AMD","AMGN","AMZN","ANSS","ASML","AVGO","AZN","BIIB","BKNG","BKR","CDNS","CDW","CEG","CHTR","CMCSA","COST","CPRT","CRWD","CSCO","CSGP","CSX","CTAS","CTSH","DASH","DDOG","DLTR","DXCM","EA","EBAY","EXC","FANG","FAST","FTNT","GEHC","GFS","GILD","GOOG","GOOGL","HON","IDXX","ILMN","INTC","INTU","ISRG","JD","KDP","KHC","KLAC","LRCX","LULU","MAR","MCHP","MDB","MDLZ","MELI","META","MNST","MRNA","MRVL","MSFT","MU","NFLX","NVDA","NXPI","ODFL","ON","ORLY","PANW","PAYX","PCAR","PDD","PEP","PYPL","QCOM","REGN","ROP","ROST","SBUX","SGEN","SIRI","SNPS","SPLK","SWKS","TEAM","TMUS","TSLA","TXN","VRSK","VRTX","WBA","WBD","WDAY","XEL","ZS"]
    
    RUSSELL = ["AAON","AAN","AAWW","ABCB","ABG","ABM","ABR","ACAD","ACCD","ACCO","ACEL","ACHC","ACIW","ACLS","ACMR","ACRE","ACT","ACVA","ADMA","ADNT","ADUS","AEIS","AEO","AGIO","AGM","AGNC","AGX","AHCO","AHH","AIRS","AIT","AIZ","AJRD","AKR","AL","ALEX","ALG","ALGT","ALHC","ALIT","ALK","ALKS","ALLO","ALPN","ALRM","ALSN","ALTR","AM","AMBA","AMBC","AMCX","AMED","AMK","AMKR","AMN","AMPH","AMPY","AMR","AMRC","AMRX","AMSC","AMSF","AMSWA","AMTB","AMWD","AN","ANAB","ANDE","ANF","ANGO","ANIP","ANNX","AORT","AOSL","APAM","APG","APLE","APLS","APO","APOG","APPF","APPN","APPS","AR","ARAY","ARCB","ARCH","ARCO","ARDX","ARI","ARIS","ARLO","AROC","ARR","ARRY","ARTNA","ARVN","ARW","ARWR","ASAN","ASB","ASGN","ASH","ASIX","ASLE","ASO","ASPN","ASTE","ATEC","ATEN","ATEX","ATGE","ATKR","ATR","ATRC","ATRI","ATRO","ATSG","ATUS","AUB","AUPH","AUR","AVA","AVAV","AVD","AVDX","AVNS","AVNT","AVNW","AVO","AVT","AVXL","AWR","AX","AXGN","AXL","AXNX","AXON","AXSM","AZEK","AZTA","AZZ","B","BANC","BAND","BANF","BANR","BARK","BASE","BBSI","BC","BCC","BCO","BCPC","BDC","BE","BEAM","BECN","BERY","BFH","BFS","BGCP","BGS","BGSF","BH","BHB","BHE","BHF","BHLB","BIG","BIGC","BILL","BIO","BIPC","BIVI","BJRI","BKD","BKE","BKH","BKU","BL","BLBD","BLDR","BLFS","BLKB","BLMN","BLNK","BMBL","BMEA","BMI","BMRC","BMRN","BMY","BNL","BOC","BOH","BOOM","BOOT","BORR","BOX","BPOP","BRBR","BRC","BRCC","BRKL","BRP","BRSP","BRT","BRX","BRY","BSIG","BSRR","BSVN","BTBT","BTU","BUSE","BV","BWA","BWXT","BXMT","BXP","BY","BYD","BYON","BZH","CABA","CAC","CADE","CAKE","CAL","CALM","CALX","CAMP","CAPL","CARA","CARG","CARR","CARS","CASH","CASS","CATC","CATO","CATY","CBAN","CBB","CBRE","CBT","CBU","CBZ","CC","CCBG","CCCS","CCF","CCNE","CCO","CCOI","CCRN","CCS","CD","CDE","CDLX","CDNA","CDP","CDRE","CDXS","CE","CECO","CEIX","CENT","CENTA","CENX","CEPU","CERE","CERT","CFB","CFFN","CFR","CG","CGEM","CGTX","CHCO","CHCT","CHE","CHEF","CHGG","CHH","CHMG","CHRD","CHRS","CHRW","CHTR","CHUY","CHWY","CHX","CIEN","CIM","CINF","CIR","CIVI","CIX","CLAR","CLB","CLBK","CLDT","CLDX","CLF","CLFD","CLH","CLNE","CLOV","CLPR","CLR","CLS","CLSK","CLVT","CLW","CM","CMA","CMBM","CMC","CMCO","CME","CMP","CMPR","CMRE","CMRX","CMS","CNA","CNC","CNDT","CNK","CNM","CNMD","CNNE","CNO","CNOB","CNS","CNSL","CNTY","CNX","CNXC","CNXN","COCO","CODI","COFS","COGT","COHN","COHU","COKE","COLB","COLD","COLL","COMM","COMP","COOK","COOP","CORT","COUR","CPE","CPF","CPK","CPRX","CPSI","CPSS","CR","CRAI","CRBG","CRBK","CRC","CRDO","CRGE","CRGY","CRI","CRK","CRL","CRM","CRMT","CRNC","CRNX","CRS","CRSP","CRSR","CRVL","CRWD","CS","CSGS","CSR","CSTL","CSTM","CSV","CSWC","CTBI","CTGO","CTKB","CTLP","CTLT","CTO","CTOS","CTRA","CTRE","CTRN","CTS","CTSH","CUBI","CUE","CUZ","CVBF","CVCO","CVE","CVGI","CVGW","CVI","CVLG","CVLT","CVNA","CVRX","CVT","CW","CWAN","CWH","CWK","CWST","CXM","CXW","CYBR","CYH","CYT","CYTH","CYTK","CZFS","CZNC","CZR","D","DAKT","DAL","DAN","DAR","DAVA","DBD","DBI","DBRG","DCBO","DCGO","DCO","DCOM","DDD","DEA","DEI","DEN","DENN","DFH","DFIN","DFS","DGICA","DGII","DHC","DHIL","DIN","DIOD","DISH","DK","DKS","DLB","DLHC","DLR","DLTH","DLX","DM","DMRC","DNB","DNLI","DNOW","DNUT","DOC","DOCN","DOCS","DOLE","DOMO","DOOR","DORM","DOUG","DOV","DOX","DRH","DRI","DRQ","DRVN","DSGN","DSGR","DSKE","DSP","DT","DTE","DTM","DUK","DUNE","DUOL","DV","DVA","DVAX","DVN","DX","DXC","DXCM","DXPE","DY","DYN","EAF","EAT","EB","EBC","EBF","EBS","ECPG","ECVT","EDIT","EE","EEFT","EEX","EFC","EFSC","EGAN","EGBN","EGHT","EGLE","EGP","EGRX","EGY","EHAB","EHC","EIG","EJH","ELAN","ELF","ELVN","EMBC","EME","EML","EMN","ENFN","ENOV","ENR","ENS","ENSG","ENTA","ENTG","ENV","ENVA","ENVB","ENZ","EOLS","EP","EPAC","EPC","EPM","EPR","EPRT","EQBK","EQC","EQH","EQT","ERAS","ERII","ERJ","ERM","ESAB","ESCA","ESE","ESGR","ESI","ESNT","ESPR","ESQ","ESRT","ESS","ESTA","ESTC","ESTE","ET","ETD","ETNB","ETRN","ETSY","ETWO","EURN","EVA","EVC","EVCM","EVER","EVEX","EVGO","EVH","EVLV","EVO","EVOP","EVRI","EVTC","EW","EWBC","EWCZ","EWTX","EXAS","EXC","EXEL","EXFY","EXK","EXLS","EXPD","EXPE","EXPI","EXPO","EXR","EXTR","EYE","EYEN","EYPT","F","FA","FARO","FAST","FATE","FBK","FBMS","FBNC","FBP","FBRT","FC","FCBC","FCEL","FCF","FCFS","FCN","FCX","FDP","FDUS","FE","FELE","FENC","FER","FF","FFBC","FFIC","FFIN","FFIV","FFWM","FG","FGBI","FHB","FHI","FHL","FHTX","FI","FIBK","FICO","FIGS","FINW","FIP","FIS","FISI","FITB","FIVE","FIVN","FIX","FIZZ","FL","FLGT","FLIC","FLL","FLNC","FLNG","FLR","FLS","FLT","FLWS","FLYW","FMAO","FMBH","FMC","FMNB","FMS","FMTX","FN","FNA","FNB","FND","FNF","FNKO","FNLC","FNV","FNWB","FOCS","FOLD","FOR","FORA","FORD","FORM","FORR","FOSL","FOUR","FOX","FOXA","FOXF","FPI","FR","FRA","FRAF","FRBA","FRBK","FRC","FREE","FREQ","FRG","FRGE","FRGI","FRHC","FROG","FRPH","FRPT","FRSH","FRST","FRSX","FRT","FSBC","FSBW","FSEA","FSFG","FSK","FSLR","FSM","FSP","FSS","FSTR","FT","FTAI","FTC","FTCI","FTDR","FTEK","FTFT","FTHM","FTK","FTNT","FTRE","FTS","FTV","FUBO","FUL","FULT","FUN","FUNC","FUSN","FUTU","FVCB","FVRR","FWONA","FWRD","FWRG","FXNC"]
    
    STOXX = ["ABBN.SW","ABI.BR","AC.PA","ACA.PA","ACKB.BR","ACS.MC","AD.AS","ADEN.SW","ADP.PA","ADS.DE","ADYEN.AS","AGN.AS","AGS.BR","AI.PA","AIR.PA","AKZA.AS","ALO.PA","ALV.DE","AM.PA","AMEAS.AS","AMS.SW","AMUN.PA","ANDR.VI","ANE.MC","AOF.DE","APAM.AS","ARGX.BR","ASML.AS","ATO.PA","AV.L","AVOL.SW","AVST.L","AXFO.ST","AZJ.L","BA.L","BALD.SW","BALN.SW","BAMI.MI","BANB.BR","BARN.SW","BAS.DE","BAYN.DE","BB.MC","BBVA.MC","BC8.DE","BEAN.SW","BEIJ.ST","BELG.BR","BEN.PA","BERY.L","BESI.AS","BHP.L","BIM.PA","BION.SW","BIRG.L","BKIA.MC","BKT.MC","BLND.L","BMPS.MI","BMW.DE","BN.PA","BNP.PA","BNZL.L","BOL.ST","BOSS.DE","BP.L","BPE.MI","BPER.MI","BRG.L","BRSN.SW","BT.L","BVI.PA","BWY.L","BYG.L","CABK.MC","CAP.PA","CARL-B.CO","CARR.PA","CBK.DE","CCEP","CDI.PA","CEM.MC","CHG.L","CIM.MC","CLN.SW","CLNX.MC","CNHI.MI","CO.PA","COB.BR","COLO.CO","CON.DE","COR.AS","CPG.L","CPR.MI","CRG.L","CRH.L","CRL.PA","CS.PA","CSN.MC","DANSKE.CO","DB1.DE","DBK.DE","DEME.BR","DG.PA","DIA.MC","DIM.PA","DKK.T","DLG.L","DMGT.L","DNORD.CO","DOM.L","DPH.L","DPW.DE","DSM.AS","DSV.CO","DTE.DE","DWNI.DE","EBS.VI","EDEN.PA","EDF.PA","EDP.LS","EDPR.LS","ELE.MC","ELI.BR","ELISA.HE","ELUX-B.ST","EMS.SW","EN.PA","ENEL.MI","ENG.MC","ENGI.PA","ENI.MI","ENR.DE","EOAN.DE","EPED.PA","EQNR.OL","ERF.PA","ERIC-B.ST","ESLO.B.ST","ESNT.L","ESSI.PA","ETL.PA","EUR.BR","EURN.BR","EVK.DE","EVT.DE","EXO.MI","EZJ.L","F.PA","FABG.ST","FBK.MI","FDR.MC","FER.MC","FGR.PA","FHZN.SW","FIE.DE","FLTR.L","FLU.PA","FME.DE","FORTUM.HE","FP.PA","FPE3.DE","FRA.DE","FRAG.DE","FRE.DE","FRES.L","FUR.AS","G.MI","G24.DE","GALP.LS","GAMA.L","GBLB.BR","GFC.PA","GIVN.SW","GJF.OL","GLEN.L","GLJ.DE","GLOG.MC","GN.CO","GNS.L","GRF.MC","GRG.L","GSK.L","GXI.DE","HABA.DE","HAFN.OL","HAL.L","HAR.L","HAS.L","HEI.DE","HEIA.AS","HEIO.AS","HER.IM","HFG.DE","HIK.L","HLE.DE","HLMA.L","HLN.L","HM-B.ST","HNR1.DE","HOOD.L","HOT.DE","HRPK.DE","HSBA.L","HUFV-A.ST","HUSQ-B.ST","IAG.L","IBE.MC","ICAD.PA","ICP.L","IDR.MC","IFX.DE","IGG.L","III.L","IMB.L","INCH.L","INDU-A.ST","INDU-C.ST","INF.L","INGA.AS","INPST.AS","INVE-B.ST","INW.MI","IPN.PA","IPS.MC","IRES.IR","ISP.MI","ITRK.L","ITV.L","ITX.MC","JD.L","JDEP.AS","JMAT.L","JMT.PA","JM.T","KBC.BR","KER.PA","KESKOB.HE","KINV-B.ST","KNEBV.HE","KNIN.SW","KOG.DE","KPN.AS","KRX.IR","KSP.L","LAND.L","LATO-B.ST","LEG.DE","LGEN.L","LI.PA","LIGHT.AS","LIN.DE","LISN.SW","LHA.DE","LLOY.L","LNE.MC","LOG.MC","LONN.SW","LOTB.BR","LR.PA","LSEG.L","LUNE.ST","LUVE.MI","LXS.DE","MAB.L","MAER-B.CO","MAN.DE","MAP.MC","MBG.DE","MC.PA","MCRO.L","MDO.L","MEL.MC","MER.L","MERY.PA","MF.PA","MGGT.L","MING.L","MITS.L","MNDI.L","MOL.PA","MONY.L","MOR.DE","MOWI.OL","MRK.DE","MRKS.L","MRO.L","MT.AS","MTX.DE","MUV2.DE","NA9.F","NAS.OL","NDA-SE.HE","NEL.OL","NEOEN.PA","NESN.SW","NESTE.HE","NEXI.MI","NG.L","NHY.OL","NIBE-B.ST","NK.PA","NKT.CO","NOD.OL","NOKIA.HE","NOVN.SW","NRE.MC","NTG.DE","NXT.L","OCI.AS","OMV.VI","ORA.PA","ORNBV.HE","OR.PA","ORK.OL","OUT1V.HE","P911.DE","PAH3.DE","PEAB-B.ST","PHIA.AS","PHNX.L","PLUS.L","PNDORA.CO","PNL.AS","POM.PA","POST.SW","PRU.L","PRY.MI","PSN.L","PSON.L","PUB.PA","PUM.DE","QIA.DE","RAA.DE","RAND.AS","RATO-B.ST","RB.L","RBI.VI","RCF.PA","RCO.PA","RCP.L","REC.MC","REL.L","RENE.L","REP.MC","RHM.DE","RI.PA","RNO.PA","ROCK-B.CO","ROG.SW","ROR.L","ROTH.SW","RRS.L","RR.L","RTO.L","RUI.PA","RWE.DE","RYA.L","SAB.MC","SAF.PA","SAGA.L","SALM.OL","SAMPO.HE","SAN.MC","SAND.ST","SAP.DE","SBRY.L","SCA-B.ST","SCHA.OL","SDF.DE","SEB.PA","SECU-B.ST","SESG.PA","SGE.L","SGO.PA","SGRO.L","SHB-A.ST","SHEL.L","SHL.DE","SIE.DE","SIGN.SW","SINCH.ST","SKA-B.ST","SKF-B.ST","SKG.L","SLHN.SW","SMDS.L","SMIN.L","SN.L","SOBI.ST","SOF.BR","SOLB.BR","SON.L","SOON.SW","SPIE.PA","SPM.MI","SPX.L","SQN.SW","SREN.SW","SRG.MI","SRS.MI","SSAB-A.ST","SSE.L","STAN.L","STERV.HE","STM.PA","STLA.PA","STMN.SW","STMP.PA","SU.PA","SWED-A.ST","SWMA.ST","SY1.DE","SYDB.CO","TALK.L","TATE.L","TEF.MC","TEG.DE","TELE2-B.ST","TEL.OL","TEL2-B.ST","TELIA.HE","TEMN.SW","TEN.MI","TEP.PA","TER.PA","TIE1V.HE","TIT.MI","TKAG.DE","TKWY.AS","TLGO.MC","TLX.DE","TNET.BR","TOP.CO","TRN.MI","TRYG.CO","TSCO.L","TTE.PA","TUI1.DE","TWEKA.HE","UBI.PA","UBSG.SW","UCB.BR","UHR.SW","ULE.MC","UMG.AS","UMI.BR","UNA.AS","UNI.MI","UPM.HE","URW.PA","UTDI.DE","VACN.SW","VALMT.HE","VANT.HE","VCT.PA","VIE.PA","VIG.VI","VK.PA","VOD.L","VOE.VI","VOLV-B.ST","VOW3.DE","VPK.AS","VWS.CO","WAC.DE","WCH.DE","WDP.BR","WHA.L","WIE.VI","WKL.AS","WLN.PA","WORL.PA","WRT1V.HE","YAR.OL","YIT.HE","ZAL.DE","ZURN.SW"]
    
    GERMAN = ["ADS.DE","AIR.DE","ALV.DE","BAS.DE","BAYN.DE","BMW.DE","BNR.DE","CBK.DE","CON.DE","DTE.DE","DBK.DE","DB1.DE","DPW.DE","DRW3.DE","EOAN.DE","FRE.DE","FME.DE","HEI.DE","HEN3.DE","IFX.DE","LIN.DE","MBG.DE","MRK.DE","MTX.DE","MUV2.DE","PAH3.DE","PUM.DE","QIA.DE","RWE.DE","SAP.DE","SIE.DE","SRT3.DE","VOW3.DE","VNA.DE","ZAL.DE","AIXA.DE","AT1.DE","BOSS.DE","EVT.DE","FRA.DE","G24.DE","HLE.DE","KGX.DE","LEG.DE","LHA.DE","LXS.DE","NDA.DE","OSR.DE","RAA.DE","SHA.DE","SY1.DE","TEG.DE","UTDI.DE","WAF.DE","AFX.DE","ARL.DE","BC8.DE","CE2.DE","DEQ.DE","DMP.DE","DUE.DE","DWS.DE","ELG.DE","FNTN.DE","FPE3.DE","G1A.DE","GBF.DE","GLJ.DE","HABA.DE","HOT.DE","HRPK.DE","ION.DE","JEN.DE","JUN3.DE","KCO.DE","KRN.DE","KSB.DE","KWS.DE","LPK.DE","MAN.DE","MLP.DE","MOR.DE","MUX.DE","NDX1.DE","NEM.DE","NOEJ.DE","NTG.DE","O2D.DE","PFV.DE","PSM.DE","RHM.DE","SAX.DE","SDF.DE","SFQ.DE","SGL.DE","SIX2.DE","SKB.DE","SMHN.DE","SPR.DE","SQZ.DE","STO3.DE","SZG.DE","TLX.DE","TTK.DE","VOS.DE","WAC.DE","WCH.DE","WSU.DE","ZIL2.DE"]
    
    all_tickers = SP500.copy()
    for t in NASDAQ100:
        if t not in all_tickers: all_tickers.append(t)
    for t in RUSSELL:
        if t not in all_tickers: all_tickers.append(t)
    for t in STOXX:
        if t not in all_tickers: all_tickers.append(t)
    for t in GERMAN:
        if t not in all_tickers: all_tickers.append(t)
    return all_tickers

# INDIKATOREN
def calc_indicators(df):
    if len(df) < 20: return None
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

def swing_score(df):
    if df is None or len(df) < 20: return 0
    try:
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        score = 0
        if pd.notna(latest.get('SMA_20')) and pd.notna(latest.get('SMA_50')):
            if latest['SMA_20'] > latest['SMA_50']: score += 15
            if latest['Close'] > latest['SMA_20']:
                score += 10
                d = (latest['Close'] - latest['SMA_20']) / latest['SMA_20'] * 100
                if 0 < d < 3: score += 5
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
            rsi_prev = prev.get('RSI', rsi)
            if 45 <= rsi
