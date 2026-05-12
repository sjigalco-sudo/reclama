import streamlit as st
import pandas as pd
import io
import zipfile
import os
from datetime import timedelta, datetime, time

st.set_page_config(page_title="Global24 AIR Generator", page_icon="📺")
st.title("📺 Генератор AIR-расписания")

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
                
                # Формируем структуру AIR файла
                # Формат: movie "путь_к_файлу"
                air_lines = []
                
                # Добавляем заставку IN
                air_lines.append(f'movie "{BASE_PATH}\\PIBLICITATE {pub_num} IN.mp4"')
                
                # Добавляем ролики рекламы
                for _, row in items.iterrows():
                    id_val = str(row['ID']).split('.')[0]
                    name_val = str(row['Name']).strip()
                    ext = "" if any(name_val.lower().endswith(e) for e in ['.mov', '.mp4', '.tga', '.mpg']) else ".mov"
                    
                    full_path = f"{BASE_PATH}\\{id_val}_{name_val}{ext}"
                    air_lines.append(f'movie "{full_path}"')
                
                # Добавляем заставку OUT
                air_lines.append(f'movie "{BASE_PATH}\\PIBLICITATE {pub_num} OUT.mp4"')
                
                # Соединяем строки и кодируем в Windows-1251 (важно для кириллицы)
                content = "\r\n".join(air_lines)
                filename = f"{time_str}_{base_name}.air"
                
                zip_file.writestr(filename, content.encode('windows-1251'))
        
        st.success(f"Готово! Создано {len(grouped)} AIR-файлов.")
        st.download_button(
            label="📥 Скачать AIR-файлы",
            data=zip_buffer.getvalue(),
            file_name=f"AIR_Schedules_{base_name}.zip"
        )
        
        st.divider()
        st.write("**Пример содержания AIR-файла:**")
        st.code(content)

    except Exception as e:
        st.error(f"Ошибка: {e}")
