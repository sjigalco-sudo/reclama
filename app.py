import streamlit as st
import pandas as pd
import io
import zipfile
import os
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Global24 SLBlock Precision", page_icon="🎬")
st.title("🎬 Генератор SLBlock (Байт-в-байт)")

BASE_PATH = r"I:\RECLAMA 2026"

def format_time_for_name(x):
    if isinstance(x, (datetime, time)):
        return x.strftime('%H-%M-%S')
    if isinstance(x, (int, float)):
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).replace(':', '-').zfill(8)
    return str(x).replace(':', '-')

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
                
                # Собираем контент по кусочкам, чтобы контролировать каждый символ
                parts = []
                # Заголовок
                parts.append(f'<slblock Source="list" Type="accurate" Sec="{total_block_sec:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2\r\n')
                
                # Входная заставка
                parts.append(f'  <item file="{BASE_PATH}\\PIBLICITATE {pub_num} IN.mp4" in="0.000" dur="{dur_in:.3f}" />\r\n')
                
                # Ролики
                for _, row in items.iterrows():
                    id_val = str(row['ID']).split('.')[0]
                    name_val = str(row['Name']).strip()
                    dur_val = float(row['Dur'])
                    ext = "" if any(name_val.lower().endswith(e) for e in ['.mov', '.mp4', '.tga', '.mpg']) else ".mov"
                    parts.append(f'  <item file="{BASE_PATH}\\{id_val}_{name_val}{ext}" in="0.000" dur="{dur_val:.3f}" />\r\n')
                
                # Выходная заставка
                parts.append(f'  <item file="{BASE_PATH}\\PIBLICITATE {pub_num} OUT.mp4" in="0.000" dur="{dur_out:.3f}" />')
                
                # СТРОГО: Приклеиваем закрывающий тег без переноса
                parts.append('</slblock>')
                
                final_string = "".join(parts)
                filename = f"{time_str}_{base_name}.slblock"
                
                # Кодируем в CP1251 (Windows-1251)
                encoded_data = final_string.encode('cp1251', errors='replace')
                zip_file.writestr(filename, encoded_data)
        
        st.success(f"Готово! Блоков: {len(grouped)}")
        st.download_button(
            label="📥 Скачать SLBLOCK (Точная копия)",
            data=zip_buffer.getvalue(),
            file_name=f"Fixed_SLBlocks_{base_name}.zip",
            mime="application/zip"
        )
        
        # Сравнение структуры в превью
        st.divider()
        st.write("Последние 60 символов (должно быть `/> </slblock>` в одну строку):")
        st.text(final_string[-60:])

    except Exception as e:
        st.error(f"Ошибка: {e}")
