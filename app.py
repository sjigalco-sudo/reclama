import streamlit as st
import pandas as pd
import io
import zipfile
import os
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Global24 SLBlock Generator", page_icon="🎬")
st.title("🎬 Генератор SLBlock для Global 24")

# Константа пути (можно менять здесь)
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
        
        # Столбцы: Время (2), Название (6), Длительность (7), ID (9)
        df_res = df.iloc[:, [2, 6, 7, 9]].copy()
        df_res.columns = ['Block_Time', 'Name', 'Dur', 'ID']
        df_res['Block_Time'] = df_res['Block_Time'].ffill()
        df_res = df_res.dropna(subset=['ID'])
        
        grouped = df_res.groupby('Block_Time', sort=False)
        
        # Создаем архив в памяти
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, (block_time, items) in enumerate(grouped, 1):
                time_str = format_time_for_name(block_time)
                pub_num = ((i - 1) % 5) + 1 
                
                # Собираем XML структуру slblock
                xml_lines = []
                xml_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
                xml_lines.append('<slblock Source="list" Type="accurate" Sec="0.000" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2')
                
                # 1. Входная заставка
                xml_lines.append(f'  <item file="{BASE_PATH}\\PIBLICITATE {pub_num} IN.mp4" in="0.000" dur="5.980" />')
                
                # 2. Ролики из блока
                for _, row in items.iterrows():
                    id_val = str(row['ID']).split('.')[0]
                    name_val = str(row['Name']).strip()
                    dur_val = float(row['Dur'])
                    # Проверка расширения
                    ext = "" if any(name_val.lower().endswith(e) for e in ['.mov', '.mp4', '.tga', '.mpg']) else ".mov"
                    
                    file_path = f"{BASE_PATH}\\{id_val}_{name_val}{ext}"
                    xml_lines.append(f'  <item file="{file_path}" in="0.000" dur="{dur_val:.3f}" />')
                
                # 3. Выходная заставка
                xml_lines.append(f'  <item file="{BASE_PATH}\\PIBLICITATE {pub_num} OUT.mp4" in="0.000" dur="6.580" />')
                xml_lines.append('</slblock>')
                
                slblock_content = "\n".join(xml_lines)
                
                # Имя файла: Время_НазваниеExcel.slblock
                filename = f"{time_str}_{base_name}.slblock"
                zip_file.writestr(filename, slblock_content.encode('utf-8'))
        
        st.success(f"Архив готов! Сгенерировано блоков: {len(grouped)}")
        
        st.download_button(
            label=f"📥 Скачать архив блоков (.zip)",
            data=zip_buffer.getvalue(),
            file_name=f"SLBlocks_{base_name}.zip",
            mime="application/zip"
        )
        
        # Предпросмотр кода одного из файлов
        st.divider()
        st.write("**Пример структуры внутри .slblock:**")
        st.code(slblock_content, language='xml')

    except Exception as e:
        st.error(f"Ошибка: {e}")
