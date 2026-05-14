import streamlit as st
import pandas as pd
import io
import zipfile
import os
from datetime import timedelta, datetime, time

# --- КОНСТАНТЫ И НАСТРОЙКИ ---
PASSWORD = "Global_Admin_2026"
FIXED_PATH = r"I:\RECLAMA 2026"  # Путь зафиксирован

st.set_page_config(page_title="Global 24 | Generator", page_icon="🌐", layout="wide")

# Авторизация
if 'auth_global' not in st.session_state:
    st.session_state['auth_global'] = False

if not st.session_state['auth_global']:
    st.title("🔒 Global 24: Вход")
    pwd = st.text_input("Пароль:", type="password", key="pwd_input")
    if st.button("Войти"):
        if pwd == PASSWORD:
            st.session_state['auth_global'] = True
            st.rerun()
        else:
            st.error("Неверный пароль")
    st.stop()

st.title("🌐 GLOBAL 24: ГЕНЕРАТОР ЭФИРА")

# --- Вспомогательные функции ---
def format_time_hh_mm(x):
    if isinstance(x, (datetime, time)): return x.strftime('%H-%M')
    if isinstance(x, (int, float)):
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).zfill(8)[:5].replace(':', '-')
    return str(x)[:5].replace(':', '-')

def xml_escape(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Настройки")
    
    st.subheader("📁 Формат MP4")
    # Список ID, которым нужно расширение .mp4 вместо .mov
    mp4_input = st.text_area("Введите ID через запятую:", 
                             value="6856, 6857",
                             help="Ролики с этими ID получат расширение .mp4")
    
    mp4_ids = [x.strip() for x in mp4_input.split(",") if x.strip()]
    
    st.divider()
    uploaded_file = st.file_uploader("Загрузить медиа-план (Excel)", type=["xls", "xlsx"])
    
    if st.button("Выйти"):
        st.session_state['auth_global'] = False
        st.rerun()

# --- Основная логика ---
if uploaded_file:
    try:
        base_name = os.path.splitext(uploaded_file.name)[0]
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Колонки: Время(2), Название(6), Длительность(7), ID(9)
        df_res = df.iloc[:, [2, 6, 7, 9]].copy()
        df_res.columns = ['Block_Time', 'Name', 'Dur', 'ID']
        df_res['Block_Time'] = df_res['Block_Time'].ffill()
        df_res = df_res.dropna(subset=['ID'])
        
        grouped = df_res.groupby('Block_Time', sort=False)
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, (block_time, items) in enumerate(grouped, 1):
                time_filename = format_time_hh_mm(block_time)
                pub_num = ((i - 1) % 5) + 1
                
                # Общая длительность с учетом заставок
                total_dur = 5.980 + items['Dur'].sum() + 6.580
                
                xml_lines = [
                    f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2',
                    f'  <item file="{xml_escape(FIXED_PATH)}\\PIBLICITATE {pub_num} IN.mp4" in="0.000" dur="5.980" />'
                ]
                
                for _, row in items.iterrows():
                    id_clean = str(row['ID']).split(".")[0]
                    nm = str(row['Name']).strip()
                    
                    # Проверяем расширение
                    if any(nm.lower().endswith(e) for e in ['.mov', '.mp4', '.tga', '.mpg']):
                        ext = ""
                    elif id_clean in mp4_ids:
                        ext = ".mp4"
                    else:
                        ext = ".mov"
                    
                    full_name = f"{id_clean}_{nm}{ext}"
                    xml_lines.append(f'  <item file="{xml_escape(FIXED_PATH)}\\{full_name}" in="0.000" dur="{float(row["Dur"]):.3f}" />')
                
                xml_lines.append(f'  <item file="{xml_escape(FIXED_PATH)}\\PIBLICITATE {pub_num} OUT.mp4" in="0.000" dur="6.580" />')
                xml_lines.append('</slblock>')
                
                # Запись в UTF-16LE (BOM добавится автоматически при таком способе)
                zip_file.writestr(f"{time_filename}.slblock", "\r\n".join(xml_lines).encode('utf-16'))

        st.success(f"✅ Файлы для Global 24 готовы! Путь в блоках: {FIXED_PATH}")
        st.download_button(f"📥 Скачать SLBlocks ({base_name})", zip_buffer.getvalue(), f"Global24_{base_name}.zip")

    except Exception as e:
        st.error(f"Ошибка при обработке: {e}")
