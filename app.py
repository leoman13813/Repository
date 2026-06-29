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
import csv

# ==========================================
# 網頁標題與狀態初始化
# ==========================================
st.set_page_config(
    page_title="風暴眼 - 旗艦版", 
    page_icon="Gemini_Generated_Image_rmgi3urmgi3urmgi.png", 
    layout="wide"
)

# ==========================================
# 視覺樣式設定 CSS
# ==========================================
nordic_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=Noto+Serif+TC:wght@400;700;900&display=swap');

    .stApp {
        background: linear-gradient(135deg, #FDFBF7 0%, #F5F0E6 100%);
        font-family: 'Noto Serif TC', "PingFang TC", "Microsoft JhengHei", serif;
    }
    [data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 2rem !important; padding-bottom: 1rem !important; }

    h1, h2, h3, h4, h5, h6 {
        color: #2D3436;
        font-family: 'Noto Sans TC', "PingFang TC", "Microsoft JhengHei", sans-serif !important;
    }
    p, span, div, li, th, td, label {
        color: #2D3436;
        font-family: 'Noto Serif TC', "PingFang TC", "Microsoft JhengHei", serif;
    }
    
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05) !important;
        padding: 1.5rem !important;
    }

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
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #4A6572 0%, #2F4858 100%);
        color: #FAF3E0; 
    }
    .stButton > button[kind="primary"]:hover {
        background: #2F4858;
        color: #FFFFFF; 
    }

    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 2px solid #E8E6E1; }
    .stTabs [data-baseweb="tab"] {
        padding-top: 10px; padding-bottom: 10px; color: #8A8F95;
        font-family: 'Noto Sans TC', sans-serif !important; font-size: 1.1rem !important;
    }
    .stTabs [aria-selected="true"] { color: #4A6572 !important; border-bottom-color: #4A6572 !important; font-weight: bold; }

    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] {
        border-radius: 6px; border: 1px solid #E8E6E1; background-color: rgba(255, 255, 255, 0.5);
    }
    .stNumberInput, .stTextInput { margin-bottom: -15px !important; }
    .stCheckbox { margin-bottom: -10px; }

    th { background-color: rgba(247, 245, 240, 0.8) !important; color: #8A8F95 !important; font-weight: 600 !important; border-bottom: 1px solid #E8E6E1 !important; }
    hr { border-top-color: #E8E6E1 !important; }
</style>
"""
st.markdown(nordic_css, unsafe_allow_html=True)

# ==========================================
# 🔒 身分驗證守門員與紀錄模組
# ==========================================
DEV_MODE = False  # 開發模式：設為 True 即可暫時免登入，上線時請改回 False

def check_password():
    if DEV_MODE:
        st.session_state["user_email"] = "admin@gmail.com"
        return True

    if st.session_state.get("password_correct", False): 
        return True

    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; color: #4A6572; font-family: \"Noto Sans TC\", sans-serif; letter-spacing: 2px;'>🔒 風暴眼 - 系統登入</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #8A8F95; margin-bottom: 20px;'>請輸入已授權的 Email 與通行密碼</p>", unsafe_allow_html=True)
            
            email_input = st.text_input("授權 Email")
            password_input = st.text_input("通行密碼", type="password") 
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("登入系統", use_container_width=True, type="primary"):
                allowed_users = {
                    "admin@gmail.com": "admin123",    
                    "leoman13813@gmail.com": "leoman",    
"billups1688@gmail.com": "storm888", 
"kaidod820@gmail.com": "storm888",
"certainok2365@gmail.com": "storm888"    
                }
                
                if email_input in allowed_users and allowed_users[email_input] == password_input:
                    st.session_state["password_correct"] = True
                    st.session_state["user_email"] = email_input
                    
                    tw_tz = timezone(timedelta(hours=8))
                    login_time = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
                    log_file = "login_logs.csv"
                    
                    try:
                        file_exists = os.path.isfile(log_file)
                        with open(log_file, mode="a", encoding="utf-8-sig", newline="") as f:
                            writer = csv.writer(f)
                            if not file_exists:
                                writer.writerow(["登入帳號 (Email)", "登入時間 (台灣時間)"])
                            writer.writerow([email_input, login_time])
                    except Exception: pass

                    st.rerun() 
                else:
                    st.error("🚫 帳號或密碼錯誤，請確認您是否有存取權限。")
    return False

if not check_password(): st.stop()

# ==========================================
# 系統主邏輯開始 (UI 與 標題)
# ==========================================
logo_path = "Gemini_Generated_Image_rmgi3urmgi3urmgi.png"
logo_html = ""
if os.path.exists(logo_path):
    with open(logo_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    logo_html = f'''<span style="display: inline-block; width: 1.4em; height: 1.4em; background-image: url('data:image/png;base64,{encoded_string}'); background-size: auto 170%; background-position: center; border-radius: 50%; vertical-align: text-bottom; margin-right: 12px; margin-bottom: -4px; box-shadow: 0 4px 10px rgba(0,0,0,0.15);"></span>'''

st.markdown(f"<h2 style='text-align: left; font-family: \"Noto Sans TC\", sans-serif; color: #2F4858; letter-spacing: 4px; font-weight: 900; margin-top: -10px; margin-bottom: 20px;'>{logo_html}風暴眼</h2>", unsafe_allow_html=True)

if 'selected_stock' not in st.session_state: st.session_state.selected_stock = None
if 'show_up' not in st.session_state: st.session_state.show_up = False
if 'show_dn' not in st.session_state: st.session_state.show_dn = False

# ==========================================
# 核心大盤資料引擎 (修正 ▽ 與 ▼ 實心跌停符號防呆)
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
            name = name_tag.text.strip()
            raw_symbol = symbol_tag.text.strip()
            clean_symbol = raw_symbol.replace(".TW", "").replace(".TWO", "")
            
            cols = row.find_all("div", class_="Fxg(1)")
            if len(cols) >= 5:
                price_str = cols[0].text.replace(",", "")
                price = float(price_str) if price_str.replace(".", "").isdigit() else 0.0
                
                # 🚀 修復：同時判定空心下跌 ▽ 與實心跌停 ▼
                change_html = str(cols[2])
                change_text = cols[2].text.strip()
                is_down = any(x in change_text for x in ["▽", "▼", "-"]) or "trend-down" in change_html
                
                clean_pct = re.sub(r'[^\d.]', '', change_text)
                try:
                    change_pct = float(clean_pct)
                    if is_down and change_pct != 0: change_pct = -change_pct
                except ValueError: change_pct = 0.0
                
                yahoo_symbols.append(raw_symbol)
                data.append({"代號": clean_symbol, "名稱": name, "當前價": price, "開盤價": 0.0, "漲跌幅(%)": change_pct, "Yahoo代號": raw_symbol})
        
        df = pd.DataFrame(data)
        if not df.empty and len(yahoo_symbols) > 0:
            yf_data = yf.download(" ".join(yahoo_symbols), period="6d", progress=False)
            pct_5d_dict = {}
            for sym in yahoo_symbols:
                try:
                    hist = yf_data['Close'][sym].dropna() if len(yahoo_symbols) > 1 else yf_data['Close'].dropna()
                    if len(hist) >= 5:
                        c_now = hist.iloc[-1]
                        c_5d = hist.iloc[-5]
                        pct_5d_dict[sym] = f"{(c_now - c_5d) / c_5d * 100:+.2f}%"
                    else: pct_5d_dict[sym] = "-"
                except: pct_5d_dict[sym] = "-"
            
            if 'Open' in yf_data:
                yf_open = yf_data['Open']
                for i, row in df.iterrows():
                    sym = row['Yahoo代號']
                    df.at[i, '漲跌幅_5d'] = pct_5d_dict.get(sym, "-")
                    if len(yahoo_symbols) > 1:
                        if sym in yf_open.columns and len(yf_open[sym]) > 0 and not pd.isna(yf_open[sym].iloc[-1]): 
                            df.at[i, '開盤價'] = round(yf_open[sym].iloc[-1], 2)
                        else: df.at[i, '開盤價'] = round(row['當前價'] * (1 - row['漲跌幅(%)']/100), 2)
                    else:
                        if len(yf_open) > 0 and not pd.isna(yf_open.iloc[-1]): df.at[i, '開盤價'] = round(yf_open.iloc[-1], 2)
                        else: df.at[i, '開盤價'] = round(row['當前價'] * (1 - row['漲跌幅(%)']/100), 2)
            else:
                for i, row in df.iterrows():
                    df.at[i, '漲跌幅_5d'] = pct_5d_dict.get(row['Yahoo代號'], "-")
                    df.at[i, '開盤價'] = round(row['當前價'] * (1 - row['漲跌幅(%)']/100), 2)
        else:
            for i, row in df.iterrows():
                df.at[i, '漲跌幅_5d'] = "-"
                df.at[i, '開盤價'] = round(row['當前價'] * (1 - row['漲跌幅(%)']/100), 2)
                
        tw_tz = timezone(timedelta(hours=8))
        return df, datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
    except Exception: return pd.DataFrame(), ""

# ==========================================
# 🌟 全市場真實強弱勢榜 (修復 endpoint 名稱)
# ==========================================
@st.cache_data(ttl=1800)
def get_top_movers(is_gainer=True):
    # 🚀 修復：Yahoo 財經正確的強弱勢網頁路徑
    endpoint = "change-up" if is_gainer else "change-down"
    url = f"https://tw.stock.yahoo.com/rank/{endpoint}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.find_all("li", class_=re.compile(r"List\(n\)", re.I))
        if not rows: rows = soup.find_all("li")
        
        data = []
        for rank, row in enumerate(rows[:20], 1):
            try:
                name_tag = row.find("div", class_="Lh(20px)")
                symbol_tag = row.find("span", class_="Fz(14px)")
                if not name_tag or not symbol_tag: continue
                name = name_tag.text.strip()
                raw_symbol = symbol_tag.text.strip()
                clean_sym = raw_symbol.replace(".TW", "").replace(".TWO", "")
                
                cols = row.find_all("div", class_="Fxg(1)")
                price_str = cols[0].text.replace(",", "")
                price = float(price_str) if price_str.replace(".", "").isdigit() else 0.0
                
                # 🚀 修復：同時判定空心下跌 ▽ 與實心跌停 ▼
                change_html = str(cols[2])
                change_text = cols[2].text.strip()
                is_down = any(x in change_text for x in ["▽", "▼", "-"]) or "trend-down" in change_html
                
                clean_pct = re.sub(r'[^\d.]', '', change_text)
                try:
                    change_pct = float(clean_pct)
                    if is_down and change_pct != 0: change_pct = -change_pct
                except ValueError: change_pct = 0.0
                
                data.append({"#": rank, "代號": clean_sym, "名稱": name, "當前價": price, "Yahoo代號": raw_symbol, "漲跌幅(%)": change_pct})
            except: pass
        
        df = pd.DataFrame(data)
        if df.empty: return df
        
        symbols = df["Yahoo代號"].tolist()
        yf_data = yf.download(" ".join(symbols), period="6d", progress=False)
        
        for i, row in df.iterrows():
            sym = row['Yahoo代號']
            try:
                hist = yf_data['Close'][sym].dropna() if len(symbols) > 1 else yf_data['Close'].dropna()
                if len(hist) >= 5:
                    c_now = hist.iloc[-1]
                    c_5d = hist.iloc[-5]
                    pct_5d = (c_now - c_5d) / c_5d * 100
                    df.at[i, '漲跌幅_5d'] = f"{pct_5d:+.2f}%"
                else: df.at[i, '漲跌幅_5d'] = "-"
            except: df.at[i, '漲跌幅_5d'] = "-"
            
        return df
    except Exception: return pd.DataFrame()

# ==========================================
# 各項爬蟲與圖表工具函數
# ==========================================
def _safe_float(val):
    if not isinstance(val, str): return float(val)
    try: return float(val.replace(',', '').replace('%', '').replace('+', '').strip())
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
            data.append({"月份": row[d_idx], "單月營收(千)": row[d_idx+1], "單月月增率": row[d_idx+2] + '%' if '%' not in row[d_idx+2] else row[d_idx+2], "單月年增率": row[d_idx+3] + '%' if '%' not in row[d_idx+3] else row[d_idx+3], "累計營收(千)": row[d_idx+4], "累計年增率": row[d_idx+5] + '%' if '%' not in row[d_idx+5] else row[d_idx+5]})
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def get_real_institutional_data(symbol):
    raw_data = scrape_yahoo_table(symbol, "institutional-trading", r'\d{2}[-/]\d{2}')
    parsed = []
    for row in raw_data:
        d_idx = next((i for i, t in enumerate(row) if re.search(r'\d{2}[-/]\d{2}', t)), None)
        if d_idx is not None:
            if len(row) >= d_idx + 10: parsed.append([row[d_idx], _safe_float(row[d_idx+1]), _safe_float(row[d_idx+2]), _safe_float(row[d_idx+3]), _safe_float(row[d_idx+4]), _safe_float(row[d_idx+5]), _safe_float(row[d_idx+6]), _safe_float(row[d_idx+7]), _safe_float(row[d_idx+8]), _safe_float(row[d_idx+9])])
            elif len(row) >= d_idx + 4: parsed.append([row[d_idx], 0.0, 0.0, _safe_float(row[d_idx+1]), 0.0, 0.0, _safe_float(row[d_idx+2]), 0.0, 0.0, _safe_float(row[d_idx+3])])
    if parsed: return pd.DataFrame(parsed, columns=pd.MultiIndex.from_tuples([('日期', ''), ('外資(張)', '買進'), ('外資(張)', '賣出'), ('外資(張)', '買賣超'), ('投信(張)', '買進'), ('投信(張)', '賣出'), ('投信(張)', '買賣超'), ('自營商(張)', '買進'), ('自營商(張)', '賣出'), ('自營商(張)', '買賣超')]))
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_broker_trading_data(symbol):
    raw_data = scrape_yahoo_table(symbol, "broker-trading", r'\d{2}[-/]\d{2}')
    parsed = []
    for row in raw_data:
        d_idx = next((i for i, t in enumerate(row) if re.search(r'\d{2}[-/]\d{2}', t)), None)
        if d_idx is not None and len(row) >= d_idx + 6: parsed.append([row[d_idx], _safe_float(row[d_idx+1]), _safe_float(row[d_idx+2]), _safe_float(row[d_idx+3]), _safe_float(row[d_idx+4]), _safe_float(row[d_idx+5])])
    if parsed: return pd.DataFrame(parsed, columns=['日期', '主力買進', '主力賣出', '買賣超', '買進家數', '賣出家數'])
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_margin_data(symbol):
    raw_data = scrape_yahoo_table(symbol, "margin", r'\d{2}[-/]\d{2}')
    parsed = []
    for row in raw_data:
        d_idx = next((i for i, t in enumerate(row) if re.search(r'\d{2}[-/]\d{2}', t)), None)
        if d_idx is not None and len(row) >= d_idx + 9: parsed.append([row[d_idx], _safe_float(row[d_idx+1]), _safe_float(row[d_idx+2]), _safe_float(row[d_idx+3]), _safe_float(row[d_idx+4]), _safe_float(row[d_idx+5]), _safe_float(row[d_idx+6]), _safe_float(row[d_idx+7]), _safe_float(row[d_idx+8])])
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

def save_strategy_image(df_up, df_dn, fetch_time, export_dir):
    try:
        if not os.path.exists(export_dir): os.makedirs(export_dir)
        plt.rcParams['font.sans-serif'] = ['Noto Sans TC', 'Microsoft JhengHei', 'PingFang HK', 'Arial Unicode MS', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
        fig.patch.set_facecolor('#F7F5F0')
        fig.suptitle(f"風暴眼雙策略快照 | 擷取時間：{fetch_time}", fontsize=18, fontweight='bold', y=0.98, color='#2D3436')

        def draw_table(ax, df, title, title_color):
            ax.axis('off'); ax.set_title(title, fontsize=15, color=title_color, pad=10, fontweight='bold')
            if df.empty: ax.text(0.5, 0.5, "此條件下無符合標的", ha='center', va='center', fontsize=12, color='#8A8F95'); return
            df_plot = df.head(20).copy()
            if "Yahoo代號" in df_plot.columns: df_plot = df_plot.drop(columns=["Yahoo代號"])
            table = ax.table(cellText=[df_plot.columns.tolist()] + df_plot.values.tolist(), colWidths=[0.15, 0.22, 0.15, 0.15, 0.15], loc='center', cellLoc='center')
            table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.8) 
            for j in range(len(df_plot.columns)): table[0, j].set_text_props(weight='bold', color='#FFFFFF'); table[0, j].set_facecolor('#4A6572')

        draw_table(ax1, df_up, "暴眼突圍術 (紅K)", '#D9736A')
        draw_table(ax2, df_dn, "暴眼定錨法 (黑K)", '#6B9080')
        plt.tight_layout()
        filepath = os.path.join(export_dir, f"Strategy_{fetch_time.replace(':', '').replace('-', '').replace(' ', '_')}.png")
        plt.savefig(filepath, bbox_inches='tight', dpi=150)
        plt.close(fig)
        return os.path.abspath(filepath)
    except Exception: return None

def render_local_chart_controls(symbol, prefix="grid", default_to_intraday=False):
    col_radio, col_spacer, col_setting = st.columns([5, 3, 4])
    with col_radio: c_type = st.radio("圖表模式", ["K線圖", "即時走勢"], index=1 if default_to_intraday else 0, horizontal=True, key=f"ctype_{prefix}_{symbol}", label_visibility="collapsed")
    if c_type == "K線圖":
        with col_setting:
            with st.popover("⚙️ 圖表設定", use_container_width=True):
                period = st.radio("週期", ["1M", "3M", "6M", "1Y"], index=1, horizontal=True, key=f"p_{prefix}_{symbol}", label_visibility="collapsed")
                st.divider()
                mas = st.multiselect("主圖指標", ["MA5", "MA10", "MA20", "MA60", "Bollinger"], default=["MA5", "MA10"], key=f"ma_{prefix}_{symbol}")
                subs = st.multiselect("副圖指標 (最多3個)", ["KD", "MACD", "RSI", "主力買賣超", "外資", "投信", "自營"], default=[], max_selections=3, key=f"subs_{prefix}_{symbol}")
        k_params = {'period': period, 'ma5': 'MA5' in mas, 'ma10': 'MA10' in mas, 'ma20': 'MA20' in mas, 'ma60': 'MA60' in mas, 'bbands': 'Bollinger' in mas}
        return "K線圖", k_params, subs
    else: return "即時走勢", {}, []

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
                new_cols = ['_'.join(col).strip('_') if col[1] else col[0] for col in chip_df.columns.values]
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
            else: hist['主力買賣超'] = 0.0
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

        fig.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name='K線', increasing=dict(line=dict(color=increasing_color), fillcolor=increasing_color), decreasing=dict(line=dict(color=decreasing_color), fillcolor=decreasing_color)), row=1, col=1)
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
        fig.update_layout(height=dynamic_height, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False, showlegend=False, plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF', xaxis=dict(showline=True, linewidth=1, linecolor='#F0EEE9', mirror=True, gridcolor='#F7F5F0'))
        for r in range(1, num_subplots + 2): fig.update_yaxes(showline=True, linewidth=1, linecolor='#F0EEE9', mirror=True, gridcolor='#F7F5F0', row=r, col=1)
        return fig
    else:
        intra = stock.history(period="1d", interval="1m")
        if intra.empty: return None
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=intra.index, y=intra['Close'], mode='lines', name='走勢', line=dict(color='#4A6572', width=2), fill='tozeroy', fillcolor='rgba(74, 101, 114, 0.1)'))
        if open_price > 0: fig.add_hline(y=open_price, line_dash="dash", line_color="#E1B16A", line_width=2, annotation_text=f"開盤: {open_price}", annotation_position="bottom right")
        last_date_str = intra.index[-1].strftime("%Y-%m-%d")
        fig.update_xaxes(range=[f"{last_date_str} 09:00:00", f"{last_date_str} 13:30:00"], showline=True, linewidth=1, linecolor='#F0EEE9', mirror=True, gridcolor='#F7F5F0')
        y_min, y_max = min(intra['Close'].min(), open_price) * 0.99, max(intra['Close'].max(), open_price) * 1.01
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF', yaxis=dict(showline=True, linewidth=1, linecolor='#F0EEE9', mirror=True, gridcolor='#F7F5F0', range=[y_min, y_max]))
        return fig

@st.fragment
def draw_overview_grid(df, limit, prefix="grid"):
    if df.empty: return
    df_plot = df.head(limit)
    
    col_title, col_btn, _ = st.columns([3, 1.5, 5.5], gap="small")
    with col_title:
        st.markdown(f"<h5 style='margin-top: 5px; color: #2D3436; font-family: \"Noto Sans TC\", sans-serif; font-weight: bold;'>選股圖表總覽 (顯示前 {len(df_plot)} 檔)</h5>", unsafe_allow_html=True)
    with col_btn:
        st.button("🔄 即時刷新走勢", key=f"refresh_btn_{prefix}", use_container_width=True)

    cols = st.columns(3)
    for i, (_, row) in enumerate(df_plot.iterrows()):
        sym, name, open_price = row['Yahoo代號'], row['名稱'], row['開盤價']
        clean_sym = sym.replace('.TW', '').replace('.TWO', '')
        with cols[i % 3]:
            with st.container(border=True):
                if st.button(f"{name} ({clean_sym})", key=f"btn_{prefix}_{sym}", use_container_width=True):
                    st.session_state.selected_stock = row.to_dict()
                    st.rerun() 
                
                c_type, k_params, subs = render_local_chart_controls(sym, prefix=f"{prefix}_chart", default_to_intraday=True)
                stock = yf.Ticker(sym)
                fig = build_ta_figure(stock, sym, name, open_price, c_type, k_params, subs)
                if fig: st.plotly_chart(fig, use_container_width=True)

def render_stock_detail(row):
    sym, clean_sym, name, open_price = row['Yahoo代號'], row['Yahoo代號'].replace('.TW', '').replace('.TWO', ''), row['名稱'], row['開盤價']
    with st.container(border=True):
        st.markdown(f"### {name} ({clean_sym}) 詳細數據看板")
        tab_ta, tab_rev, tab_chips = st.tabs(["圖表分析", "營收資料", "籌碼分佈"])
        with tab_ta:
            c_type, k_params, subs = render_local_chart_controls(sym, prefix="detail", default_to_intraday=False)
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
                st.markdown(f"""<div style="display: flex; gap: 15px; margin-bottom: 20px;"><div style="flex: 1; border: 1px solid #F0EEE9; padding: 15px; border-radius: 8px; background-color: #FAFAFA;"><div style="font-size: 13px; color: #8A8F95;">外資今日</div><div style="font-size: 20px; font-weight: bold; color: {get_color(fi_today)};">{get_sign(fi_today)}{int(fi_today):,}</div></div><div style="flex: 1; border: 1px solid #F0EEE9; padding: 15px; border-radius: 8px; background-color: #FAFAFA;"><div style="font-size: 13px; color: #8A8F95;">外資 5 日</div><div style="font-size: 20px; font-weight: bold; color: {get_color(fi_5d)};">{get_sign(fi_5d)}{int(fi_5d):,}</div></div><div style="flex: 1; border: 1px solid #F0EEE9; padding: 15px; border-radius: 8px; background-color: #FAFAFA;"><div style="font-size: 13px; color: #8A8F95;">投信今日</div><div style="font-size: 20px; font-weight: bold; color: {get_color(it_today)};">{get_sign(it_today)}{int(it_today):,}</div></div><div style="flex: 1; border: 1px solid #F0EEE9; padding: 15px; border-radius: 8px; background-color: #FAFAFA;"><div style="font-size: 13px; color: #8A8F95;">投信 5 日</div><div style="font-size: 20px; font-weight: bold; color: {get_color(it_5d)};">{get_sign(it_5d)}{int(it_5d):,}</div></div></div>""", unsafe_allow_html=True)
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

# ==========================================
# 🚀 擴充功能 2：極速成交值排行與 HTML 表格繪製
# ==========================================
@st.cache_data(ttl=1800)
def get_turnover_top30_fast():
    url = "https://tw.stock.yahoo.com/rank/turnover"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.find_all("li", class_=re.compile(r"List\(n\)", re.I))
        if not rows: rows = soup.find_all("li")
        data = []
        for rank, row in enumerate(rows[:30], 1):
            try:
                name_tag = row.find("div", class_="Lh(20px)")
                symbol_tag = row.find("span", class_="Fz(14px)")
                if not name_tag or not symbol_tag: continue
                name = name_tag.text.strip()
                raw_symbol = symbol_tag.text.strip()
                
                cols = row.find_all("div", class_="Fxg(1)")
                change_html = str(cols[2])
                change_text = cols[2].text.strip()
                is_down = any(x in change_text for x in ["▽", "▼", "-"]) or "trend-down" in change_html
                
                clean_pct = re.sub(r'[^\d.]', '', change_text)
                try:
                    pct_1d = float(clean_pct)
                    if is_down and pct_1d != 0: pct_1d = -pct_1d
                except: pct_1d = 0.0
                
                try:
                    turnover_val = cols[4].text.strip()
                    if "億" not in turnover_val: turnover_val = "-"
                except: turnover_val = "-"
                
                data.append({
                    "#": rank, 
                    "股票": f"{name} ({raw_symbol.replace('.TW', '').replace('.TWO', '')})", 
                    "Yahoo代號": raw_symbol,
                    "漲跌": f"{pct_1d:+.2f}%",
                    "成交值": turnover_val
                })
            except: pass
            
        if not data: return pd.DataFrame()
        symbols = [item["Yahoo代號"] for item in data]
        yf_data = yf.download(" ".join(symbols), period="6d", progress=False)
        
        for item in data:
            sym = item["Yahoo代號"]
            try:
                hist = yf_data['Close'][sym].dropna() if len(symbols) > 1 else yf_data['Close'].dropna()
                if len(hist) >= 5:
                    c_now = hist.iloc[-1]
                    c_5d = hist.iloc[-5]
                    pct_5d = (c_now - c_5d) / c_5d * 100
                    item["5日"] = f"{pct_5d:+.2f}%"
                else: item["5日"] = "-"
                
                if item["成交值"] == "-":
                    if len(hist) > 1:
                        vol_series = yf_data['Volume'][sym].dropna() if len(symbols) > 1 else yf_data['Volume'].dropna()
                        last_vol = vol_series.iloc[-1]
                        last_close = hist.iloc[-1]
                        t_100m = (last_close * last_vol) / 100000000
                        item["成交值"] = f"{t_100m:.1f} 億"
            except: item["5日"] = "-"
        return pd.DataFrame(data)
    except Exception: return pd.DataFrame()

def render_turnover_table_fast(df):
    html_str = ""
    html_str += "<style>"
    html_str += ".rank-table { width: 100%; table-layout: fixed; border-collapse: collapse; font-family: 'Noto Sans TC', sans-serif; background: #FFFFFF; font-size: 14.5px; }"
    html_str += ".rank-table thead tr th:first-child { display: table-cell !important; }"
    html_str += ".rank-table th { color: #8A8F95; font-weight: bold; padding: 12px 10px; border-bottom: 2px solid #F0EEE9; font-size: 14px; }"
    html_str += ".rank-table td { padding: 12px 10px; color: #2D3436; border-bottom: 1px solid #F0EEE9; vertical-align: middle; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }"
    html_str += ".rank-table tr:hover { background-color: #FAFAFA; }"
    html_str += "</style>"
    html_str += "<table class='rank-table'>"
    html_str += "<thead><tr><th style='width: 10%; text-align: center;'>#</th><th style='width: 40%; text-align: left;'>股票</th><th style='width: 20%; text-align: center;'>成交值</th><th style='width: 15%; text-align: center;'>漲跌</th><th style='width: 15%; text-align: center;'>5日</th></tr></thead><tbody>"
    for _, row in df.iterrows():
        c_day = "color: #47B262; font-weight: bold;" if "-" in str(row["漲跌"]) else ("color: #EB5554; font-weight: bold;" if "+" in str(row["漲跌"]) else "color: #2D3436;")
        c_5d = "color: #47B262; font-weight: bold;" if "-" in str(row["5日"]) else ("color: #EB5554; font-weight: bold;" if "+" in str(row["5日"]) else "color: #2D3436;")
        clean_sym = row["Yahoo代號"].replace(".TW", "").replace(".TWO", "")
        html_str += "<tr>"
        html_str += f"<td style='color: #8A8F95; text-align: center;'>{row['#']}</td>"
        html_str += f"<td style='text-align: left; font-weight: bold;'><a href='https://tw.stock.yahoo.com/quote/{clean_sym}' target='_blank' style='color: #2D3436; text-decoration: none;'>{row['股票']}</a></td>"
        html_str += f"<td style='font-weight: bold; color: #4A6572; text-align: center;'>{row['成交值']}</td>"
        html_str += f"<td style='{c_day} text-align: center;'>{row['漲跌']}</td>"
        html_str += f"<td style='{c_5d} text-align: center;'>{row['5日']}</td>"
        html_str += "</tr>"
    html_str += "</tbody></table>"
    return html_str

def render_movement_table(df, is_gainer=True):
    html_str = ""
    html_str += "<style>"
    html_str += ".move-table { width: 100%; table-layout: fixed; border-collapse: collapse; font-family: 'Noto Sans TC', sans-serif; background: #FFFFFF; font-size: 14px; }"
    html_str += ".move-table thead tr th:first-child { display: table-cell !important; }"
    html_str += ".move-table th { color: #8A8F95; font-weight: bold; padding: 10px 8px; border-bottom: 2px solid #F0EEE9; font-size: 13.5px; }"
    html_str += ".move-table td { padding: 10px 8px; color: #2D3436; border-bottom: 1px solid #F0EEE9; vertical-align: middle; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }"
    html_str += ".move-table tr:hover { background-color: #FAFAFA; }"
    html_str += "</style>"
    html_str += "<table class='move-table'>"
    html_str += f"<thead><tr><th style='width: 8%; text-align: center;'>#</th><th style='width: 34%; text-align: left;'>股票</th><th style='width: 20%; text-align: center;'>{'漲幅' if is_gainer else '跌幅'}</th><th style='width: 20%; text-align: center;'>5日</th><th style='width: 18%; text-align: center;'>收盤</th><th style='width: 20%; text-align: center;'>所屬題材</th></tr></thead><tbody>"
    
    for i, row in df.iterrows():
        rank = row['#']
        stock_title = f"{row['名稱']} ({row['代號']})"
        pct_1d = row['漲跌幅(%)']
        change_1d = f"{pct_1d:+.2f}%"
        change_5d = row['漲跌幅_5d']
        price = f"{row['當前價']:.2f}"
        
        c_day = "color: #EB5554; font-weight: bold;" if pct_1d > 0 else ("color: #47B262; font-weight: bold;" if pct_1d < 0 else "color: #2D3436;")
        c_5d = "color: #EB5554; font-weight: bold;" if "+" in str(change_5d) else ("color: #47B262; font-weight: bold;" if "-" in str(change_5d) else "color: #2D3436;")
        
        html_str += "<tr>"
        html_str += f"<td style='color: #8A8F95; text-align: center;'>{rank}</td>"
        html_str += f"<td style='text-align: left; font-weight: bold;'>{stock_title}</td>"
        html_str += f"<td style='{c_day} text-align: center;'>{change_1d}</td>"
        html_str += f"<td style='{c_5d} text-align: center;'>{change_5d}</td>"
        html_str += f"<td style='color: #4A6572; text-align: center;'>{price}</td>"
        html_str += f"<td style='color: #8A8F95; text-align: center;'>—</td>"
        html_str += "</tr>"
    html_str += "</tbody></table>"
    return html_str

# ==========================================
# 6. 全局框架切換 (動態產生 Tabs)
# ==========================================
tab_titles = ["📊 金錢策略", "📈 今日重點", "🔮 AI 趨勢預測", "⚙️ 回測與資產管理"]
is_admin = st.session_state.get("user_email") == "admin@gmail.com"

if is_admin:
    tab_titles.append("🛡️ 後台管理")

main_tabs = st.tabs(tab_titles)

with main_tabs[0]:
    with st.container(border=True):
        st.markdown("<h4 style='margin-bottom: 5px; color: #2D3436; font-family: \"Noto Sans TC\", sans-serif;'>策略參數與自動化</h4>", unsafe_allow_html=True)
        left_panel, right_panel = st.columns([5.5, 4.5])
        with left_panel:
            c1, c2, c3 = st.columns([2, 2, 1.5], gap="small")
            with c1: min_price = st.number_input("最低價", value=10, step=10)
            with c2: max_price = st.number_input("最高價", value=700, step=10)
            with c3:
                st.markdown("<div style='margin-top: 31px;'></div>", unsafe_allow_html=True)
                exclude_etf = st.checkbox("排除 ETF", value=True)
            c4, c5, _ = st.columns([2, 2, 1.5], gap="small")
            with c4: max_up_change = st.number_input("最高漲幅限制%", value=6.0, step=0.5)
            with c5: max_dn_change = st.number_input("最低跌幅限制%", value=-6.0, step=0.5)
        with right_panel:
            rc1, rc2 = st.columns([1, 1.5], gap="small")
            with rc1:
                st.markdown("<div style='margin-top: 31px;'></div>", unsafe_allow_html=True)
                enable_charts = st.toggle("顯示圖表總覽", value=False)
            with rc2: chart_limit = st.slider("最多顯示數量", min_value=3, max_value=21, step=3, value=6)
            export_dir = st.text_input("快照儲存路徑", value=os.path.join(os.getcwd(), "exports"))
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

    if auto_triggered or run_snapshot: st.session_state.show_up, st.session_state.show_dn = True, True

    if st.session_state.selected_stock is not None:
        if st.button("返回策略清單", type="primary", use_container_width=True):
            st.session_state.selected_stock = None
            st.rerun()
        render_stock_detail(st.session_state.selected_stock)
    elif st.session_state.show_up or st.session_state.show_dn:
        with st.spinner('同步數據中...'): raw_df, fetch_time = get_market_data()
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
                    with df_col: st.dataframe(df_up[display_cols], use_container_width=True, hide_index=True)
                    if enable_charts: draw_overview_grid(df_up, chart_limit, prefix="up")
                else: st.info("無符合標的")
            if st.session_state.show_dn:
                st.markdown("<hr style='margin-top: 10px; margin-bottom: 10px; border-top: 1px solid #E8E6E1;'>", unsafe_allow_html=True)
                col_t1, col_t2 = st.columns([6, 4])
                with col_t1: st.markdown("### 暴眼定錨法")
                with col_t2: st.markdown(f"<div style='text-align: right; margin-top: 15px; color: #8A8F95; font-size: 14px;'>資料時間：{fetch_time}</div>", unsafe_allow_html=True)
                if not df_dn.empty:
                    df_col, _ = st.columns([3.5, 6.5])
                    with df_col: st.dataframe(df_dn[display_cols], use_container_width=True, hide_index=True)
                    if enable_charts: draw_overview_grid(df_dn, chart_limit, prefix="dn")
                else: st.info("無符合標的")

# ==========================================
# 🚀 擴充功能 2: 今日重點
# ==========================================
with main_tabs[1]:
    tw_tz = timezone(timedelta(hours=8))
    current_date_str = datetime.now(tw_tz).strftime("%Y-%m-%d")
    
    st.markdown(f"<h3 style='color: #4A6572; margin-bottom: 5px; font-family: \"Noto Sans TC\", sans-serif;'>今日焦點 {current_date_str}</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8A8F95; font-size: 15px; margin-bottom: 20px;'>當日強弱族群、資金集中度、漲停家數與個股漲跌幅榜。點擊題材或個股可深入查看詳情。</p>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("""<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #E8E6E1; padding-bottom: 10px; margin-bottom: 15px;"><div style="font-size: 18px; font-weight: bold; color: #4A6572; border-left: 4px solid #D9736A; padding-left: 10px;">成值分析</div><div style="font-size: 13px; color: #8A8F95; background: #F0EEE9; padding: 4px 10px; border-radius: 4px;">當日成交值前 30 名個股，掌握主力資金真實去向</div></div>""", unsafe_allow_html=True)
        st.markdown("""<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;"><div style="font-size: 16px; font-weight: bold; color: #2D3436; border-left: 3px solid #E1B16A; padding-left: 8px;">個股成交值排行</div><div style="font-size: 13px; color: #8A8F95;">點擊個股查看詳情</div></div>""", unsafe_allow_html=True)

        with st.spinner('鎖定資金流向，極速運算大盤成交值前 30 強...'):
            df_turnover = get_turnover_top30_fast()
            if not df_turnover.empty:
                col_left, col_right = st.columns([5, 5])
                with col_left: st.markdown(render_turnover_table_fast(df_turnover), unsafe_allow_html=True)
            else: st.info("無法獲取成交值排行榜，請稍後再試。")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("""<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #E8E6E1; padding-bottom: 10px; margin-bottom: 15px;"><div style="font-size: 18px; font-weight: bold; color: #4A6572; border-left: 4px solid #4A6572; padding-left: 10px;">個股動向</div><div style="font-size: 13px; color: #8A8F95; background: #F0EEE9; padding: 4px 10px; border-radius: 4px;">今日漲幅前 20 與跌幅前 20，點擊可查看個股詳情</div></div>""", unsafe_allow_html=True)
        
        with st.spinner('即時拉取全市場強弱勢榜單...'):
            col_gain, col_lose = st.columns([5, 5])
            
            df_gainers = get_top_movers(is_gainer=True)
            with col_gain:
                st.markdown("<div style='font-size: 16px; font-weight: bold; color: #2D3436; border-left: 3px solid #EB5554; padding-left: 8px; margin-bottom: 12px;'>個股漲幅榜</div>", unsafe_allow_html=True)
                if not df_gainers.empty:
                    st.markdown(render_movement_table(df_gainers, is_gainer=True), unsafe_allow_html=True)
                else: st.info("無法獲取漲幅排行榜")
                
            df_losers = get_top_movers(is_gainer=False)
            with col_lose:
                st.markdown("<div style='font-size: 16px; font-weight: bold; color: #2D3436; border-left: 3px solid #47B262; padding-left: 8px; margin-bottom: 12px;'>個股跌幅榜</div>", unsafe_allow_html=True)
                if not df_losers.empty:
                    st.markdown(render_movement_table(df_losers, is_gainer=False), unsafe_allow_html=True)
                else: st.info("無法獲取跌幅排行榜")

with main_tabs[2]:
    st.info("💡 **AI 趨勢預測**：此區塊為未來新功能保留。未來若串接機器學習或語言模型 (LLM) 分析財經新聞，可在此展示大盤與個股的情緒分數。")

with main_tabs[3]:
    st.info("💡 **回測與資產管理**：此區塊為未來新功能保留。適合放入使用者專屬的投資組合追蹤、績效回測報告與資金水位管理工具。")

# ==========================================
# 🛡️ 隱藏版後台管理分頁 (僅限 Admin 可見)
# ==========================================
if is_admin:
    with main_tabs[4]:
        st.markdown("<h3 style='color: #4A6572; font-family: \"Noto Sans TC\", sans-serif;'>系統登入與連線紀錄</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #8A8F95;'>這份紀錄檔暫存於雲端容器中，每次系統重新啟動或長時間休眠後可能會被清空。</p>", unsafe_allow_html=True)
        
        log_file = "login_logs.csv"
        
        if os.path.exists(log_file):
            df_logs = pd.read_csv(log_file)
            df_logs = df_logs.iloc[::-1].reset_index(drop=True)
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
            
            st.write("")
            col_btn, _ = st.columns([2, 8])
            with col_btn:
                if st.button("🗑️ 清空歷史紀錄", type="secondary", use_container_width=True):
                    os.remove(log_file)
                    st.rerun()
        else:
            st.info("目前尚無任何外部登入紀錄，或紀錄檔案已隨雲端休眠而重置。")

st.markdown("""
<style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
</style>
""", unsafe_allow_html=True)

if st.session_state.get('auto_mode', False) and st.session_state.selected_stock is None:
    time.sleep(10); st.rerun()