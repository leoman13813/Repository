import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import yfinance as yf
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import time
import re
import base64

# ==========================================
# 網頁標題與狀態初始化 (加入分頁 LOGO)
# ==========================================
st.set_page_config(
    page_title="風暴眼 - 旗艦版", 
    page_icon="Gemini_Generated_Image_rmgi3urmgi3urmgi.png", # 瀏覽器分頁標籤圖示
    layout="wide"
)

# 聖家堂午後光影風格 CSS (載入思源黑體與思源宋體)
nordic_css = """
<style>
    /* 載入 Google Fonts: 思源黑體 (Noto Sans TC) 與 思源宋體 (Noto Serif TC) */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Noto+Serif+TC:wght@400;700;900&display=swap');

    /* 1. 聖家堂午後陽光漸層底色 & 全局內文預設思源宋體 */
    .stApp {
        background: linear-gradient(135deg, #FDFBF7 0%, #F5F0E6 100%);
        font-family: 'Noto Serif TC', "PingFang TC", "Microsoft JhengHei", serif;
    }

    /* 隱藏/透明化 Streamlit 頂部預設的白色 Header */
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* 2. 標題與文字顏色與字體劃分 */
    /* 標題層級：使用思源黑體 */
    h1, h2, h3, h4, h5, h6 {
        color: #2D3436;
        font-family: 'Noto Sans TC', "PingFang TC", "Microsoft JhengHei", sans-serif !important;
    }
    
    /* 內文層級：使用思源宋體 */
    p, span, div, li, th, td, label {
        color: #2D3436;
        font-family: 'Noto Serif TC', "PingFang TC", "Microsoft JhengHei", serif;
    }
    
    /* 3. 磨砂玻璃質感卡片 (Glassmorphism) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05) !important;
        padding: 1.5rem !important;
    }

    /* 4. 按鈕設計 (陽光漸層質感) - 介面按鈕維持黑體較為俐落 */
    .stButton > button {
        background: linear-gradient(90deg, #FCEAB8 0%, #F9D423 100%);
        color: #2D3436;
        font-family: 'Noto Sans TC', sans-serif !important;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s ease;
        padding: 0.4rem 1rem;
    }
    .stButton > button:hover {
        background: #F9D423;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* 定時快照與返回按鈕 (Primary按鈕) 專屬樣式：字體改為米白 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #4A6572 0%, #2F4858 100%);
        color: #FAF3E0; /* 修改為米白字體 */
    }
    .stButton > button[kind="primary"]:hover {
        background: #2F4858;
        color: #FFFFFF; /* 滑過時變為亮白，增加互動感 */
    }

    /* 5. 頁籤 Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 2px solid #E8E6E1;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 10px;
        padding-bottom: 10px;
        color: #8A8F95;
        font-family: 'Noto Sans TC', sans-serif !important; /* 頁籤標題使用黑體 */
        font-size: 1.1rem !important;
    }
    .stTabs [aria-selected="true"] {
        color: #4A6572 !important;
        border-bottom-color: #4A6572 !important;
        font-weight: bold;
    }

    /* 6. 輸入框與排版壓縮設定 */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] {
        border-radius: 6px;
        border: 1px solid #E8E6E1;
        background-color: rgba(255, 255, 255, 0.5);
    }
    
    /* 【排版壓縮】減少數值與文字輸入框的垂直佔用空間，讓左右兩排完美對齊 */
    .stNumberInput, .stTextInput { margin-bottom: -15px !important; }
    .stCheckbox { margin-bottom: -10px; }

    /* 7. 表格標題列 */
    th {
        background-color: rgba(247, 245, 240, 0.8) !important;
        color: #8A8F95 !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #E8E6E1 !important;
    }
    hr { border-top-color: #E8E6E1 !important; }
</style>
"""

st.markdown(nordic_css, unsafe_allow_html=True)

