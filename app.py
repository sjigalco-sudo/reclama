import streamlit as st
import pandas as pd
import io
import zipfile
import os
from datetime import timedelta, datetime, time

# Конфигурация страницы под бренд
st.set_page_config(page_title="Global 24 | Forward Generator", page_icon="📺", layout="wide")

# Кастомный стиль для Global 24
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1E3A8A; color: white; border: none; }
    .stDownloadButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #10B981; color: white; border: none; }
    h1 { color: #1E3A8A; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📺 GLOBAL 24: ГЕНЕРАТОР РАСПИСАНИЯ")
st.subheader("Формат: SLBlock (N4) | Кодировка: UTF-16LE | Имена: ЧЧ-ММ")

# Константа пути
BASE_PATH = r"I:\RECLAMA 2026"

def format_time_hh_mm(x):
    """Форматирует время строго в ЧЧ-ММ"""
    if isinstance(x, (datetime, time)):
        return x.strftime('%H-%M')
    if isinstance(x, (int, float)):
        total_seconds = int(round(x * 86400))
        full_time = str(timedelta(seconds=total_seconds)).zfill(8)
        # Убираем секунды, берем только первые 5 символов (HH:MM) и меняем : на -
        return full_time[:5].replace(':', '-')
    # Если пришла строка типа 10:00:00
    return str(x)[:5].replace(':', '-')

def xml_escape(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

with st.sidebar:
    st.header("Управление")
    uploaded_file = st.file_uploader("Загрузите медиа-план (Excel)", type=["xls", "xlsx"])
    st.divider()
    st.info(f"Рабочая папка: \n`{BASE_PATH}`")

if uploaded_file:
    try:
        # Имя архива как у исходного файла
        original_filename = os.path.splitext(uploaded_file.name)[0]
        
        # Чтение Excel (скипаем 6 строк шапки)
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Столбцы: 2-Время, 6-Название, 7-Длительность, 9-ID
        df_res = df.iloc[:, [2, 6, 7, 9]].copy()
        df_res.columns = ['Block_Time', 'Name', 'Dur', 'ID']
        df_res['Block_Time'] = df_res['Block_Time'].ffill()
        df_res = df_res.dropna(subset=['ID'])
        
        grouped = df_res.groupby('Block_Time', sort=False)
        
        zip_buffer = io.BytesIO()
        summary_table = []

        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, (block_time, items) in enumerate(grouped, 1):
                # Имя файла ЧЧ-ММ
                time_display = format_time_hh_mm(block_time)
                pub_num = ((i - 1) % 5) + 1 
                
                # Длительность (In + Out + Ролики)
                total_dur = 5.980 + items['Dur'].sum() + 6.580
                
                # Генерация контента SLBlock
                xml_lines = [
                    f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2',
                    f'  <item file="{xml_escape(BASE_PATH)}\\PIBLICITATE {pub_num} IN.mp4" in="0.000" dur="5.980" />'
                ]
                
                for _, row in items.iterrows():
                    id_val = str(row['ID']).split('.')[0]
                    name_val = str(row['Name']).strip()
                    dur_val = float(row['Dur'])
                    # Проверка на наличие расширения
                    ext = "" if any(name_val.lower().endswith(e) for e in ['.mov', '.mp4', '.tga', '.mpg']) else ".mov"
                    
                    full_path = f"{BASE_PATH}\\{id_val}_{name_val}{ext}"
                    xml_lines.append(f'  <item file="{xml_escape(full_path)}" in="0.000" dur="{dur_val:.3f}" />')
                
                xml_lines.append(f'  <item file="{xml_escape(BASE_PATH)}\\PIBLICITATE {pub_num} OUT.mp4" in="0.000" dur="6.580" />')
                xml_lines.append('</slblock>')
                
                # Финальный текст в UTF-16 LE с BOM
                content = "\r\n".join(xml_lines)
                raw_bytes = content.encode('utf-16')
                
                zip_file.writestr(f"{time_display}.slblock", raw_bytes)
                summary_table.append({"Выход": time_display, "Роликов": len(items), "Всего сек.": round(total_dur, 2)})

        # Интерфейс после обработки
        st.success(f"Успешно обработано {len(grouped)} рекламных блоков!")
        st.table(pd.DataFrame(summary_table))

        st.download_button(
            label=f"📥 СКАЧАТЬ АРХИВ ДЛЯ GLOBAL 24 ({original_filename}.zip)",
            data=zip_buffer.getvalue(),
            file_name=f"{original_filename}.zip",
            mime="application/zip"
        )

    except Exception as e:
        st.error(f"Ошибка при чтении файла: {e}")
else:
    st.info("Перетащите Excel файл сюда или выберите через боковую панель.")
