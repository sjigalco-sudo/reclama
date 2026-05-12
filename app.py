import streamlit as st
import pandas as pd
import io
import zipfile
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Global24 Precision Fix", page_icon="🎬")
st.title("🎬 Генератор SLBlock (Точность 100%)")

BASE_PATH = "I:\\RECLAMA 2026\\"

def format_time_for_name(x):
    if isinstance(x, (datetime, time)): return x.strftime('%H-%M-%S')
    if isinstance(x, (int, float)):
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).zfill(8).replace(':', '-')
    return str(x).replace(':', '-')

def create_slblock_content(items, block_num):
    dur_in = 5.980
    dur_out = 6.580
    
    # Чередуем заставки 1-5
    pub_num = ((block_num - 1) % 5) + 1 
    
    # Считаем сумму с высокой точностью
    # Используем round(..., 3) чтобы избежать ошибок плавающей запятой
    items_dur_sum = round(items['Dur'].sum(), 3)
    total_dur = round(dur_in + items_dur_sum + dur_out, 3)
    
    lines = []
    # Форматируем Sec строго до 3 знаков
    header = f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="" '
    header += 'cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2'
    lines.append(header)
    
    # IN
    lines.append(f'  <item file="{BASE_PATH}PIBLICITATE {pub_num} IN.mp4" in="0.000" dur="{dur_in:.3f}" />')
    
    for _, row in items.iterrows():
        id_val = str(row['ID']).split('.')[0]
        name_val = str(row['Name']).strip()
        # Принудительно берем длительность как float с точностью
        duration = float(row['Dur'])
        
        if not any(name_val.lower().endswith(ext) for ext in ['.mov', '.mp4', '.tga']):
            full_name = f"{id_val}_{name_val}.mov"
        else:
            full_name = f"{id_val}_{name_val}"
            
        # Форматируем dur ролика строго до 3 знаков (например 40.040)
        lines.append(f'  <item file="{BASE_PATH}{full_name}" in="0.000" dur="{duration:.3f}" />')
    
    # OUT
    lines.append(f'  <item file="{BASE_PATH}PIBLICITATE {pub_num} OUT.mp4" in="0.000" dur="{dur_out:.3f}" />')
    lines.append('</slblock>')
    
    # Соединяем без финального переноса строки
    return "\r\n".join(lines)

uploaded_file = st.file_uploader("Загрузите Excel", type=["xls", "xlsx"])

if uploaded_file:
    try:
        # Читаем Excel, принудительно указывая, что Dur — это число
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        df_res = df.iloc[:, [2, 6, 7, 9]].copy()
        df_res.columns = ['Raw_Time', 'Name', 'Dur', 'ID']
        
        # Заполняем время и убираем мусор
        df_res['Block_Time'] = df_res['Raw_Time'].ffill()
        df_res = df_res.dropna(subset=['Name', 'ID'])
        
        # Преобразуем длительность в числа, заменяя ошибки на 0
        df_res['Dur'] = pd.to_numeric(df_res['Dur'], errors='coerce').fillna(0.0)

        grouped = df_res.groupby('Block_Time', sort=False)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, (block_time, items) in enumerate(grouped, 1):
                file_name = format_time_for_name(block_time)
                content = create_slblock_content(items, i)
                zip_file.writestr(f"{file_name}.SLBlock", content.encode('utf-8'))

        st.success("Готово! Теперь длительность должна совпадать до миллисекунды.")
        st.download_button("📥 Скачать точные блоки", zip_buffer.getvalue(), "Forward_Final.zip")

    except Exception as e:
        st.error(f"Ошибка: {e}")
