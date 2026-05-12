import streamlit as st
import pandas as pd
import io
import zipfile
import os
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Global24 SLBlock Generator", page_icon="🎬")
st.title("🎬 Генератор SLBlock (Исправленный формат)")

BASE_PATH = r"I:\RECLAMA 2026"

def format_time_for_name(x):
    if isinstance(x, (datetime, time)):
        return x.strftime('%H-%M-%S')
    if isinstance(x, (int, float)):
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).replace(':', '-').zfill(8)
    return str(x).replace(':', '-')

uploaded_file = st.file_uploader("Загрузите Excel файл", type=["xls", "xlsx"])

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
                
                # Формируем структуру ТОЧНО как в вашем файле (без <?xml?>)
                # Используем \r\n для совместимости с Windows
                lines = []
                header = f'<slblock Source="list" Type="accurate" Sec="{total_block_sec:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2'
                lines.append(header)
                
                # Добавляем элементы
                lines.append(f'  <item file="{BASE_PATH}\\PIBLICITATE {pub_num} IN.mp4" in="0.000" dur="{dur_in:.3f}" />')
                
                for _, row in items.iterrows():
                    id_val = str(row['ID']).split('.')[0]
                    name_val = str(row['Name']).strip()
                    dur_val = float(row['Dur'])
                    ext = "" if any(name_val.lower().endswith(e) for e in ['.mov', '.mp4', '.tga', '.mpg']) else ".mov"
                    
                    lines.append(f'  <item file="{BASE_PATH}\\{id_val}_{name_val}{ext}" in="0.000" dur="{dur_val:.3f}" />')
                
                lines.append(f'  <item file="{BASE_PATH}\\PIBLICITATE {pub_num} OUT.mp4" in="0.000" dur="{dur_out:.3f}" />')
                lines.append('</slblock>')
                
                # Соединяем через Windows-перенос строки
                xml_content = "\r\n".join(lines)
                
                filename = f"{time_str}_{base_name}.slblock"
                # Записываем в UTF-8 без BOM, как в оригинале
                zip_file.writestr(filename, xml_content.encode('utf-8'))
        
        st.success(f"Готово! Блоков: {len(grouped)}")
        st.download_button(
            label="📥 Скачать архив SLBLOCK",
            data=zip_buffer.getvalue(),
            file_name=f"SLBlocks_{base_name}.zip",
            mime="application/zip"
        )
        
        st.divider()
        st.write("**Проверка структуры (должна быть 1-в-1 как в образце):**")
        st.code(xml_content, language='xml')

    except Exception as e:
        st.error(f"Ошибка: {e}")
