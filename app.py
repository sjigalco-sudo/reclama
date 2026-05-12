import streamlit as st
import pandas as pd
import io
import zipfile
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Global24 SLBlock Fix", page_icon="🎬")
st.title("🎬 Генератор SLBlock (Final Fix)")

BASE_PATH = "I:\\RECLAMA 2026\\"

def format_time_for_name(x):
    if isinstance(x, (datetime, time)): return x.strftime('%H-%M-%S')
    if isinstance(x, (int, float)):
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).zfill(8).replace(':', '-')
    return str(x).replace(':', '-')

def create_slblock_content(items, block_num):
    # Длительности заставок из ваших оригиналов
    dur_in = 5.980
    dur_out = 6.580
    
    # Чередуем заставки 1, 2, 3, 4, 5 (как в ваших примерах)
    pub_num = ((block_num - 1) % 5) + 1 
    
    # Считаем точную сумму Sec
    total_dur = dur_in + items['Dur'].sum() + dur_out
    
    # Собираем строки без лишних пробелов в начале/конце
    header = f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="" '
    header += 'cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2'
    
    lines = [header]
    lines.append(f'  <item file="{BASE_PATH}PIBLICITATE {pub_num} IN.mp4" in="0.000" dur="{dur_in:.3f}" />')
    
    for _, row in items.iterrows():
        id_val = str(row['ID']).split('.')[0]
        name_val = str(row['Name']).strip()
        duration = float(row['Dur'])
        
        # Реклама — всегда .mov, если не указано иное
        if not any(name_val.lower().endswith(ext) for ext in ['.mov', '.mp4', '.tga']):
            full_name = f"{id_val}_{name_val}.mov"
        else:
            full_name = f"{id_val}_{name_val}"
            
        lines.append(f'  <item file="{BASE_PATH}{full_name}" in="0.000" dur="{duration:.3f}" />')
    
    lines.append(f'  <item file="{BASE_PATH}PIBLICITATE {pub_num} OUT.mp4" in="0.000" dur="{dur_out:.3f}" />')
    lines.append('</slblock>')
    
    # Склеиваем через \r\n, но БЕЗ переноса в самом конце файла
    return "\r\n".join(lines)

uploaded_file = st.file_uploader("Загрузите Excel GLOBAL24", type=["xls", "xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, skiprows=6)
        # Столбцы: 2-Время блока, 6-Название ролика, 7-Длительность, 9-ID
        df_res = df.iloc[:, [2, 6, 7, 9]].copy()
        df_res.columns = ['Raw_Time', 'Name', 'Dur', 'ID']
        
        df_res['Block_Time'] = df_res['Raw_Time'].ffill()
        df_res = df_res.dropna(subset=['Name', 'ID'])
        
        # Группируем блоки в том порядке, в котором они идут в Excel
        grouped = df_res.groupby('Block_Time', sort=False)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, (block_time, items) in enumerate(grouped, 1):
                file_name = format_time_for_name(block_time)
                content = create_slblock_content(items, i)
                # Кодируем строго в UTF-8 без BOM
                zip_file.writestr(f"{file_name}.SLBlock", content.encode('utf-8'))

        st.success(f"Готово! Создано {len(grouped)} блоков.")
        st.download_button("📥 Скачать исправленные блоки", zip_buffer.getvalue(), "Forward_Final_Fix.zip")

    except Exception as e:
        st.error(f"Ошибка: {e}")
