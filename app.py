import streamlit as st
import pandas as pd
import io
import zipfile
import os
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Forward AIR Generator", page_icon="📺")
st.title("📺 Генератор расписания (Без кавычек)")

# Путь к папке
BASE_PATH = r"I:\RECLAMA 2026"

def format_time_only(x):
    """Превращает время в формат ЧЧ-ММ-СС для имени файла"""
    if isinstance(x, (datetime, time)):
        return x.strftime('%H-%M-%S')
    if isinstance(x, (int, float)):
        # Обработка времени из Excel (доля дня)
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).replace(':', '-').zfill(8)
    return str(x).replace(':', '-')

uploaded_file = st.file_uploader("Загрузите Excel", type=["xls", "xlsx"])

if uploaded_file:
    try:
        # Читаем данные, пропуская шапку
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Выбираем нужные колонки: Время (2), Название (6), Длительность (7), ID (9)
        df_res = df.iloc[:, [2, 6, 7, 9]].copy()
        df_res.columns = ['Block_Time', 'Name', 'Dur', 'ID']
        df_res['Block_Time'] = df_res['Block_Time'].ffill()
        df_res = df_res.dropna(subset=['ID'])
        
        grouped = df_res.groupby('Block_Time', sort=False)
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, (block_time, items) in enumerate(grouped, 1):
                # Имя файла — ТОЛЬКО время
                time_filename = format_time_only(block_time)
                pub_num = ((i - 1) % 5) + 1 
                
                # Список путей для блока
                paths = []
                # 1. Заставка IN
                paths.append(f"{BASE_PATH}\\PIBLICITATE {pub_num} IN.mp4")
                
                # 2. Ролики
                for _, row in items.iterrows():
                    id_val = str(row['ID']).split('.')[0]
                    name_val = str(row['Name']).strip()
                    # Проверка расширения
                    ext = "" if any(name_val.lower().endswith(e) for e in ['.mov', '.mp4', '.tga', '.mpg']) else ".mov"
                    paths.append(f"{BASE_PATH}\\{id_val}_{name_val}{ext}")
                
                # 3. Заставка OUT
                paths.append(f"{BASE_PATH}\\PIBLICITATE {pub_num} OUT.mp4")
                
                # Создаем два варианта контента без кавычек
                # Вариант 1: Командный AIR (movie путь)
                air_content = "\r\n".join([f"movie {p}" for p in paths])
                
                # Вариант 2: Чистый список путей TXT
                txt_content = "\r\n".join(paths)
                
                # Записываем в архив (кодировка Windows-1251 для кириллицы)
                zip_file.writestr(f"AIR/{time_filename}.air", air_content.encode('windows-1251'))
                zip_file.writestr(f"TXT/{time_filename}.txt", txt_content.encode('windows-1251'))
        
        st.success(f"Готово! Сформировано {len(grouped)} файлов.")
        st.download_button(
            label="📥 Скачать расписание (AIR и TXT)",
            data=zip_buffer.getvalue(),
            file_name=f"Forward_Schedules.zip"
        )
        
        st.divider()
        st.write(f"**Пример файла {time_filename}.air (без кавычек):**")
        st.code(air_content)

    except Exception as e:
        st.error(f"Ошибка при обработке: {e}")