# 讀取 Logo 圖片並轉為 Base64 (用於與主標題文字並排顯示)
logo_path = "Gemini_Generated_Image_rmgi3urmgi3urmgi.png"
logo_html = ""
if os.path.exists(logo_path):
    with open(logo_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    # 利用 CSS background-size 放大並精準裁切中間的圓形，完美去掉黑邊
    logo_html = f'''
    <span style="
        display: inline-block; 
        width: 1.4em; 
        height: 1.4em; 
        background-image: url('data:image/png;base64,{encoded_string}'); 
        background-size: auto 170%; 
        background-position: center; 
        border-radius: 50%; 
        vertical-align: text-bottom; 
        margin-right: 12px; 
        margin-bottom: -4px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    "></span>
    '''

# 更新主標題：字體改為思源黑體 (Noto Sans TC)
st.markdown(f"<h2 style='text-align: left; font-family: \"Noto Sans TC\", sans-serif; color: #2F4858; letter-spacing: 4px; font-weight: 900; margin-top: -20px; margin-bottom: 20px;'>{logo_html}風暴眼</h2>", unsafe_allow_html=True)

# 初始化 Session State (與原始碼一致)
if 'selected_stock' not in st.session_state: st.session_state.selected_stock = None
if 'show_up' not in st.session_state: st.session_state.show_up = False
if 'show_dn' not in st.session_state: st.session_state.show_dn = False

# ==========================================
# 1. 靜態截圖引擎
# ==========================================
def save_strategy_image(df_up, df_dn, fetch_time, export_dir):
    try:
        if not os.path.exists(export_dir): os.makedirs(export_dir)
        # 繪圖時加入 Noto Sans TC 確保靜態快照字體也漂亮
        plt.rcParams['font.sans-serif'] = ['Noto Sans TC', 'Microsoft JhengHei', 'PingFang HK', 'Arial Unicode MS', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
        fig.patch.set_facecolor('#F7F5F0')
        fig.suptitle(f"風暴眼雙策略快照 | 擷取時間：{fetch_time}", fontsize=18, fontweight='bold', y=0.98, color='#2D3436')

        def draw_table(ax, df, title, title_color):
            ax.axis('off')
            ax.set_title(title, fontsize=15, color=title_color, pad=10, fontweight='bold')
            if df.empty:
                ax.text(0.5, 0.5, "此條件下無符合標的", ha='center', va='center', fontsize=12, color='#8A8F95')
                return
            df_plot = df.head(20).copy()
            if "Yahoo代號" in df_plot.columns: df_plot = df_plot.drop(columns=["Yahoo代號"])
            table_data = [df_plot.columns.tolist()] + df_plot.values.tolist()
            
            # 【優化】加入 colWidths 限制靜態圖表中表格的寬度，使其更為緊湊
            col_widths = [0.15, 0.22, 0.15, 0.15, 0.15] 
            table = ax.table(cellText=table_data, colWidths=col_widths, loc='center', cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.8) 
            for j in range(len(df_plot.columns)):
                cell = table[0, j]
                cell.set_text_props(weight='bold', color='#FFFFFF')
                cell.set_facecolor('#4A6572')

        # 更新靜態快照標題
        draw_table(ax1, df_up, "暴眼突圍術 (紅K)", '#D9736A')
        draw_table(ax2, df_dn, "暴眼定錨法 (黑K)", '#6B9080')

        plt.tight_layout()
        filename_time = fetch_time.replace(':', '').replace('-', '').replace(' ', '_')
        filepath = os.path.join(export_dir, f"Strategy_{filename_time}.png")
        plt.savefig(filepath, bbox_inches='tight', dpi=150)
        plt.close(fig)
        return os.path.abspath(filepath)
    except Exception as e: return None

# ==========================================
# 2. 資料爬蟲引擎
# ==========================================
def _safe_float(val):
    if not isinstance(val, str): return float(val)
    try:
        clean_val = val.replace(',', '').replace('%', '').replace('+', '').strip()
        if clean_val in ['-', '--', '無', '']: return 0.0
        return float(clean_val)
    except: return 0.0

def scrape_yahoo_table(symbol, endpoint, date_regex):
    clean_sym = symbol.replace('.TW', '').replace('.TWO', '')
    url = f"https://tw.stock.yahoo.com/quote/{clean_sym}/{endpoint}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        data, seen_parents = [], set()
        
        for text_node in soup.find_all(string=re.compile(date_regex)):
            parent = text_node.parent
            row_container = None
            for _ in range(4):
                if parent is None or parent.name == 'body': break
                if parent.name == 'li': row_container = parent; break
                if parent.name == 'div' and len(parent.find_all(['div', 'span'], recursive=False)) >= 4:
                    row_container = parent; break
                parent = parent.parent
            
            if row_container and id(row_container) not in seen_parents:
                seen_parents.add(id(row_container))
                texts = list(row_container.stripped_strings)
                merged, skip = [], False
                for i in range(len(texts)):
                    if skip: skip = False; continue
                    if texts[i] in ['+', '-'] and i + 1 < len(texts):
                        merged.append(texts[i] + texts[i+1]); skip = True
                    else: merged.append(texts[i])
                if len(merged) >= 4 and any(re.search(date_regex, t) for t in merged[:3]): data.append(merged)
        return data
    except Exception: return []

@st.cache_data(ttl=3600)
def get_revenue_data(symbol):
    raw_data = scrape_yahoo_table(symbol, "revenue", r'^\d{4}[-/]\d{2}$')
    data = []
    for row in raw_data:
        d_idx = next((i for i, t in enumerate(row) if re.search(r'^\d{4}[-/]\d{2}$', t)), None)
        if d_idx is not None and len(row) >= d_idx + 6:
            data.append({
                "月份": row[d_idx], "單月營收(千)": row[d_idx+1],
                "單月月增率": row[d_idx+2] + '%' if '%' not in row[d_idx+2] else row[d_idx+2],
                "單月年增率": row[d_idx+3] + '%' if '%' not in row[d_idx+3] else row[d_idx+3],
                "累計營收(千)": row[d_idx+4],
                "累計年增率": row[d_idx+5] + '%' if '%' not in row[d_idx+5] else row[d_idx+5]
            })
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def get_real_institutional_data(symbol):
    raw_data = scrape_yahoo_table(symbol, "institutional-trading", r'\d{2}[-/]\d{2}')
    parsed = []
    for row in raw_data:
        d_idx = next((i for i, t in enumerate(row) if re.search(r'\d{2}[-/]\d{2}', t)), None)
        if d_idx is not None:
            if len(row) >= d_idx + 10:
                parsed.append([row[d_idx], _safe_float(row[d_idx+1]), _safe_float(row[d_idx+2]), _safe_float(row[d_idx+3]), _safe_float(row[d_idx+4]), _safe_float(row[d_idx+5]), _safe_float(row[d_idx+6]), _safe_float(row[d_idx+7]), _safe_float(row[d_idx+8]), _safe_float(row[d_idx+9])])
            elif len(row) >= d_idx + 4:
                parsed.append([row[d_idx], 0.0, 0.0, _safe_float(row[d_idx+1]), 0.0, 0.0, _safe_float(row[d_idx+2]), 0.0, 0.0, _safe_float(row[d_idx+3])])
    if parsed:
        columns = pd.MultiIndex.from_tuples([('日期', ''), ('外資(張)', '買進'), ('外資(張)', '賣出'), ('外資(張)', '買賣超'), ('投信(張)', '買進'), ('投信(張)', '賣出'), ('投信(張)', '買賣超'), ('自營商(張)', '買進'), ('自營商(張)', '賣出'), ('自營商(張)', '買賣超')])
        return pd.DataFrame(parsed, columns=columns)
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_broker_trading_data(symbol):
    raw_data = scrape_yahoo_table(symbol, "broker-trading", r'\d{2}[-/]\d{2}')
    parsed = []
    for row in raw_data:
        d_idx = next((i for i, t in enumerate(row) if re.search(r'\d{2}[-/]\d{2}', t)), None)
        if d_idx is not None and len(row) >= d_idx + 6:
            parsed.append([row[d_idx], _safe_float(row[d_idx+1]), _safe_float(row[d_idx+2]), _safe_float(row[d_idx+3]), _safe_float(row[d_idx+4]), _safe_float(row[d_idx+5])])
    if parsed: return pd.DataFrame(parsed, columns=['日期', '主力買進', '主力賣出', '買賣超', '買進家數', '賣出家數'])
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_margin_data(symbol):
    raw_data = scrape_yahoo_table(symbol, "margin", r'\d{2}[-/]\d{2}')
    parsed = []
    for row in raw_data:
        d_idx = next((i for i, t in enumerate(row) if re.search(r'\d{2}[-/]\d{2}', t)), None)
        if d_idx is not None and len(row) >= d_idx + 9:
            parsed.append([row[d_idx], _safe_float(row[d_idx+1]), _safe_float(row[d_idx+2]), _safe_float(row[d_idx+3]), _safe_float(row[d_idx+4]), _safe_float(row[d_idx+5]), _safe_float(row[d_idx+6]), _safe_float(row[d_idx+7]), _safe_float(row[d_idx+8])])
    if parsed: return pd.DataFrame(parsed, columns=['日期', '融資買進', '融資賣出', '融資餘額', '融券買進', '融券賣出', '融券餘額', '資券互抵', '券資比'])
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_major_holders_data(symbol):
    raw_data = scrape_yahoo_table(symbol, "major-holders", r'\d{2}[-/]\d{2}|\d{8}')
    parsed = []
    for row in raw_data:
        d_idx = next((i for i, t in enumerate(row) if re.search(r'\d{2}[-/]\d{2}|\d{8}', t)), None)
        if d_idx is not None and len(row) >= d_idx + 5:
            while len(row) < d_idx + 6: row.append("0")
            parsed.append([row[d_idx], _safe_float(row[d_idx+1]), _safe_float(row[d_idx+2]), _safe_float(row[d_idx+3]), _safe_float(row[d_idx+4]), _safe_float(row[d_idx+5])])
    if parsed: return pd.DataFrame(parsed, columns=['統計日期', '收盤價', '400張以上(%)', '1000張以上(%)', '總股東人數', '內部人持股'])
    return pd.DataFrame()

# ==========================================
# 3. 本地化圖表控制面板與繪圖引擎
# ==========================================
def render_local_chart_controls(symbol, prefix="grid"):
    col_radio, col_spacer, col_setting = st.columns([5, 3, 4])
    
    with col_radio:
        c_type = st.radio("圖表模式", ["K線圖", "即時走勢"], horizontal=True, key=f"ctype_{prefix}_{symbol}", label_visibility="collapsed")
    
    if c_type == "K線圖":
        with col_setting:
            with st.popover("⚙️ 圖表設定", use_container_width=True):
                st.markdown("<div style='font-weight:bold; margin-bottom:5px; color:#4A6572;'>資料週期</div>", unsafe_allow_html=True)
                period = st.radio("週期", ["1M", "3M", "6M", "1Y"], index=1, horizontal=True, key=f"p_{prefix}_{symbol}", label_visibility="collapsed")
                
                st.divider()
                
                mas = st.multiselect("主圖指標", 
                                     ["MA5", "MA10", "MA20", "MA60", "Bollinger"], 
                                     default=["MA5", "MA10"], 
                                     key=f"ma_{prefix}_{symbol}")
                
                subs = st.multiselect("副圖指標 (最多3個)", 
                                      ["KD", "MACD", "RSI", "主力買賣超", "外資", "投信", "自營"], 
                                      default=[], 
                                      max_selections=3,
                                      key=f"subs_{prefix}_{symbol}")
                
        k_params = {
            'period': period, 
            'ma5': 'MA5' in mas, 
            'ma10': 'MA10' in mas, 
            'ma20': 'MA20' in mas, 
            'ma60': 'MA60' in mas, 
            'bbands': 'Bollinger' in mas
        }
        return "K線圖", k_params, subs
    else:
        return "即時走勢", {}, []

def calculate_indicators(hist):
    hist['MA5'], hist['MA10'] = hist['Close'].rolling(window=5).mean(), hist['Close'].rolling(window=10).mean()
    hist['MA20'], hist['MA60'] = hist['Close'].rolling(window=20).mean(), hist['Close'].rolling(window=60).mean()
    std20 = hist['Close'].rolling(window=20).std()
    hist['BB_UP'], hist['BB_DN'] = hist['MA20'] + 2 * std20, hist['MA20'] - 2 * std20

    low_min, high_max = hist['Low'].rolling(window=9).min(), hist['High'].rolling(window=9).max()
    hist['RSV'] = 100 * (hist['Close'] - low_min) / (high_max - low_min)
    hist['K'] = hist['RSV'].ewm(com=2, adjust=False).mean()
    hist['D'] = hist['K'].ewm(com=2, adjust=False).mean()

    exp1, exp2 = hist['Close'].ewm(span=12, adjust=False).mean(), hist['Close'].ewm(span=26, adjust=False).mean()
    hist['MACD'] = exp1 - exp2
    hist['Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
    hist['MACD_Hist'] = hist['MACD'] - hist['Signal']

    delta = hist['Close'].diff()
    gain, loss = delta.where(delta > 0, 0).rolling(window=14).mean(), -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    hist['RSI'] = 100 - (100 / (1 + rs))
    return hist

def build_ta_figure(stock, sym, name, open_price, chart_type, k_params, sub_indicators):
    if "K線" in chart_type:
        hist = stock.history(period="2y")
        if hist.empty: return None
        hist = calculate_indicators(hist)
        
        needs_chip = any(ind in sub_indicators for ind in ["外資", "投信", "自營", "主力買賣超"])
        if needs_chip:
            chip_df = get_real_institutional_data(sym)
            broker_df = get_broker_trading_data(sym)
            
            hist['Date_Col'] = hist.index
            hist['Date_str'] = hist['Date_Col'].dt.strftime('%m/%d')
            
            if not chip_df.empty:
                new_cols = []
                for col in chip_df.columns.values:
                    if isinstance(col, tuple): new_cols.append('_'.join(col).strip('_') if col[1] else col[0])
                    else: new_cols.append(col)
                chip_df.columns = new_cols
                
                if '日期' in chip_df.columns and '外資(張)_買賣超' in chip_df.columns:
                    chip_subset = chip_df[['日期', '外資(張)_買賣超', '投信(張)_買賣超', '自營商(張)_買賣超']].copy()
                    chip_subset.columns = ['Date_str', '外資', '投信', '自營']
                    hist = hist.merge(chip_subset, on='Date_str', how='left')
                else:
                    for c in ["外資", "投信", "自營"]: hist[c] = 0.0
            else:
                for c in ["外資", "投信", "自營"]: hist[c] = 0.0
                
            if not broker_df.empty and '日期' in broker_df.columns and '買賣超' in broker_df.columns:
                broker_subset = broker_df[['日期', '買賣超']].copy()
                broker_subset.columns = ['Date_str', '主力買賣超']
                hist = hist.merge(broker_subset, on='Date_str', how='left')
            else:
                hist['主力買賣超'] = 0.0
                
            hist.index = hist['Date_Col']
            hist.fillna(0, inplace=True)

        days_map = {"1M": 22, "3M": 65, "6M": 130, "1Y": 260}
        days = days_map.get(k_params.get('period', '3M'), 65)
        plot_df = hist.tail(days)

        active_subs = [ind for ind in sub_indicators if ind in ["KD", "MACD", "RSI", "主力買賣超", "外資", "投信", "自營"]]
        
        num_subplots = 1 + len(active_subs)
        row_heights = [0.6] + [0.4 / num_subplots] * num_subplots if num_subplots > 1 else [0.7, 0.3]
        fig = make_subplots(rows=num_subplots + 1, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=row_heights)

        increasing_color = '#EB5554'
        decreasing_color = '#47B262'

        fig.add_trace(go.Candlestick(
            x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name='K線',
            increasing=dict(line=dict(color=increasing_color), fillcolor=increasing_color),
            decreasing=dict(line=dict(color=decreasing_color), fillcolor=decreasing_color)
        ), row=1, col=1)
        
        if k_params.get('ma5'): fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA5'], line=dict(color='#E1B16A', width=1.5), name='MA5'), row=1, col=1)
        if k_params.get('ma10'): fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA10'], line=dict(color='#7882A4', width=1.5), name='MA10'), row=1, col=1)
        if k_params.get('ma20'): fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA20'], line=dict(color='#4A6572', width=1.5), name='MA20'), row=1, col=1)
        if k_params.get('ma60'): fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA60'], line=dict(color='#9B59B6', width=1.5), name='MA60'), row=1, col=1)
        if k_params.get('bbands'):
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['BB_UP'], line=dict(color='rgba(74, 101, 114, 0.4)', width=1, dash='dot'), name='BB上'), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['BB_DN'], fill='tonexty', fillcolor='rgba(74, 101, 114, 0.05)', line=dict(color='rgba(74, 101, 114, 0.4)', width=1, dash='dot'), name='BB下'), row=1, col=1)

        colors = [increasing_color if r['Close'] >= r['Open'] else decreasing_color for _, r in plot_df.iterrows()]
        fig.add_trace(go.Bar(x=plot_df.index, y=plot_df['Volume'], marker_color=colors, name='成交量'), row=2, col=1)

        curr_r = 3
        for ind in active_subs:
            if ind == "KD":
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['K'], line=dict(color='#4A6572', width=1.5), name='K'), row=curr_r, col=1)
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['D'], line=dict(color='#E1B16A', width=1.5), name='D'), row=curr_r, col=1)
            elif ind == "MACD":
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MACD'], line=dict(color='#4A6572', width=1.5), name='DIF'), row=curr_r, col=1)
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['Signal'], line=dict(color='#E1B16A', width=1.5), name='MACD'), row=curr_r, col=1)
                macd_colors = [increasing_color if val >= 0 else decreasing_color for val in plot_df['MACD_Hist']]
                fig.add_trace(go.Bar(x=plot_df.index, y=plot_df['MACD_Hist'], marker_color=macd_colors, name='OSC'), row=curr_r, col=1)
            elif ind == "RSI":
                fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['RSI'], line=dict(color='#7882A4', width=1.5), name='RSI'), row=curr_r, col=1)
                fig.add_hline(y=70, line_dash="dot", line_color="#E8E6E1", row=curr_r, col=1)
                fig.add_hline(y=30, line_dash="dot", line_color="#E8E6E1", row=curr_r, col=1)
            elif ind in ["主力買賣超", "外資", "投信", "自營"]:
                if ind in plot_df.columns:
                    chip_colors = [increasing_color if val >= 0 else decreasing_color for val in plot_df[ind]]
                    fig.add_trace(go.Bar(x=plot_df.index, y=plot_df[ind], marker_color=chip_colors, name=ind), row=curr_r, col=1)
            curr_r += 1

        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
        
        dynamic_height = 280 + (len(active_subs) * 120)
        fig.update_layout(
            height=dynamic_height, margin=dict(l=10, r=10, t=10, b=10),
            xaxis_rangeslider_visible=False, showlegend=False, 
            plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
            xaxis=dict(showline=True, linewidth=1, linecolor='#F0EEE9', mirror=True, gridcolor='#F7F5F0')
        )
        for r in range(1, num_subplots + 2): 
            fig.update_yaxes(showline=True, linewidth=1, linecolor='#F0EEE9', mirror=True, gridcolor='#F7F5F0', row=r, col=1)
        return fig
    else:
        intra = stock.history(period="1d", interval="1m")
        if intra.empty: return None
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=intra.index, y=intra['Close'], mode='lines', name='走勢', line=dict(color='#4A6572', width=2), fill='tozeroy', fillcolor='rgba(74, 101, 114, 0.1)'))
        if open_price > 0:
            fig.add_hline(y=open_price, line_dash="dash", line_color="#E1B16A", line_width=2, annotation_text=f"開盤: {open_price}", annotation_position="bottom right")
        last_date_str = intra.index[-1].strftime("%Y-%m-%d")
        fig.update_xaxes(range=[f"{last_date_str} 09:00:00", f"{last_date_str} 13:30:00"], showline=True, linewidth=1, linecolor='#F0EEE9', mirror=True, gridcolor='#F7F5F0')
        y_min, y_max = min(intra['Close'].min(), open_price) * 0.99, max(intra['Close'].max(), open_price) * 1.01
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF', yaxis=dict(showline=True, linewidth=1, linecolor='#F0EEE9', mirror=True, gridcolor='#F7F5F0', range=[y_min, y_max]))
        return fig

