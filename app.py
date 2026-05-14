import streamlit as st
import pandas as pd
import io
import zipfile
import os
import re
from datetime import timedelta, datetime, time

# --- КОНСТАНТЫ ---
PATH_MAIN = r"I:\RECLAMA 2026"
PATH_TOPSHOP = r"I:\TOPSHOP"
TS_FILE = "teleshopping1.mp4"
TS_DUR = 7.600
LOGO_PATH = "Global 24 Logo TV.png"

# --- КАСТОМНЫЙ ДИЗАЙН (CSS) ---
def inject_custom_css():
    st.markdown("""
        <style>
        .main { background-color: #0d1117; }
        h1 {
            color: #e6edf3;
            font-weight: 700;
            letter-spacing: 1px;
            border-bottom: 2px solid #30363d;
            padding-bottom: 10px;
        }
        section[data-testid="stSidebar"] {
            background-color: #161b22 !important;
            border-right: 1px solid #30363d;
        }
        .stButton>button {
            width: 100%;
            border-radius: 6px;
            border: 1px solid #30363d;
            background-color: #21262d;
            color: #c9d1d9;
            font-weight: 600;
        }
        .stButton>button:hover {
            border-color: #8b949e;
            color: #ffffff;
            background-color: #30363d;
        }
        .stDownloadButton>button {
            width: 100%;
            background-color: #238636 !important;
            color: white !important;
            border: 1px solid #2ea043 !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            margin-top: 20px;
        }
        .stDownloadButton>button:hover {
            background-color: #2ea043 !important;
            border-color: #3fb950 !important;
        }
        div[data-testid="stExpander"], .stFileUploader {
            border: 1px solid #30363d;
            border-radius: 8px;
            background-color: #0d1117;
        }
        .stAlert {
            border: 1px solid #238636;
            background-color: #04190b;
            color: #3fb950;
        }
        </style>
    """, unsafe_allow_html=True)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def extract_date_info(text):
    if pd.isna(text): return None, ""
    match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', str(text))
    if match:
        day, month, year = match.groups()
        clean_digits = f"{day.zfill(2)}{month.zfill(2)}{year}"
        display_date = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
        return display_date, clean_digits
    return None, ""

def to_time_obj(val):
    if isinstance(val, (datetime, time)): return val
    if isinstance(val, str):
        val = val.strip()
        for fmt in ("%H:%M:%S", "%H:%M"):
            try: return datetime.strptime(val, fmt).time()
            except ValueError: continue
    return None

def format_time_filename(t_obj):
    if hasattr(t_obj, 'strftime'): return t_obj.strftime('%H:%M')
    return str(t_obj)[:5]

def format_dur(sec):
    return f"{int(sec // 60):02d}:{int(sec % 60):02d}"

def xml_escape(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="Global 24 | Generator", page_icon="📺", layout="wide")
inject_custom_css()

# Логотип и Главный заголовок
if os.path.exists(LOGO_PATH):
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2: st.image(LOGO_PATH, use_container_width=True)

st.markdown("<h1 style='text-align: center;'>GLOBAL 24: УНИВЕРСАЛЬНЫЙ ГЕНЕРАТОР</h1>", unsafe_allow_html=True)

# Боковая панель
with st.sidebar:
    st.markdown("### ⚙️ ПАРАМЕТРЫ")
    ad_type = st.radio("Режим работы:", ["MD+SP (I:\RECLAMA 2026)", "TopShop (I:\TOPSHOP)"])
    
    mp4_ids = []
    if "MD+SP" in ad_type:
        with st.expander("🎥 Форматы (.mp4)"):
            # Исправленная строка (была ошибкой AttributeError)
            mp4_ids_input = st.text_area("ID через запятую:", value="6856, 6857")
            mp4_ids = [x.strip() for x in mp4_ids_input.split(",") if x.strip()]
    
    st.divider()
    st.markdown("### 📁 ЗАГРУЗКА")
    uploaded_file = st.file_uploader("Медиа-план (XLSX)", type=["xls", "xlsx"])

