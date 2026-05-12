import streamlit as st
import pandas as pd
from datetime import timedelta, datetime, time
import io

st.set_page_config(page_title="Global24 Playlist Gen", page_icon="📄")
st.title("📄 Генератор текстового плейлиста")

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
        # Читаем Excel, пропуская первые 6 строк (как в оригинале)
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Столбцы: 2 (Время блока), 6 (Название ролика), 9 (ID)
        # Индексы: [2, 6, 9]
        df_res = df.iloc[:, [2, 6, 9]].copy()
        df_res.columns = ['Block_Time', 'Name', 'ID']
        
        # Заполняем пустое время вниз
        df_res['Block_Time'] = df_res['Block_Time'].ffill()
        
        # Убираем строки без названия или ID
        df_res = df_res.dropna(subset=['Name', 'ID'])
        
        # Группируем по времени блока
        grouped = df_res.groupby('Block_Time', sort=False)
        
        # Формируем текст
        output = io.StringIO()
        
        for i, (block_time, items) in enumerate(grouped, 1):
            time_str = format_time(block_time)
            pub_num = ((i - 1) % 5) + 1 # Логика чередования заставок 1-5
            
            output.write(f"=== БЛОК {time_str} ===\n")
            output.write(f"Заставка IN: PIBLICITATE {pub_num} IN.mp4\n")
            
            for _, row in items.iterrows():
                id_val = str(row['ID']).split('.')[0]
                name_val = str(row['Name']).strip()
                # Если в названии нет расширения, добавим .mov
                ext = "" if any(name_val.lower().endswith(e) for e in ['.mov', '.mp4', '.tga', '.mpg']) else ".mov"
                output.write(f"  - {id_val}_{name_val}{ext}\n")
                
            output.write(f"Заставка OUT: PIBLICITATE {pub_num} OUT.mp4\n")
            output.write("\n") # Пробел между блоками
            
        final_text = output.getvalue()
        
        st.text_area("Предпросмотр файла:", final_text, height=400)
        
        st.download_button(
            label="📥 Скачать плейлист (.txt)",
            data=final_text,
            file_name=f"Playlist_{datetime.now().strftime('%d_%m')}.txt",
            mime="text/plain"
        )
        
    except Exception as e:
        st.error(f"Произошла ошибка при обработке: {e}")
