import streamlit as st
import pandas as pd
import io
import zipfile
import os
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Global24 SLBlock V3", page_icon="🎬")
st.title("🎬 Генератор SLBlock для Forward 5.10.x")

BASE_PATH = r"I:\RECLAMA 2026"

def format_time_for_name(x):
    if isinstance(x, (datetime, time)):
        return x.strftime('%H-%M-%S')
    if isinstance(x, (int, float)):
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).replace(':', '-').zfill(8)
    return str(x).replace(':', '-')

def xml_escape(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

uploaded_file = st.file_uploader("Загрузите Excel", type=["xls", "xlsx"])

if uploaded_file:
    try:
        base_name = os.path.splitext(uploaded_file.name)[0]
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        df_res = df.iloc[:, [2, 6, 7, 9]].copy()
        df_res.columns = ['Block_Time', 'Name', 'Dur', 'ID']
        df_res['Block_Time'] = df_res['Block_Time'].ffill()
        df_res = df_res.dropna(subset=['ID'])
        
        grouped = df_res.groupby('Block_Time', sort=False)
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, (block_time, items) in enumerate(grouped, 1):
                time_str = format_time_for_name(block_time)
                pub_num = ((i - 1) % 5) + 1 
                
                dur_in = 5.980
                dur_out = 6.580
                total_block_sec = dur_in + items['Dur'].sum() + dur_out
                
                # Формируем валидный XML версии 3
                xml_lines = [
                    '<?xml version="1.0" encoding="windows-1251"?>',
                    f'<slblock version="3" Source="list" Type="accurate" Sec="{total_block_sec:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">',
                    f'  <item file="{xml_escape(BASE_PATH)}\\PIBLICITATE {pub_num} IN.mp4" in="0.000" dur="{dur_in:.3f}" />'
                ]
                
                for _, row in items.iterrows():
                    id_val = xml_escape(str(row['ID']).split('.')[0])
                    name_val = xml_escape(str(row['Name']).strip())
                    dur_val = float(row['Dur'])
                    ext = "" if any(name_val.lower().endswith(e) for e in ['.mov', '.mp4', '.tga', '.mpg']) else ".mov"
                    
                    xml_lines.append(f'  <item file="{xml_escape(BASE_PATH)}\\{id_val}_{name_val}{ext}" in="0.000" dur="{dur_val:.3f}" />')
                
                xml_lines.append(f'  <item file="{xml_escape(BASE_PATH)}\\PIBLICITATE {pub_num} OUT.mp4" in="0.000" dur="{dur_out:.3f}" />')
                xml_lines.append('</slblock>')
                
                # Сборка контента с правильными переносами CRLF
                content = "\r\n".join(xml_lines)
                filename = f"{time_str}_{base_name}.slblock"
                
                # Кодирование в Windows-1251 (критично для кириллицы в путях)
                raw_bytes = content.encode('windows-1251', errors='replace')
                zip_file.writestr(filename, raw_bytes)
        
        st.success(f"Готово! Создано {len(grouped)} блоков для версии OnAir 3.9.x")
        st.download_button(
            label="📥 Скачать SLBLOCK (V3 Format)",
            data=zip_buffer.getvalue(),
            file_name=f"SLBlocks_V3_{base_name}.zip"
        )
        
        st.divider()
        st.write("**Как выглядит структура V3:**")
        st.code(content, language='xml')

    except Exception as e:
        st.error(f"Ошибка: {e}")
