import streamlit as st
import pandas as pd
from datetime import timedelta, datetime, time
import io
import os

st.set_page_config(page_title="Global24 TXT Generator", page_icon="📝")
st.title("📝 Генератор плейлиста (Слитно в кавычках)")

def format_time(x):
    if isinstance(x, (datetime, time)):
        return x.strftime('%H:%M:%S')
    if isinstance(x, (int, float)):
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).zfill(8)
    return str(x)

uploaded_file = st.file_uploader("Загрузите Excel", type=["xls", "xlsx"])

if uploaded_file:
    try:
        # Имя файла из исходника
        base_name = os.path.splitext(uploaded_file.name)[0]
        new_filename = f"{base_name}.txt"

        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Столбцы: Время (2), Название (6), ID (9)
        df_res = df.iloc[:, [2, 6, 9]].copy()
        df_res.columns = ['Block_Time', 'Name', 'ID']
        
        df_res['Block_Time'] = df_res['Block_Time'].ffill()
        df_res = df_res.dropna(subset=['Name', 'ID'])
        
        grouped = df_res.groupby('Block_Time', sort=False)
        
        output = io.StringIO()
        
        for i, (block_time, items) in enumerate(grouped, 1):
            time_str = format_time(block_time)
            pub_num = ((i - 1) % 5) + 1 
            
            # 1. Время
            output.write(f"{time_str}\n")
            
            # 2. Формируем элементы в кавычках
            line_elements = []
            line_elements.append(f'"PIBLICITATE {pub_num} IN.mp4"')
            
            for _, row in items.iterrows():
                id_val = str(row['ID']).split('.')[0]
                name_val = str(row['Name']).strip()
                ext = "" if any(name_val.lower().endswith(e) for e in ['.mov', '.mp4', '.tga', '.mpg']) else ".mov"
                line_elements.append(f'"{id_val}_{name_val}{ext}"')
            
            line_elements.append(f'"PIBLICITATE {pub_num} OUT.mp4"')
            
            # 3. Соединяем БЕЗ пробела
            output.write("".join(line_elements) + "\n\n")
            
        final_text = output.getvalue()
        
        st.subheader(f"Результат: {new_filename}")
        st.text_area("Предпросмотр (без пробелов между кавычками):", final_text, height=300)
        
        st.download_button(
            label=f"📥 Скачать {new_filename}",
            data=final_text,
            file_name=new_filename,
            mime="text/plain"
        )
        
    except Exception as e:
        st.error(f"Ошибка: {e}")
