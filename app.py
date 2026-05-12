import streamlit as st
import pandas as pd
import io
import zipfile
import os
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Global24 SLBlock UTF16", page_icon="🎬")
st.title("🎬 Генератор SLBlock (Кодировка UTF-16LE)")

BASE_PATH = r"I:\RECLAMA 2026"

def format_time_only(x):
    if isinstance(x, (datetime, time)):
        return x.strftime('%H-%M-%S')
    if isinstance(x, (int, float)):
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).replace(':', '-').zfill(8)
    return str(x).replace(':', '-')

uploaded_file = st.file_uploader("Загрузите Excel", type=["xls", "xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, skiprows=6)
        df_res = df.iloc[:, [2, 6, 7, 9]].copy()
        df_res.columns = ['Block_Time', 'Name', 'Dur', 'ID']
        df_res['Block_Time'] = df_res['Block_Time'].ffill()
        df_res = df_res.dropna(subset=['ID'])
        
        grouped = df_res.groupby('Block_Time', sort=False)
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, (block_time, items) in enumerate(grouped, 1):
                time_filename = format_time_only(block_time)
                pub_num = ((i - 1) % 5) + 1 
                
                # Считаем общую длительность (хотя мы забили на точность длины, 
                # атрибут Sec в заголовке XML всё равно должен быть)
                total_block_sec = 5.980 + items['Dur'].sum() + 6.580
                
                # Собираем структуру (версия 2)
                lines = []
                lines.append(f'<slblock Source="list" Type="accurate" Sec="{total_block_sec:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2')
                
                lines.append(f'  <item file="{BASE_PATH}\\PIBLICITATE {pub_num} IN.mp4" in="0.000" dur="5.980" />')
                
                for _, row in items.iterrows():
                    id_val = str(row['ID']).split('.')[0]
                    name_val = str(row['Name']).strip()
                    dur_val = float(row['Dur'])
                    ext = "" if any(name_val.lower().endswith(e) for e in ['.mov', '.mp4', '.tga', '.mpg']) else ".mov"
                    lines.append(f'  <item file="{BASE_PATH}\\{id_val}_{name_val}{ext}" in="0.000" dur="{dur_val:.3f}" />')
                
                lines.append(f'  <item file="{BASE_PATH}\\PIBLICITATE {pub_num} OUT.mp4" in="0.000" dur="6.580" />')
                lines.append('</slblock>')
                
                content = "\r\n".join(lines)
                
                # ВАЖНО: Используем 'utf-16' (он автоматически добавит BOM FF FE в начало)
                # Это создаст файл в кодировке UTF-16 Little Endian
                raw_bytes = content.encode('utf-16')
                
                zip_file.writestr(f"{time_filename}.slblock", raw_bytes)
        
        st.success(f"Готово! Сгенерировано {len(grouped)} файлов в UTF-16LE.")
        st.download_button(
            label="📥 Скачать SLBLOCK (UTF-16LE)",
            data=zip_buffer.getvalue(),
            file_name=f"SLBlocks_UTF16LE.zip"
        )
        
        st.info("Теперь каждый файл начинается с байтов FF FE (BOM), что сообщает Форварду о кодировке UTF-16 Little Endian.")

    except Exception as e:
        st.error(f"Ошибка: {e}")
