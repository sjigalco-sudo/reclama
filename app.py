import streamlit as st
import pandas as pd
import io
import zipfile
import os
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Forward AIR Generator", page_icon="📺")
st.title("📺 Генератор AIR-файлов")

# Путь к папке с видео
BASE_PATH = r"I:\RECLAMA 2026"

def format_time_only(x):
    """Форматирует время для названия файла (ЧЧ-ММ-СС)"""
    if isinstance(x, (datetime, time)):
        return x.strftime('%H-%M-%S')
    if isinstance(x, (int, float)):
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).replace(':', '-').zfill(8)
    return str(x).replace(':', '-')

uploaded_file = st.file_uploader("Загрузите Excel файл рекламы", type=["xls", "xlsx"])

if uploaded_file:
    try:
        # Чтение данных (пропускаем техническую шапку Excel)
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Столбцы: Время (2), Название (6), Длительность (7), ID (9)
        df_res = df.iloc[:, [2, 6, 7, 9]].copy()
        df_res.columns = ['Block_Time', 'Name', 'Dur', 'ID']
        df_res['Block_Time'] = df_res['Block_Time'].ffill()
        df_res = df_res.dropna(subset=['ID'])
        
        grouped = df_res.groupby('Block_Time', sort=False)
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, (block_time, items) in enumerate(grouped, 1):
                # Название файла = Время выхода
                time_filename = format_time_only(block_time)
                # Номер заставки (цикл от 1 до 5)
                pub_num = ((i - 1) % 5) + 1 
                
                air_lines = []
                
                # 1. Заставка IN (без кавычек)
                air_lines.append(f"movie {BASE_PATH}\\PIBLICITATE {pub_num} IN.mp4")
                
                # 2. Ролики из Excel
                for _, row in items.iterrows():
                    id_val = str(row['ID']).split('.')[0]
                    name_val = str(row['Name']).strip()
                    # Проверка расширения (добавляем .mov если нет другого)
                    ext = "" if any(name_val.lower().endswith(e) for e in ['.mov', '.mp4', '.tga', '.mpg']) else ".mov"
                    
                    full_path = f"{BASE_PATH}\\{id_val}_{name_val}{ext}"
                    air_lines.append(f"movie {full_path}")
                
                # 3. Заставка OUT (без кавычек)
                air_lines.append(f"movie {BASE_PATH}\\PIBLICITATE {pub_num} OUT.mp4")
                
                # Сборка текста и кодировка Windows-1251 (стандарт Forward)
                content = "\r\n".join(air_lines)
                
                # Сохраняем файл в корень архива
                zip_file.writestr(f"{time_filename}.air", content.encode('windows-1251'))
        
        st.success(f"Готово! Подготовлено {len(grouped)} AIR-файлов.")
        st.download_button(
            label="📥 Скачать архив .air файлов",
            data=zip_buffer.getvalue(),
            file_name=f"Forward_AIR_Schedules.zip",
            mime="application/zip"
        )
        
        # Превью последнего блока для контроля
        st.divider()
        st.write(f"**Пример структуры файла ({time_filename}.air):**")
        st.code(content)

    except Exception as e:
        st.error(f"Произошла ошибка: {e}")
