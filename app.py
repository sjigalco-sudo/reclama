import streamlit as st
import pandas as pd
import io
import zipfile
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Global24 SLBlock Pro", page_icon="🎬")
st.title("🎬 Генератор SLBlock Pro")

BASE_PATH = "I:\\RECLAMA 2026\\"

def format_excel_time(x):
    if isinstance(x, (datetime, time)): return x.strftime('%H-%M-%S')
    if isinstance(x, (int, float)):
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).zfill(8).replace(':', '-')
    return str(x).replace(':', '-')

def create_slblock_content(items, block_index):
    # Длительности заставок из ваших файлов
    dur_in = 5.980
    dur_out = 6.580
    
    # Определяем номер заставки (цикл 1-2-3-4-5...)
    # Основываясь на ваших файлах: 6.1 -> IN 1, 9.1 -> IN 2, 9.2 -> IN 3 и т.д.
    # Для простоты можно использовать остаток от деления или просто 1, если не критично
    pub_num = ((block_index - 1) % 5) + 1 
    
    # Считаем общую длительность блока
    total_dur = dur_in + items['Dur'].sum() + dur_out
    
    lines = []
    header = f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="" '
    header += 'cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2'
    lines.append(header)
    
    # Добавляем IN
    lines.append(f'  <item file="{BASE_PATH}PIBLICITATE {pub_num} IN.mp4" in="0.000" dur="{dur_in:.3f}" />')
    
    # Добавляем ролики
    for _, row in items.iterrows():
        id_val = str(row['ID']).split('.')[0]
        name_val = str(row['Name']).strip()
        duration = float(row['Dur'])
        
        # Если расширения нет, ставим .mov
        if not any(name_val.lower().endswith(ext) for ext in ['.mov', '.mp4', '.tga']):
            full_name = f"{id_val}_{name_val}.mov"
        else:
            full_name = f"{id_val}_{name_val}"
            
        lines.append(f'  <item file="{BASE_PATH}{full_name}" in="0.000" dur="{duration:.3f}" />')
    
    # Добавляем OUT
    lines.append(f'  <item file="{BASE_PATH}PIBLICITATE {pub_num} OUT.mp4" in="0.000" dur="{dur_out:.3f}" />')
    lines.append('</slblock>')
    
    return "\r\n".join(lines)

uploaded_file = st.file_uploader("Загрузите оригинал GLOBAL24 .xls", type=["xls", "xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, skiprows=6)
        # Столбцы: 2-Время блока, 6-Название, 7-Длительность ролика, 9-ID
        df_res = df.iloc[:, [2, 6, 7, 9]].copy()
        df_res.columns = ['Raw_Time', 'Name', 'Dur', 'ID']
        
        df_res['Block_Time'] = df_res['Raw_Time'].ffill()
        df_res = df_res.dropna(subset=['Name', 'ID'])
        
        grouped = df_res.groupby('Block_Time', sort=False)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, (block_time, items) in enumerate(grouped, 1):
                time_str = format_excel_time(block_time)
                # Передаем порядковый номер блока для смены заставок
                content = create_slblock_content(items, i)
                zip_file.writestr(f"{time_str}.SLBlock", content.encode('utf-8'))

        st.success(f"Готово! Сгенерировано {len(grouped)} блоков с расчетом времени.")
        st.download_button("📥 Скачать архив для Forward", zip_buffer.getvalue(), "Forward_Final.zip")

    except Exception as e:
        st.error(f"Ошибка: {e}")
