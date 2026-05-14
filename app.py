import streamlit as st
import pandas as pd
import io
import zipfile
import os
import re
from datetime import timedelta, datetime, time

# --- КОНСТАНТЫ ---
PASSWORD = "Global_Admin_2026"
PATH_MAIN = r"I:\RECLAMA 2026"
PATH_TOPSHOP = r"I:\TOPSHOP"
TS_FILE = "teleshopping1.mp4"
TS_DUR = 7.600

st.set_page_config(page_title="Global 24 | Generator", page_icon="🌐", layout="wide")

# --- Авторизация ---
if 'auth_global' not in st.session_state:
    st.session_state['auth_global'] = False

if not st.session_state['auth_global']:
    st.title("🔒 Global 24: Вход")
    pwd = st.text_input("Пароль:", type="password")
    if st.button("Войти"):
        if pwd == PASSWORD:
            st.session_state['auth_global'] = True
            st.rerun()
    st.stop()

st.title("🌐 GLOBAL 24: УНИВЕРСАЛЬНЫЙ ГЕНЕРАТОР")

# --- Функции ---
def extract_date_digits(text):
    """Оставляет только цифры из строки даты (напр. 11.5.2026 -> 11052026)"""
    if pd.isna(text): return ""
    digits = re.sub(r'\D', '', str(text))
    return digits

def format_time_hh_mm(x):
    if isinstance(x, (datetime, time)): return x.strftime('%H-%M')
    if isinstance(x, (int, float)):
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).zfill(8)[:5].replace(':', '-')
    # Обработка строки типа 09:00:00
    s = str(x).strip()
    return s[:5].replace(':', '-')

def xml_escape(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Настройки")
    ad_type = st.radio("Тип рекламы:", ["Основная (I:\RECLAMA 2026)", "TopShop (I:\TOPSHOP)"])
    
    st.divider()
    st.subheader("📁 Формат MP4")
    mp4_input = st.text_area("ID для .mp4 (через запятую):", value="6856, 6857")
    mp4_ids = [x.strip() for x in mp4_input.split(",") if x.strip()]
    
    st.divider()
    uploaded_file = st.file_uploader("Загрузить медиа-план", type=["xls", "xlsx"])
    
    if st.button("Выйти"):
        st.session_state['auth_global'] = False
        st.rerun()

# --- Логика ---
if uploaded_file:
    try:
        mode_topshop = True if ad_type == "TopShop (I:\TOPSHOP)" else False
        current_path = PATH_TOPSHOP if mode_topshop else PATH_MAIN
        
        # Читаем файл целиком без пропуска строк, чтобы поймать заголовки дат
        df_raw = pd.read_excel(uploaded_file, header=None)
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            
            if mode_topshop:
                current_date_prefix = ""
                # Проходим по строкам для TopShop
                for index, row in df_raw.iterrows():
                    val_col0 = str(row[0])
                    
                    # Если строка содержит дату (разделитель дней)
                    if any(day in val_col0 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
                        current_date_prefix = extract_date_digits(val_col0)
                        continue
                    
                    # Если это строка с данными (проверяем наличие времени в кол. 1 и ID в кол. 3)
                    if pd.notna(row[1]) and ":" in str(row[1]) and pd.notna(row[3]):
                        time_val = row[1]
                        time_str = format_time_hh_mm(time_val)
                        
                        # Собираем имя файла: ДатаЦифрами_Время
                        file_name = f"{current_date_prefix}_{time_str}.slblock" if current_date_prefix else f"{time_str}.slblock"
                        
                        # Для TopShop обычно один блок = один файл, но если нужно группировать, 
                        # тут можно добавить логику сбора. В TopShop обычно каждый выход — отдельный файл.
                        
                        dur = float(row[4])
                        total_dur = TS_DUR + dur + TS_DUR
                        
                        id_clean = str(row[3]).strip()
                        nm = str(row[2]).strip()
                        full_name = f"{id_clean}__{nm}.mp4" # Двойное подчеркивание
                        
                        xml_lines = [
                            f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2',
                            f'  <item file="{xml_escape(current_path)}\\{TS_FILE}" in="0.000" dur="{TS_DUR:.3f}" />',
                            f'  <item file="{xml_escape(current_path)}\\{full_name}" in="0.000" dur="{dur:.3f}" />',
                            f'  <item file="{xml_escape(current_path)}\\{TS_FILE}" in="0.000" dur="{TS_DUR:.3f}" />',
                            '</slblock>'
                        ]
                        zip_file.writestr(file_name, "\r\n".join(xml_lines).encode('utf-16'))
            
            else:
                # ЛОГИКА ДЛЯ ОСНОВНОЙ РЕКЛАМЫ (Global 24)
                df = pd.read_excel(uploaded_file, skiprows=6)
                df_res = df.iloc[:, [2, 6, 7, 9]].copy()
                df_res.columns = ['Block_Time', 'Name', 'Dur', 'ID']
                df_res['Block_Time'] = df_res['Block_Time'].ffill()
                df_res = df_res.dropna(subset=['ID'])
                
                grouped = df_res.groupby('Block_Time', sort=False)
                for i, (block_time, items) in enumerate(grouped, 1):
                    time_filename = format_time_hh_mm(block_time)
                    pub_num = ((i - 1) % 5) + 1
                    total_dur = 5.980 + items['Dur'].sum() + 6.580
                    
                    xml_lines = [f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2']
                    xml_lines.append(f'  <item file="{xml_escape(PATH_MAIN)}\\PIBLICITATE {pub_num} IN.mp4" in="0.000" dur="5.980" />')
                    
                    for _, row in items.iterrows():
                        id_c = str(row['ID']).split(".")[0]
                        nm_c = str(row['Name']).strip()
                        ext = ".mp4" if id_c in mp4_ids else ".mov"
                        xml_lines.append(f'  <item file="{xml_escape(PATH_MAIN)}\\{id_c}_{nm_c}{ext}" in="0.000" dur="{float(row["Dur"]):.3f}" />')
                    
                    xml_lines.append(f'  <item file="{xml_escape(PATH_MAIN)}\\PIBLICITATE {pub_num} OUT.mp4" in="0.000" dur="6.580" />')
                    xml_lines.append('</slblock>')
                    zip_file.writestr(f"{time_filename}.slblock", "\r\n".join(xml_lines).encode('utf-16'))

        st.success("✅ Файлы успешно сформированы!")
        st.download_button("📥 Скачать архив SLBlocks", zip_buffer.getvalue(), f"Global_Blocks_{uploaded_file.name}.zip")

    except Exception as e:
        st.error(f"Ошибка: {e}")
