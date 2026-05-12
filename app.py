import streamlit as st
import pandas as pd
import io
import zipfile
from datetime import timedelta

st.set_page_config(page_title="Global24 SLBlock Gen", page_icon="🎬")

st.title("🎬 Генератор SLBlock — GLOBAL24")
st.info("Загрузите Excel, чтобы получить архив с готовыми блоками для эфира.")

uploaded_file = st.file_uploader("Выберите файл .xls или .xlsx", type=["xls", "xlsx"])

def format_excel_time(x):
    try:
        if pd.isna(x) or isinstance(x, str): return str(x)
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).zfill(8).replace(':', '-')
    except:
        return "00-00-00"

def create_slblock_content(items):
    # Начало XML структуры
    xml = '<slblock Source="list" Type="accurate" Sec="0.000" Include_subfolders="no" Path="" '
    xml += 'cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2\n'
    
    # Путь к папке с рекламой (можно поменять под ваш сервер)
    base_path = "I:\\RECLAMA 2026\\"
    
    # Добавляем ролики из группы
    for _, row in items.iterrows():
        id_val = str(row['ID']).split('.')[0]
        name_val = str(row['Name'])
        # Формируем имя файла (ID_Название)
        file_name = f"{id_val}_{name_val}"
        xml += f'  <item file="{base_path}{file_name}" in="0.000" dur="0.000" />\n'
    
    xml += '</slblock>'
    return xml

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Индексы: 2 (Время блока), 6 (Название ролика), 9 (ID)
        df_res = df.iloc[:, [2, 6, 9]].copy()
        df_res.columns = ['Raw_Time', 'Name', 'ID']

        # Находим строки, где есть время блока, и протягиваем его
        df_res['Block_Time'] = df_res['Raw_Time'].ffill()
        
        # Убираем всё, кроме роликов
        df_res = df_res.dropna(subset=['Name', 'ID'])
        
        # Группируем данные по времени блока
        grouped = df_res.groupby('Block_Time')

        # Создаем ZIP архив в памяти
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for block_time, items in grouped:
                # Форматируем время для имени файла (например 06-20-00)
                file_name_time = format_excel_time(block_time)
                slblock_content = create_slblock_content(items)
                
                # Записываем файл в архив
                zip_file.writestr(f"{file_name_time}.SLBlock", slblock_content)

        st.success(f"Обработано блоков: {len(grouped)}")

        # Кнопка скачивания архива
        st.download_button(
            label="📥 Скачать архив со всеми .SLBlock",
            data=zip_buffer.getvalue(),
            file_name=f"Blocks_{uploaded_file.name.split('.')[0]}.zip",
            mime="application/zip"
        )
        
        st.write("Внутри архива файлы будут названы по времени выхода блока.")

    except Exception as e:
        st.error(f"Ошибка: {e}")
