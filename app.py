Понял, подправляем формат. Теперь в файле будет только чистое время и список файлов в одну строку без лишних слов «Заставка» и дефисов.

Обновленный код для app.py:
Python
import streamlit as st
import pandas as pd
from datetime import timedelta, datetime, time
import io

st.set_page_config(page_title="Global24 Playlist Gen", page_icon="📄")
st.title("📄 Генератор плейлиста TXT")

def format_time(x):
    if isinstance(x, (datetime, time)):
        return x.strftime('%H:%M:%S')
    if isinstance(x, (int, float)):
        total_seconds = int(round(x * 86400))
        return str(timedelta(seconds=total_seconds)).zfill(8)
    return str(x)

uploaded_file = st.file_uploader("Загрузите Excel файл", type=["xls", "xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Столбцы: Время блока (2), Название ролика (6), ID (9)
        df_res = df.iloc[:, [2, 6, 9]].copy()
        df_res.columns = ['Block_Time', 'Name', 'ID']
        
        df_res['Block_Time'] = df_res['Block_Time'].ffill()
        df_res = df_res.dropna(subset=['Name', 'ID'])
        
        grouped = df_res.groupby('Block_Time', sort=False)
        
        output = io.StringIO()
        
        for i, (block_time, items) in enumerate(grouped, 1):
            time_str = format_time(block_time)
            pub_num = ((i - 1) % 5) + 1 
            
            # Начинаем строку со времени блока
            line_parts = [time_str]
            
            # Добавляем входную заставку
            line_parts.append(f"PIBLICITATE {pub_num} IN.mp4")
            
            # Добавляем ролики
            for _, row in items.iterrows():
                id_val = str(row['ID']).split('.')[0]
                name_val = str(row['Name']).strip()
                ext = "" if any(name_val.lower().endswith(e) for e in ['.mov', '.mp4', '.tga', '.mpg']) else ".mov"
                line_parts.append(f"{id_val}_{name_val}{ext}")
            
            # Добавляем выходную заставку
            line_parts.append(f"PIBLICITATE {pub_num} OUT.mp4")
            
            # Собираем всё в одну строку через пробел (или запятую, если нужно)
            output.write(" ".join(line_parts) + "\n")
            
        final_text = output.getvalue()
        
        st.text_area("Предпросмотр (в одну строку):", final_text, height=400)
        
        st.download_button(
            label="📥 Скачать плейлист (.txt)",
            data=final_text,
            file_name=f"Playlist_{datetime.now().strftime('%H_%M')}.txt",
            mime="text/plain"
        )
        
    except Exception as e:
        st.error(f"Ошибка: {e}")