# ==========================================
# 4. 個股深度分析面板
# ==========================================
def render_stock_detail(row):
    sym, clean_sym, name, open_price = row['Yahoo代號'], row['Yahoo代號'].replace('.TW', '').replace('.TWO', ''), row['名稱'], row['開盤價']
    
    with st.container(border=True):
        st.markdown(f"### {name} ({clean_sym}) 詳細數據看板")
        tab_ta, tab_rev, tab_chips = st.tabs(["圖表分析", "營收資料", "籌碼分佈"])
        
        with tab_ta:
            c_type, k_params, subs = render_local_chart_controls(sym, prefix="detail")
            with st.spinner("繪製圖表中..."):
                stock = yf.Ticker(sym)
                fig = build_ta_figure(stock, sym, name, open_price, c_type, k_params, subs)
                if fig: st.plotly_chart(fig, use_container_width=True)

        with tab_rev:
            with st.spinner("載入營收資料..."):
                df_rev = get_revenue_data(sym)
                if not df_rev.empty:
                    rev_values = [float(str(v).replace(',', '')) for v in df_rev['單月營收(千)']]
                    fig_rev = go.Figure(data=[go.Bar(x=df_rev['月份'], y=rev_values, marker_color='#4A6572')])
                    fig_rev.update_layout(title=dict(text="近一年單月營收趨勢", font=dict(color='#2D3436')), height=300, margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF', xaxis=dict(showline=True, linewidth=1, linecolor='#F0EEE9', mirror=True), yaxis=dict(showline=True, linewidth=1, linecolor='#F0EEE9', mirror=True, gridcolor='#F7F5F0'))
                    st.plotly_chart(fig_rev, use_container_width=True)
                    st.dataframe(df_rev, use_container_width=True)
                else: st.info("查無營收資料")

        with tab_chips:
            df_chips = get_real_institutional_data(sym)
            if not df_chips.empty:
                fi_today, fi_5d = df_chips.iloc[0][('外資(張)', '買賣超')], df_chips.head(5)[('外資(張)', '買賣超')].sum()
                it_today, it_5d = df_chips.iloc[0][('投信(張)', '買賣超')], df_chips.head(5)[('投信(張)', '買賣超')].sum()
                def get_color(val): return "#EB5554" if val > 0 else "#47B262"
                def get_sign(val): return "+" if val > 0 else ""

                st.markdown(f"""
                <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                    <div style="flex: 1; border: 1px solid #F0EEE9; padding: 15px; border-radius: 8px; background-color: #FAFAFA;">
                        <div style="font-size: 13px; color: #8A8F95;">外資今日</div><div style="font-size: 20px; font-weight: bold; color: {get_color(fi_today)};">{get_sign(fi_today)}{int(fi_today):,}</div>
                    </div>
                    <div style="flex: 1; border: 1px solid #F0EEE9; padding: 15px; border-radius: 8px; background-color: #FAFAFA;">
                        <div style="font-size: 13px; color: #8A8F95;">外資 5 日</div><div style="font-size: 20px; font-weight: bold; color: {get_color(fi_5d)};">{get_sign(fi_5d)}{int(fi_5d):,}</div>
                    </div>
                    <div style="flex: 1; border: 1px solid #F0EEE9; padding: 15px; border-radius: 8px; background-color: #FAFAFA;">
                        <div style="font-size: 13px; color: #8A8F95;">投信今日</div><div style="font-size: 20px; font-weight: bold; color: {get_color(it_today)};">{get_sign(it_today)}{int(it_today):,}</div>
                    </div>
                    <div style="flex: 1; border: 1px solid #F0EEE9; padding: 15px; border-radius: 8px; background-color: #FAFAFA;">
                        <div style="font-size: 13px; color: #8A8F95;">投信 5 日</div><div style="font-size: 20px; font-weight: bold; color: {get_color(it_5d)};">{get_sign(it_5d)}{int(it_5d):,}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            sub_tabs = st.tabs(["三大法人", "主力進出", "資券變化", "大戶資料"])
            with sub_tabs[0]:
                if not df_chips.empty:
                    df_plot_chips = df_chips.head(30).sort_values(by=('日期', ''), ascending=True)
                    fig_chip = go.Figure()
                    fig_chip.add_trace(go.Bar(x=df_plot_chips[('日期', '')], y=df_plot_chips[('外資(張)', '買賣超')], name='外資', marker_color='#4A6572'))
                    fig_chip.add_trace(go.Bar(x=df_plot_chips[('日期', '')], y=df_plot_chips[('投信(張)', '買賣超')], name='投信', marker_color='#E1B16A'))
                    fig_chip.add_trace(go.Bar(x=df_plot_chips[('日期', '')], y=df_plot_chips[('自營商(張)', '買賣超')], name='自營商', marker_color='#47B262'))
                    fig_chip.update_layout(barmode='relative', height=300, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color='#8A8F95')), xaxis=dict(showline=True, linewidth=1, linecolor='#F0EEE9', mirror=True, tickangle=45), yaxis=dict(showline=True, linewidth=1, linecolor='#F0EEE9', mirror=True, gridcolor='#F7F5F0', zeroline=True, zerolinewidth=1, zerolinecolor='#E8E6E1'))
                    st.plotly_chart(fig_chip, use_container_width=True)
                    
                    def style_net_buy(val): return f"color: {'#EB5554' if val > 0 else '#47B262' if val < 0 else '#2D3436'}; font-weight: bold;" if isinstance(val, (int, float)) else ''
                    styled_df = df_chips.style.format(precision=0, thousands=",").applymap(style_net_buy, subset=[('外資(張)', '買賣超'), ('投信(張)', '買賣超'), ('自營商(張)', '買賣超')])
                    st.dataframe(styled_df, use_container_width=True, height=350)
            
            with sub_tabs[1]:
                df_broker = get_broker_trading_data(sym)
                if not df_broker.empty: st.dataframe(df_broker, use_container_width=True, height=450)
            with sub_tabs[2]:
                df_margin = get_margin_data(sym)
                if not df_margin.empty: st.dataframe(df_margin, use_container_width=True, height=450)
            with sub_tabs[3]:
                df_major = get_major_holders_data(sym)
                if not df_major.empty: st.dataframe(df_major, use_container_width=True, height=450)

def draw_overview_grid(df, limit):
    if df.empty: return
    df_plot = df.head(limit)
    st.markdown(f"##### 選股圖表總覽 (顯示前 {len(df_plot)} 檔)")
    cols = st.columns(3)
    for i, (_, row) in enumerate(df_plot.iterrows()):
        sym, name, open_price = row['Yahoo代號'], row['名稱'], row['開盤價']
        clean_sym = sym.replace('.TW', '').replace('.TWO', '')
        with cols[i % 3]:
            with st.container(border=True):
                if st.button(f"{name} ({clean_sym})", key=f"btn_{sym}", use_container_width=True):
                    st.session_state.selected_stock = row.to_dict()
                    st.rerun()
                
                c_type, k_params, subs = render_local_chart_controls(sym, prefix="grid")
                
                stock = yf.Ticker(sym)
                fig = build_ta_figure(stock, sym, name, open_price, c_type, k_params, subs)
                if fig: st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 5. 市場資料總抓取模組
# ==========================================
@st.cache_data(ttl=60)
def get_market_data():
    url = "https://tw.stock.yahoo.com/rank/turnover"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        rows = soup.find_all("li", class_=re.compile(r"List\(n\)", re.I))
        if not rows: rows = soup.find_all("li")
            
        data, yahoo_symbols = [], []
        for rank, row in enumerate(rows, 1):
            name_tag, symbol_tag = row.find("div", class_="Lh(20px)"), row.find("span", class_="Fz(14px)")
            if not name_tag or not symbol_tag: continue 
            name, raw_symbol = name_tag.text.strip(), symbol_tag.text.strip()
            clean_symbol = raw_symbol.replace(".TW", "").replace(".TWO", "")
            
            cols = row.find_all("div", class_="Fxg(1)")
            if len(cols) >= 5:
                price_str = cols[0].text.replace(",", "")
                change_pct_str = cols[2].text.replace("%", "").replace("+", "")
                price = float(price_str) if price_str.replace(".", "").isdigit() else 0.0
                try: change_pct = float(change_pct_str)
                except ValueError: change_pct = 0.0
                
                yahoo_symbols.append(raw_symbol)
                data.append({"代號": clean_symbol, "名稱": name, "當前價": price, "開盤價": 0.0, "漲跌幅(%)": change_pct, "Yahoo代號": raw_symbol})
        
        df = pd.DataFrame(data)
        if not df.empty and len(yahoo_symbols) > 0:
            yf_data = yf.download(" ".join(yahoo_symbols), period="1d", progress=False)
            if not yf_data.empty and 'Open' in yf_data:
                yf_open = yf_data['Open']
                for i, row in df.iterrows():
                    sym = row['Yahoo代號']
                    if sym in yf_open.columns and len(yf_open[sym]) > 0 and not pd.isna(yf_open[sym].iloc[-1]): df.at[i, '開盤價'] = round(yf_open[sym].iloc[-1], 2)
                    else: df.at[i, '開盤價'] = round(row['當前價'] * (1 - row['漲跌幅(%)']/100), 2)
            else:
                for i, row in df.iterrows(): df.at[i, '開盤價'] = round(row['當前價'] * (1 - row['漲跌幅(%)']/100), 2)
        
        tw_tz = timezone(timedelta(hours=8))
        return df, datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
    except Exception: return pd.DataFrame(), ""

# ==========================================
# 6. 全局框架切換 (新增頂部 Tabs)
# ==========================================
# 建立頂層導航標籤
main_tabs = st.tabs(["📊 金錢策略", "📈 籌碼深度透視", "🔮 AI 趨勢預測", "⚙️ 回測與資產管理"])

# 原本的所有邏輯全部放入第一個 Tab 內
with main_tabs[0]:
    with st.container(border=True):
        st.markdown("<h4 style='margin-bottom: 5px; color: #2D3436; font-family: \"Noto Sans TC\", sans-serif;'>策略參數與自動化</h4>", unsafe_allow_html=True)

        # 區分左右半部，左半部為參數網格，右半部為顯示設定
        left_panel, right_panel = st.columns([5.5, 4.5])

        with left_panel:
            # 第一排輸入框
            c1, c2, c3 = st.columns([2, 2, 1.5], gap="small")
            with c1: min_price = st.number_input("最低價", value=10, step=10)
            with c2: max_price = st.number_input("最高價", value=700, step=10)
            with c3:
                st.markdown("<div style='margin-top: 31px;'></div>", unsafe_allow_html=True)
                exclude_etf = st.checkbox("排除 ETF", value=True)

            # 第二排輸入框
            c4, c5, _ = st.columns([2, 2, 1.5], gap="small")
            with c4: max_up_change = st.number_input("最高漲幅限制%", value=6.0, step=0.5)
            with c5: max_dn_change = st.number_input("最低跌幅限制%", value=-6.0, step=0.5)

        with right_panel:
            # 將顯示圖表相關控制移至右側，並與左側第一排對齊
            rc1, rc2 = st.columns([1, 1.5], gap="small")
            with rc1:
                # 加上 margin-top 讓開關剛好跟右側 Slider 對齊
                st.markdown("<div style='margin-top: 31px;'></div>", unsafe_allow_html=True)
                enable_charts = st.toggle("顯示圖表總覽", value=False)
            with rc2:
                chart_limit = st.slider("最多顯示數量", min_value=3, max_value=21, step=3, value=6)

            # 將快照儲存路徑移入右半部，與左側第二排完美水平對齊
            export_dir = st.text_input("快照儲存路徑", value=os.path.join(os.getcwd(), "exports"))

        # 使用自訂 HR 標籤來取代 st.divider() 以大幅減少上下留白
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px; border-top: 1px solid #E8E6E1;'>", unsafe_allow_html=True)

        b1, b2, b3, b4, b5 = st.columns([1.5, 1.5, 1.5, 1, 1.5], gap="small")
        
        with b1: run_up_strategy = st.button("暴眼突圍術", use_container_width=True)
        with b2: run_dn_strategy = st.button("暴眼定錨法", use_container_width=True)
        with b3: run_snapshot = st.button("儲存快照", use_container_width=True)
        with b4: auto_interval = st.selectbox("自動間隔", [5, 10, 15, 30], format_func=lambda x: f"{x}分", label_visibility="collapsed")
        with b5: 
            if not st.session_state.get('auto_mode', False):
                if st.button("定時快照", type="primary", use_container_width=True):
                    st.session_state.auto_mode = True
                    st.session_state.interval = auto_interval
                    st.session_state.last_run_time = 0
                    st.rerun()
            else:
                if st.button("停止定時快照", type="secondary", use_container_width=True):
                    st.session_state.auto_mode = False
                    st.rerun()

    if run_up_strategy: st.session_state.show_up, st.session_state.show_dn, st.session_state.selected_stock = True, False, None
    if run_dn_strategy: st.session_state.show_up, st.session_state.show_dn, st.session_state.selected_stock = False, True, None
    auto_triggered = False

    if st.session_state.get('auto_mode', False):
        tw_tz = timezone(timedelta(hours=8))
        now = datetime.now(tw_tz)
        if now.strftime("%H:%M") > "14:45":
            st.warning("已過收盤時間，定時快照結束。")
            st.session_state.auto_mode = False
            time.sleep(3); st.rerun()
        elif now.weekday() >= 5: st.info("週末非開盤時間，暫停定時快照。")
        elif now.strftime("%H:%M") < "09:00": st.info("尚未開盤，等待中。")
        else:
            current_time = time.time()
            if current_time - st.session_state.get('last_run_time', 0) >= st.session_state.interval * 60:
                st.cache_data.clear(); auto_triggered = True; st.session_state.last_run_time = current_time
            st.success(f"自動模式運作中，每 {st.session_state.interval} 分鐘儲存快照。")

    if auto_triggered or run_snapshot:
        st.session_state.show_up, st.session_state.show_dn = True, True

    # ------------------------------------------
    # 主邏輯顯示 (限定在金錢策略 Tab 內)
    # ------------------------------------------
    if st.session_state.selected_stock is not None:
        if st.button("返回策略清單", type="primary", use_container_width=True):
            st.session_state.selected_stock = None
            st.rerun()
        render_stock_detail(st.session_state.selected_stock)

    elif st.session_state.show_up or st.session_state.show_dn:
        with st.spinner('同步數據中...'):
            raw_df, fetch_time = get_market_data()

        if not raw_df.empty:
            base_df = raw_df[(raw_df["當前價"] >= min_price) & (raw_df["當前價"] <= max_price)]
            if exclude_etf: base_df = base_df[~base_df["代號"].str.startswith("00")]

            up_cond = (base_df["漲跌幅(%)"] <= max_up_change) & (base_df["當前價"] >= base_df["開盤價"])
            df_up = base_df[up_cond].sort_values(by="漲跌幅(%)", ascending=False).head(20).reset_index(drop=True)
            df_up.index += 1

            dn_cond = (base_df["漲跌幅(%)"] >= max_dn_change) & (base_df["當前價"] < base_df["開盤價"])
            df_dn = base_df[dn_cond].sort_values(by="漲跌幅(%)", ascending=False).head(20).reset_index(drop=True)
            df_dn.index += 1

            if auto_triggered or run_snapshot:
                img_path = save_strategy_image(df_up, df_dn, fetch_time, export_dir)
                if img_path: st.success(f"快照已儲存：{img_path}")

            display_cols = ["代號", "名稱", "當前價", "開盤價", "漲跌幅(%)"]

            if st.session_state.show_up:
                col_t1, col_t2 = st.columns([6, 4])
                with col_t1: st.markdown("### 暴眼突圍術")
                with col_t2: st.markdown(f"<div style='text-align: right; margin-top: 15px; color: #8A8F95; font-size: 14px;'>資料時間：{fetch_time}</div>", unsafe_allow_html=True)
                
                if not df_up.empty:
                    df_col, _ = st.columns([3.5, 6.5])
                    with df_col:
                        st.dataframe(df_up[display_cols], use_container_width=True, hide_index=True)
                    if enable_charts: draw_overview_grid(df_up, chart_limit)
                else: st.info("無符合標的")

            if st.session_state.show_dn:
                st.markdown("<hr style='margin-top: 10px; margin-bottom: 10px; border-top: 1px solid #E8E6E1;'>", unsafe_allow_html=True)
                col_t1, col_t2 = st.columns([6, 4])
                with col_t1: st.markdown("### 暴眼定錨法")
                with col_t2: st.markdown(f"<div style='text-align: right; margin-top: 15px; color: #8A8F95; font-size: 14px;'>資料時間：{fetch_time}</div>", unsafe_allow_html=True)
                
                if not df_dn.empty:
                    df_col, _ = st.columns([3.5, 6.5])
                    with df_col:
                        st.dataframe(df_dn[display_cols], use_container_width=True, hide_index=True)
                    if enable_charts: draw_overview_grid(df_dn, chart_limit)
                else: st.info("無符合標的")

# ------------------------------------------
# 未來擴充的 Tab 預留區塊
# ------------------------------------------
with main_tabs[1]:
    st.info("💡 **籌碼深度透視**：此區塊為未來新功能保留。您可以考慮在這裡加入三大法人進階追蹤、大戶持股比例變化圖等進階籌碼面功能。")

with main_tabs[2]:
    st.info("💡 **AI 趨勢預測**：此區塊為未來新功能保留。未來若串接機器學習或語言模型 (LLM) 分析財經新聞，可在此展示大盤與個股的情緒分數。")

with main_tabs[3]:
    st.info("💡 **回測與資產管理**：此區塊為未來新功能保留。適合放入使用者專屬的投資組合追蹤、績效回測報告與資金水位管理工具。")

st.markdown("""
<style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
</style>
""", unsafe_allow_html=True)

if st.session_state.get('auto_mode', False) and st.session_state.selected_stock is None:
    time.sleep(10); st.rerun()