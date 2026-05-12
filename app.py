import streamlit as st
import pandas as pd
import io
import zipfile
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Global24 SLBlock Gen", page_icon="🎬")
st.title("🎬 Генератор SLBlock для Forward")

# Настройки путей (измените, если папка другая)
BASE_PATH = "I:\\RECLAMA 2026\\"

def format_excel_time(x):
    try:
        if isinstance(x, (datetime, time)):
            return x.strftime('%H-%M-%S')
        if isinstance(x, (int, float)):
            total_seconds = int(round(x * 86400))
            return str(timedelta(seconds=total_seconds)).zfill(8).replace(':', '-')
        return str(x).replace(':', '-')
    except:
        return "00-00-00"

def create_slblock_content(items):
    # Точная структура из вашего образца
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n' # Добавили заголовок XML
    xml += '<slblock Source="list" Type="accurate" Sec="0.000" Include_subfolders="no" Path="" '
    xml += 'cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2\n'
    
    # Заставка IN
    xml += f'  <item file="{BASE_PATH}PIBLICITATE 1 IN.mp4" in="0.000" dur="0.000" />\n'
    
    for _, row in items.iterrows():
        id_val = str(row['ID']).split('.')[0]
        name_val = str(row['Name']).strip()
        
        # Проверяем, есть ли уже расширение в названии
        if not (name_val.lower().endswith('.mp4') or name_val.lower().endswith('.mov') or name_val.lower().endswith('.tga')):
            file_name = f"{id_val}_{name_val}.mp4" # Добавляем .mp4 по умолчанию
        else:
            file_name = f"{id_val}_{name_val}"
            
        xml += f'  <item file="{BASE_PATH}{file_name}" in="0.000" dur="0.000" />\n'
    
    # Заставка OUT
    xml += f'  <item file="{BASE_PATH}PIBLICITATE 1 OUT.mp4" in="0.000" dur="0.000" />\n'
    xml += '</slblock>'
    return xml

uploaded_file = st.file_uploader("Загрузите Excel GLOBAL24", type=["xls", "xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, skiprows=6)
        df_res = df.iloc[:, [2, 6, 9]].copy()
        df_res.columns = ['Raw_Time', 'Name', 'ID']
        
        # Группировка
        df_res['Block_Time_Str'] = df_res['Raw_Time'].ffill().apply(format_excel_time)
        df_res = df_res.dropna(subset=['Name', 'ID'])
        grouped = df_res.groupby('Block_Time_Str', sort=False)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for time_str, items in grouped:
                content = create_slblock_content(items)
                # Кодируем в UTF-8 без BOM для совместимости с Forward
                zip_file.writestr(f"{time_str}.SLBlock", content.encode('utf-8'))

        st.success(f"Создано {len(grouped)} блоков. Проверьте путь: {BASE_PATH}")
        st.download_button("📥 Скачать блоки (.zip)", zip_buffer.getvalue(), f"Forward_Blocks.zip")

    except Exception as e:
        st.error(f"Ошибка: {e}")
