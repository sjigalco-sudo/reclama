import streamlit as st
import pandas as pd
import io
import zipfile
import os
import re
from datetime import timedelta, datetime, time

# --- КОНСТАНТЫ ---
PATH_MAIN = r"I:\RECLAMA 2026"
PATH_TOPSHOP = r"I:\TOPSHOP"
TS_FILE = "teleshopping1.mp4"
TS_DUR = 7.600
LOGO_PATH = "Global 24 Logo TV.png"

# --- КАСТОМНЫЙ ДИЗАЙН (CSS) ---
def inject_custom_css():
    st.markdown("""
        <style>
        .main { background-color: #0d1117; }
        h1 {
            color: #e6edf3;
            font-weight: 700;
            letter-spacing: 1px;
            border-bottom: 2px solid #30363d;
            padding-bottom: 10px;
        }
        section[data-testid="stSidebar"] {
            background-color: #161b22 !important;
            border-right: 1px solid #30363d;
        }
        .stButton>button {
            width: 100%;
            border-radius: 6px;
            border: 1px solid #30363d;
            background-color: #21262d;
            color: #c9d1d9;
            font-weight: 600;
        }
        .stButton>button:hover {
            border-color: #8b949e;
            color: #ffffff;
            background-color: #30363d;
        }
        .stDownloadButton>button {
            width: 100%;
            background-color: #238636 !important;
            color: white !important;
            border: 1px solid #2ea043 !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            margin-top: 20px;
        }
        .stDownloadButton>button:hover {
            background-color: #2ea043 !important;
            border-color: #3fb950 !important;
        }
        div[data-testid="stExpander"], .stFileUploader {
            border: 1px solid #30363d;
            border-radius: 8px;
            background-color: #0d1117;
        }
        .stAlert {
            border: 1px solid #238636;
            background-color: #04190b;
            color: #3fb950;
        }
        </style>
    """, unsafe_allow_html=True)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def extract_date_info(text):
    if pd.isna(text): return None, ""
    match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', str(text))
    if match:
        day, month, year = match.groups()
        clean_digits = f"{day.zfill(2)}{month.zfill(2)}{year}"
        display_date = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
        return display_date, clean_digits
    return None, ""

def to_time_obj(val):
    if isinstance(val, (datetime, time)): return val
    if isinstance(val, str):
        val = val.strip()
        for fmt in ("%H:%M:%S", "%H:%M"):
            try: return datetime.strptime(val, fmt).time()
            except ValueError: continue
    return None

def format_time_filename(t_obj):
    if hasattr(t_obj, 'strftime'): return t_obj.strftime('%H:%M')
    return str(t_obj)[:5]

def format_dur(sec):
    return f"{int(sec // 60):02d}:{int(sec % 60):02d}"

def xml_escape(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="Global 24 | Generator", page_icon="📺", layout="wide")
inject_custom_css()

# Логотип и Главный заголовок
if os.path.exists(LOGO_PATH):
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2: st.image(LOGO_PATH, use_container_width=True)

st.markdown("<h1 style='text-align: center;'>GLOBAL 24: УНИВЕРСАЛЬНЫЙ ГЕНЕРАТОР</h1>", unsafe_allow_html=True)

# Боковая панель
with st.sidebar:
    st.markdown("### ⚙️ ПАРАМЕТРЫ")
    ad_type = st.radio("Режим работы:", ["MD+SP (I:\RECLAMA 2026)", "TopShop (I:\TOPSHOP)"])
    
    mp4_ids = []
    if "MD+SP" in ad_type:
        with st.expander("🎥 Форматы (.mp4)"):
            mp4_ids_input = st.text_
