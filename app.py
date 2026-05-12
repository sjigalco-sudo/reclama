import streamlit as st
import pandas as pd
import io
import zipfile
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Global24 SLBlock Gen", page_icon="🎬")
st.title("🎬 Генератор SLBlock для Forward")

# ПУТЬ — проверьте его еще раз. В образце был именно такой:
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
    # Строго по вашему образцу: без заголовка XML, без лишних пробелов
    lines = []
    header = '<slblock Source="list" Type="accurate" Sec="0.000" Include_subfolders="no" Path="" '
    header += 'cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2'
    lines.append(header)
    
    # Заставка IN
    lines.append(f'<item file="{BASE_PATH}PIBLICITATE 1 IN.mp4" in="0.000" dur="0.000" />')
    
    for _, row in items.iterrows():
        id_val = str(row['ID']).split('.')[0]
        name_val = str(row['Name']).strip()
        
        # Проверка расширения
        lower_name = name_val.lower()
        if any(lower_name.endswith(ext) for ext in ['.mp4', '.mov', '.tga', '.mpg', '.avi']):
            full_name = f"{id_val}_{name_val}"
        else:
            full_name = f"{id_val}_{name_val}.mp4"
            
        lines.append(f'<item file="{BASE_PATH}{full_name}" in="0.000" dur="0.000" />')
    
    # Заставка OUT
    lines.append(f'<item file="{BASE_PATH}PIBLICITATE 1 OUT.mp4" in="0.000" dur="0.000" />')
    lines.append('</slblock>')
    
    # Соединяем через стандартный Windows-перенос строки
    return "\r\n".join(lines)

uploaded_file = st.file_uploader("Загрузите Excel", type=["xls", "xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Столбцы: 2 (Время), 6 (Название), 9 (ID)
        df_res = df.iloc[:, [2, 6, 9]].copy()
        df_res.columns = ['Raw_Time', 'Name', 'ID']
        
        # Протягиваем время и чистим пустые строки
        df_res['Block_Time_Str'] = df_res['Raw_Time'].ffill().apply(format_excel_time)
        df_res = df_res.dropna(subset=['Name', 'ID'])
        
        # Группируем блоки
        grouped = df_res.groupby('Block_Time_Str', sort=False)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for time_str, items in grouped:
                content = create_slblock_content(items)
                # Важно: кодируем в utf-8 БЕЗ BOM
                zip_file.writestr(f"{time_str}.SLBlock", content.encode('utf-8'))

        st.success(f"Готово! Создано {len(grouped)} файлов.")
        st.download_button("📥 Скачать блоки (.zip)", zip_buffer.getvalue(), f"Forward_Blocks.zip")

    except Exception as e:
        st.error(f"Ошибка в программе: {e}")
