import streamlit as st
import pandas as pd
import io
import zipfile
import os
import re
from datetime import timedelta, datetime, time

# --- КОНСТАНТЫ ---
PASSWORD = "SJ"
PATH_MAIN = r"I:\RECLAMA 2026"
PATH_TOPSHOP = r"I:\TOPSHOP"
TS_FILE = "teleshopping1.mp4"
TS_DUR = 7.600
LOGO_PATH = "Global 24 Logo TV.png"

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
    if hasattr(t_obj, 'strftime'): return t_obj.strftime('%H-%M')
    return str(t_obj)[:5].replace(':', '-')

def xml_escape(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# --- ИНТЕРФЕЙС STREAMLIT ---
st.set_page_config(page_title="Global 24 | Generator", page_icon="🌐", layout="wide")

if 'auth_global' not in st.session_state:
    st.session_state['auth_global'] = False

if not st.session_state['auth_global']:
    st.title("🔒 Global 24: Вход")
    pwd = st.text_input("Пароль:", type="password")
    if st.button("Войти"):
        if pwd == PASSWORD:
            st.session_state['auth_global'] = True
            st.rerun()
        else:
            st.error("Неверный пароль")
    st.stop()

# --- ВЕРХНЯЯ ЧАСТЬ СТРАНИЦЫ (ЛОГОТИП ТОЛЬКО ТУТ) ---
if os.path.exists(LOGO_PATH):
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image(LOGO_PATH, use_container_width=True)

st.markdown("<h1 style='text-align: center;'>🌐 GLOBAL 24: УНИВЕРСАЛЬНЫЙ ГЕНЕРАТОР</h1>", unsafe_allow_html=True)

# --- SIDEBAR (ТОЛЬКО НАСТРОЙКИ) ---
with st.sidebar:
    st.header("⚙️ Настройки")
    ad_type = st.radio("Тип рекламы:", ["MD+SP (I:\RECLAMA 2026)", "TopShop (I:\TOPSHOP)"])
    
    mp4_ids = []
    if "MD+SP" in ad_type:
        with st.expander("📁 Настройки форматов (MP4)"):
            st.info("По умолчанию .mov. Впишите ID через запятую для .mp4")
            mp4_input = st.text_area("ID для .mp4:", value="6856, 6857")
            mp4_ids = [x.strip() for x in mp4_input.split(",") if x.strip()]
    
    st.divider()
    uploaded_file = st.file_uploader("Загрузить медиа-план", type=["xls", "xlsx"])
    
    if st.button("Выйти"):
        st.session_state['auth_global'] = False
        st.rerun()

# --- ЛОГИКА ОБРАБОТКИ ---
if uploaded_file:
    try:
        mode_topshop = "TopShop" in ad_type
        current_path = PATH_TOPSHOP if mode_topshop else PATH_MAIN
        
        df_raw = pd.read_excel(uploaded_file, header=None)
        zip_buffer = io.BytesIO()
        found_dates = []
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            if mode_topshop:
                current_date_prefix = ""
                current_block_items = []
                
                for index, row in df_raw.iterrows():
                    val_col0 = str(row[0])
                    if any(day in val_col0 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
                        disp_date, clean_digits = extract_date_info(val_col0)
                        if disp_date:
                            found_dates.append(disp_date)
                            current_date_prefix = clean_digits
                        continue
                    
                    if pd.notna(row[1]) and (":" in str(row[1])) and pd.notna(row[3]):
                        t_obj = to_time_obj(row[1])
                        if current_block_items and t_obj:
                            dt1 = datetime.combine(datetime.today(), current_block_items[-1]['time'])
                            dt2 = datetime.combine(datetime.today(), t_obj)
                            # Разрыв > 6 минут — новый файл
                            if (dt2 - dt1).total_seconds() > 360:
                                start_time_str = format_time_filename(current_block_items[0]['time'])
                                f_name = f"{current_date_prefix}_{start_time_str}.slblock"
                                total_dur = TS_DUR + sum(item['dur'] for item in current_block_items) + TS_DUR
                                xml_lines = [
                                    f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2',
                                    f'  <item file="{xml_escape(current_path)}\\{TS_FILE}" in="0.000" dur="{TS_DUR:.3f}" />'
                                ]
                                for item in current_block_items:
                                    xml_lines.append(f'  <item file="{xml_escape(current_path)}\\{item["file"]}" in="0.000" dur="{item["dur"]:.3f}" />')
                                xml_lines.append(f'  <item file="{xml_escape(current_path)}\\{TS_FILE}" in="0.000" dur="{TS_DUR:.3f}" />')
                                xml_lines.append('</slblock>')
                                zip_file.writestr(f_name, "\r\n".join(xml_lines).encode('utf-16'))
                                current_block_items = []

                        id_clean = str(row[3]).strip()
                        nm = str(row[2]).strip()
                        current_block_items.append({'time': t_obj, 'dur': float(row[4]), 'file': f"{id_clean}__{nm}.mp4"})

                if current_block_items:
                    start_time_str = format_time_filename(current_block_items[0]['time'])
                    f_name = f"{current_date_prefix}_{start_time_str}.slblock"
                    total_dur = TS_DUR + sum(item['dur'] for item in current_block_items) + TS_DUR
                    xml_lines = [
                        f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2',
                        f'  <item file="{xml_escape(current_path)}\\{TS_FILE}" in="0.000" dur="{TS_DUR:.3f}" />'
                    ]
                    for item in current_block_items:
                        xml_lines.append(f'  <item file="{xml_escape(current_path)}\\{item["file"]}" in="0.000" dur="{item["dur"]:.3f}" />')
                    xml_lines.append(f'  <item file="{xml_escape(current_path)}\\{TS_FILE}" in="0.000" dur="{TS_DUR:.3f}" />')
                    xml_lines.append('</slblock>')
                    zip_file.writestr(f_name, "\r\n".join(xml_lines).encode('utf-16'))

                zip_name = f"TOPSHOP {found_dates[0].split('.')[0]}-{found_dates[-1]}.zip" if found_dates else "TOPSHOP_Archive.zip"

            else:
                # --- ЛОГИКА MD+SP ---
                df = pd.read_excel(uploaded_file, skiprows=6)
                df_res = df.iloc[:, [2, 6, 7, 9]].copy()
                df_res.columns = ['Block_Time', 'Name', 'Dur', 'ID']
                df_res['Block_Time'] = df_res['Block_Time'].ffill()
                df_res = df_res.dropna(subset=['ID'])
                for i, (block_time, items) in enumerate(df_res.groupby('Block_Time', sort=False), 1):
                    time_filename = format_time_filename(block_time)
                    pub_num = ((i - 1) % 5) + 1
                    total_dur = 5.980 + items['Dur'].sum() + 6.580
                    xml_lines = [
                        f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2',
                        f'  <item file="{xml_escape(PATH_MAIN)}\\PIBLICITATE {pub_num} IN.mp4" in="0.000" dur="5.980" />'
                    ]
                    for _, row in items.iterrows():
                        id_c = str(row['ID']).split(".")[0]
                        nm_c = str(row['Name']).strip()
                        ext = ".mp4" if id_c in mp4_ids else ".mov"
                        xml_lines.append(f'  <item file="{xml_escape(PATH_MAIN)}\\{id_c}_{nm_c}{ext}" in="0.000" dur="{float(row["Dur"]):.3f}" />')
                    xml_lines.append(f'  <item file="{xml_escape(PATH_MAIN)}\\PIBLICITATE {pub_num} OUT.mp4" in="0.000" dur="6.580" />')
                    xml_lines.append('</slblock>')
                    zip_file.writestr(f"{time_filename}.slblock", "\r\n".join(xml_lines).encode('utf-16'))
                zip_name = f"MD_SP_Blocks_{os.path.splitext(uploaded_file.name)[0]}.zip"

        st.success(f"✅ Готово! Архив: {zip_name}")
        st.download_button(f"📥 Скачать {zip_name}", zip_buffer.getvalue(), zip_name)

    except Exception as e:
        st.error(f"Ошибка: {e}")