# --- ЛОГИКА ОБРАБОТКИ ---
if uploaded_file:
    try:
        summary_data = [] 
        
        with st.status("Выполняется генерация блоков...", expanded=True) as status:
            mode_topshop = "TopShop" in ad_type
            current_path = PATH_TOPSHOP if mode_topshop else PATH_MAIN
            
            df_raw = pd.read_excel(uploaded_file, header=None)
            zip_buffer = io.BytesIO()
            found_dates = []
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                if mode_topshop:
                    current_date_prefix = ""
                    current_block_items = []
                    for index, row in df_raw.iterrows():
                        val_col0 = str(row[0])
                        if any(day in val_col0 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
                            disp_date, clean_digits = extract_date_info(val_col0)
                            if disp_date:
                                found_dates.append(disp_date)
                                current_date_prefix = clean_digits
                            continue
                        
                        if pd.notna(row[1]) and (":" in str(row[1])) and pd.notna(row[3]):
                            t_obj = to_time_obj(row[1])
                            if current_block_items and t_obj:
                                dt1 = datetime.combine(datetime.today(), current_block_items[-1]['time'])
                                dt2 = datetime.combine(datetime.today(), t_obj)
                                if (dt2 - dt1).total_seconds() > 360:
                                    start_t = format_time_filename(current_block_items[0]['time'])
                                    total_dur = TS_DUR + sum(item['dur'] for item in current_block_items) + TS_DUR
                                    summary_data.append([start_t, format_dur(total_dur), len(current_block_items)])
                                    
                                    f_name = f"{current_date_prefix}_{start_t.replace(':', '-')}.slblock"
                                    xml_lines = [
                                        f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2',
                                        f'  <item file="{xml_escape(current_path)}\\{TS_FILE}" in="0.000" dur="{TS_DUR:.3f}" />'
                                    ]
                                    for item in current_block_items:
                                        xml_lines.append(f'  <item file="{xml_escape(current_path)}\\{item["file"]}" in="0.000" dur="{item["dur"]:.3f}" />')
                                    xml_lines.append(f'  <item file="{xml_escape(current_path)}\\{TS_FILE}" in="0.000" dur="{TS_DUR:.3f}" />')
                                    xml_lines.append('</slblock>')
                                    zip_file.writestr(f_name, "\r\n".join(xml_lines).encode('utf-16'))
                                    current_block_items = []
                            
                            id_clean = str(row[3]).strip()
                            nm = str(row[2]).strip()
                            current_block_items.append({'time': t_obj, 'dur': float(row[4]), 'file': f"{id_clean}____{nm}.mp4"})

                    if current_block_items:
                        start_t = format_time_filename(current_block_items[0]['time'])
                        total_dur = TS_DUR + sum(item['dur'] for item in current_block_items) + TS_DUR
                        summary_data.append([start_t, format_dur(total_dur), len(current_block_items)])
                        f_name = f"{current_date_prefix}_{start_t.replace(':', '-')}.slblock"
                        xml_lines = [
                            f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2',
                            f'  <item file="{xml_escape(current_path)}\\{TS_FILE}" in="0.000" dur="{TS_DUR:.3f}" />'
                        ]
                        for item in current_block_items:
                            xml_lines.append(f'  <item file="{xml_escape(current_path)}\\{item["file"]}" in="0.000" dur="{item["dur"]:.3f}" />')
                        xml_lines.append(f'  <item file="{xml_escape(current_path)}\\{TS_FILE}" in="0.000" dur="{TS_DUR:.3f}" />')
                        xml_lines.append('</slblock>')
                        zip_file.writestr(f_name, "\r\n".join(xml_lines).encode('utf-16'))
                    zip_name = f"TOPSHOP_{found_dates[0] if found_dates else 'Archive'}.zip"

                else:
                    # --- MD+SP ---
                    df = pd.read_excel(uploaded_file, skiprows=6)
                    df_res = df.iloc[:, [2, 6, 7, 9]].copy()
                    df_res.columns = ['Block_Time', 'Name', 'Dur', 'ID']
                    df_res['Block_Time'] = df_res['Block_Time'].ffill()
                    df_res = df_res.dropna(subset=['ID'])
                    for i, (block_time, items) in enumerate(df_res.groupby('Block_Time', sort=False), 1):
                        time_filename = format_time_filename(block_time)
                        pub_num = ((i - 1) % 5) + 1
                        total_dur = 5.980 + items['Dur'].sum() + 6.580
                        summary_data.append([time_filename, format_dur(total_dur), len(items)])
                        xml_lines = [
                            f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="" cptn_start_file="" cptn_end_file="" cptn_between_file="" cptn_start_en="no" cptn_end_en="no" cptn_between_en="no">version 2',
                            f'  <item file="{xml_escape(PATH_MAIN)}\\PIBLICITATE {pub_num} IN.mp4" in="0.000" dur="5.980" />'
                        ]
                        for _, row in items.iterrows():
                            id_c = str(row['ID']).split(".")[0]
                            nm_c = str(row['Name']).strip()
                            ext = ".mp4" if id_c in mp4_ids else ".mov"
                            xml_lines.append(f'  <item file="{xml_escape(PATH_MAIN)}\\{id_c}_{nm_c}{ext}" in="0.000" dur="{float(row["Dur"]):.3f}" />')
                        xml_lines.append(f'  <item file="{xml_escape(PATH_MAIN)}\\PIBLICITATE {pub_num} OUT.mp4" in="0.000" dur="6.580" />')
                        xml_lines.append('</slblock>')
                        zip_file.writestr(f"{time_filename.replace(':', '-')}.slblock", "\r\n".join(xml_lines).encode('utf-16'))
                    zip_name = f"MD_SP_Blocks_{os.path.splitext(uploaded_file.name)[0]}.zip"
            
            status.update(label="Генерация завершена успешно!", state="complete")

        # --- ОБЪЕДИНЕННЫЙ БЛОК: УСПЕХ + ОТЧЕТ ---
        if summary_data:
            with st.expander("✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА УСПЕШНО! (НАЖМИТЕ ДЛЯ ПРОСМОТРА ОТЧЕТА)", expanded=False):
                df_report = pd.DataFrame(summary_data, columns=["Время выхода", "Длительность блока", "Кол-во файлов"])
                st.table(df_report)

        st.download_button(
            label="📥 СКАЧАТЬ СФОРМИРОВАННЫЙ АРХИВ",
            data=zip_buffer.getvalue(),
            file_name=zip_name,
            mime="application/zip"
        )

    except Exception as e:
        st.error(f"Произошла ошибка при обработке: {e}")
