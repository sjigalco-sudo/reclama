import streamlit as st
import pandas as pd
import io
import zipfile
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Global24 SLBlock Gen", page_icon="🎬")

st.title("🎬 Генератор SLBlock — GLOBAL24")

uploaded_file = st.file_uploader("Выберите файл .xls или .xlsx", type=["xls", "xlsx"])

def format_excel_time(x):
    try:
        # Если это уже объект time или datetime, берем только время
        if isinstance(x, (datetime, time)):
            return x.strftime('%H-%M-%S')
        # Если это число Excel (доля суток)
        if isinstance(x, (int, float)):
            total_seconds = int(round(x * 86400))
            return str(timedelta(seconds=total_seconds)).zfill(8).replace(':', '-')
        return str(x).replace(':', '-')
    except:
        return "00-00-00"

def create_slblock_content(items):
    xml = '<slblock Source="list" Type="accurate" Sec="0.000" Include_subfolders="no" Path="" '
    xml += 'cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2\n'
    
    # Путь к папке (два обратных слеша для Windows)
    base_path = "I:\\\\RECLAMA 2026\\\\"
    
    # Добавляем в начало заставку IN
    xml += f'  <item file="{base_path}PIBLICITATE 1 IN.mp4" in="0.000" dur="0.000" />\n'
    
    for _, row in items.iterrows():
        id_val = str(row['ID']).split('.')[0]
        name_val = str(row['Name'])
        file_name = f"{id_val}_{name_val}"
        xml += f'  <item file="{base_path}{file_name}" in="0.000" dur="0.000" />\n'
    
    # Добавляем в конец заставку OUT
    xml += f'  <item file="{base_path}PIBLICITATE 1 OUT.mp4" in="0.000" dur="0.000" />\n'
    xml += '</slblock>'
    return xml

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Берем столбцы: 2 (время), 6 (название), 9 (ID)
        df_res = df.iloc[:, [2, 6, 9]].copy()
        df_res.columns = ['Raw_Time', 'Name', 'ID']

        # Ключевое исправление: преобразуем всё в строковый формат времени для группировки
        # Это исключает ошибку сравнения datetime и time
        df_res['Block_Time_Str'] = df_res['Raw_Time'].ffill().apply(format_excel_time)
        
        # Очистка
        df_res = df_res.dropna(subset=['Name', 'ID'])
        
        # Группируем по строковому значению времени
        grouped = df_res.groupby('Block_Time_Str', sort=False)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for time_str, items in grouped:
                slblock_content = create_slblock_content(items)
                zip_file.writestr(f"{time_str}.SLBlock", slblock_content)

        st.success(f"Готово! Сформировано блоков: {len(grouped)}")

        st.download_button(
            label="📥 Скачать архив .SLBlock",
            data=zip_buffer.getvalue(),
            file_name=f"Blocks_{uploaded_file.name.split('.')[0]}.zip",
            mime="application/zip"
        )

    except Exception as e:
        st.error(f"Ошибка: {e}")
