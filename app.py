import streamlit as st
import pandas as pd
import io
import zipfile
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Global24 SLBlock Gen", page_icon="🎬")
st.title("🎬 Генератор SLBlock для Forward")

# Настройка пути — проверьте, чтобы в конце был обратный слеш
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
    # Убираем XML заголовок, так как в вашем образце его нет
    # Параметр Sec="42.560" возьмем из вашего примера, обычно это общая длительность, 
    # но Forward часто пересчитывает её сам при загрузке.
    xml = '<slblock Source="list" Type="accurate" Sec="0.000" Include_subfolders="no" Path="" '
    xml += 'cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2\r\n'
    
    # Заставка IN
    xml += f'  <item file="{BASE_PATH}PIBLICITATE 1 IN.mp4" in="0.000" dur="0.000" />\r\n'
    
    for _, row in items.iterrows():
        id_val = str(row['ID']).split('.')[0]
        name_val = str(row['Name']).strip()
        
        # Если в Excel уже есть расширение (.mp4, .mov, .tga), не добавляем ничего.
        # Если нет — добавляем .mp4
        lower_name = name_val.lower()
        if any(lower_name.endswith(ext) for ext in ['.mp4', '.mov', '.tga', '.mpg', '.avi']):
            full_name = f"{id_val}_{name_val}"
        else:
            full_name = f"{id_val}_{name_val}.mp4"
            
        xml += f'  <item file="{BASE_PATH}{full_name}" in="0.000" dur="0.000" />\r\n'
    
    # Заставка OUT
    xml += f'  <item file="{BASE_PATH}PIBLICITATE 1 OUT.mp4" in="0.000" dur="0.000" />\r\n'
    xml += '</slblock>'
    return xml

uploaded_file = st.file_uploader("Загрузите Excel GLOBAL24", type=["xls", "xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Индексы: 2 (Время), 6 (Название), 9 (ID)
        df_res = df.iloc[:, [2, 6, 9]].copy()
        df_res.columns = ['Raw_Time', 'Name', 'ID']
        
        # Группировка по времени
        df_res['Block_Time_Str'] = df_res['Raw_Time'].ffill().apply(format_excel_time)
        
        # Важно: удаляем строки, где нет ID или Названия, чтобы не создавать пустые айтемы
        df_res = df_res.dropna(subset=['Name', 'ID'])
        
        grouped = df_res.groupby('Block_Time_Str', sort=False)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for time_str, items in grouped:
                content = create_slblock_content(items)
                # Forward чувствителен к концам строк. Используем стандарт Windows \r\n
                # И кодировку UTF-8 без заголовка
                zip_file.writestr(f"{time_str}.SLBlock", content.encode('utf-8'))

        st.success(f"Готово! Сформировано {len(grouped)} блоков.")
        st.download_button("📥 Скачать готовые .SLBlock", zip_buffer.getvalue(), f"Forward_Blocks.zip")

    except Exception as e:
        st.error(f"Ошибка: {e}")
