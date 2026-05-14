import streamlit as st
import pandas as pd
import io
import zipfile
import os
import re
from datetime import datetime, time

# --- КОНСТАНТЫ ---
PATH_MAIN = r"I:\RECLAMA 2026"
PATH_TOPSHOP = r"I:\TOPSHOP"
TS_TARGET_DUR = 915.0  # 15:15 в секундах
LOGO_PATH = "Global 24 Logo TV.png"

# --- КАСТОМНЫЙ ДИЗАЙН ---
def inject_custom_css():
    st.markdown("""
        <style>
        .main { background-color: #0d1117; }
        h1 { color: #e6edf3; font-weight: 700; border-bottom: 2px solid #30363d; padding-bottom: 10px; }
        section[data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #30363d; }
        .stButton>button { width: 100%; border-radius: 6px; background-color: #21262d; color: #c9d1d9; }
        .stDownloadButton>button { width: 100%; background-color: #238636 !important; color: white !important; font-weight: 700; }
        div[data-testid="stExpander"], .stFileUploader { border: 1px solid #30363d; border-radius: 8px; background-color: #0d1117; }
        </style>
    """, unsafe_allow_html=True)

def extract_date_info(text):
    if pd.isna(text): return None, ""
    match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', str(text))
    if match:
        day, month, year = match.groups()
        return f"{day.zfill(2)}.{month.zfill(2)}.{year}", f"{day.zfill(2)}{month.zfill(2)}{year}"
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
    return t_obj.strftime('%H-%M') if hasattr(t_obj, 'strftime') else str(t_obj)[:5].replace(':', '-')

def format_dur(sec):
    return f"{int(sec // 60):02d}:{int(sec % 60):02d}"

def xml_escape(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="Global 24 | Generator", page_icon="📺", layout="wide")
inject_custom_css()

if os.path.exists(LOGO_PATH):
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2: st.image(LOGO_PATH, use_container_width=True)

st.markdown("<h1 style='text-align: center;'>GLOBAL 24: УНИВЕРСАЛЬНЫЙ ГЕНЕРАТОР</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ НАСТРОЙКИ")
    ad_type = st.radio("Режим работы:", ["MD+SP (I:\RECLAMA 2026)", "TopShop (I:\TOPSHOP)"])
    mp4_ids = []
    if "MD+SP" in ad_type:
        with st.expander("🎥 Форматы (.mp4)"):
            mp4_ids_input = st.text_area("ID через запятую:", value="6856, 6857")
            mp4_ids = [x.strip() for x in mp4_ids_input.split(",") if x.strip()]
    st.divider()
    uploaded_file = st.file_uploader("Загрузите медиа-план (XLSX)", type=["xls", "xlsx"])

if uploaded_file:
    try:
        # Получаем чистое имя исходного файла
        source_name = os.path.splitext(uploaded_file.name)[0]
        summary_data = [] 
        
        with st.status("Генерация архива...", expanded=True) as status:
            mode_topshop = "TopShop" in ad_type
            current_path = PATH_TOPSHOP if mode_topshop else PATH_MAIN
            df_raw = pd.read_excel(uploaded_file, header=None)
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                if mode_topshop:
                    all_rows = []
                    curr_d_disp, curr_d_clean = "00.00.0000", "00000000"
                    
                    for _, row in df_raw.iterrows():
                        d_disp, d_clean = extract_date_info(str(row[0]))
                        if d_disp:
                            curr_d_disp, curr_d_clean = d_disp, d_clean
                            continue
                        
                        t_obj = to_time_obj(row[1])
                        if t_obj and pd.notna(row[3]):
                            all_rows.append({
                                'd_disp': curr_d_disp, 'd_clean': curr_d_clean,
                                'time': t_obj, 'hour': t_obj.hour,
                                'id': str(row[3]).strip(),
                                'name': str(row[2]).strip(), 'dur': float(row[4]) if pd.notna(row[4]) else 0.0
                            })

                    if all_rows:
                        df_ts = pd.DataFrame(all_rows)
                        for (d_clean, d_disp, hour), group in df_ts.groupby(['d_clean', 'd_disp', 'hour'], sort=False):
                            t_start = format_time_filename(group.iloc[0]['time'])
                            total_dur = group['dur'].sum()
                            summary_data.append([f"{d_disp} {t_start.replace('-', ':')}", format_dur(total_dur), len(group)])
                            
                            xml = [f'<slblock Source="list" Type="accurate" Sec="{total_dur:.3f}" Include_subfolders="no" Path="">version 2']
                            for _, r in group.iterrows():
                                xml.append(f'  <item file="{xml_escape(current_path)}\\{r["id"]}____{r["name"]}.mp4" in="0.000" dur="{r["dur"]:.3f}" />')
                            xml.append('</slblock>')
                            zip_file.writestr(f"{d_clean}_{t_start}.slblock", "\r\n".join(xml).encode('utf-16'))
                    
                    zip_name = f"TOPSHOP {source_name}.zip"

                else:
                    df = pd.read_excel(uploaded_file, skiprows=6)
                    df_res = df.iloc[:, [2, 6, 7, 9]].copy()
                    df_res.columns = ['Time', 'Name', 'Dur', 'ID']
                    df_res['Time'] = df_res['Time'].ffill()
                    df_res = df_res.dropna(subset=['ID'])
                    for i, (bt, items) in enumerate(df_res.groupby('Time', sort=False), 1):
                        t_f, p_n = format_time_filename(bt), ((i - 1) % 5) + 1
                        total = 5.980 + items['Dur'].sum() + 6.580
                        summary_data.append([t_f.replace('-', ':'), format_dur(total), len(items)])
                        
                        xml = [f'<slblock Source="list" Type="accurate" Sec="{total:.3f}" Include_subfolders="no" Path="">version 2']
                        xml.append(f'  <item file="{xml_escape(PATH_MAIN)}\\PIBLICITATE {p_n} IN.mp4" in="0.000" dur="5.980" />')
                        for _, r in items.iterrows():
                            id_c = str(r['ID']).split(".")[0]
                            ext = ".mp4" if id_c in mp4_ids else ".mov"
                            xml.append(f'  <item file="{xml_escape(PATH_MAIN)}\\{id_c}_{str(r["Name"]).strip()}{ext}" in="0.000" dur="{float(r["Dur"]):.3f}" />')
                        xml.append(f'  <item file="{xml_escape(PATH_MAIN)}\\PIBLICITATE {p_n} OUT.mp4" in="0.000" dur="6.580" />')
                        xml.append('</slblock>')
                        zip_file.writestr(f"{t_f}.slblock", "\r\n".join(xml).encode('utf-16'))
                    
                    zip_name = f"RECLAMA {source_name}.zip"

            status.update(label="Готово!", state="complete")

        if summary_data:
            with st.expander("📊 ДЕТАЛИЗАЦИЯ БЛОКОВ", expanded=True):
                st.table(pd.DataFrame(summary_data, columns=["Блок", "Длительность", "Количество роликов"]))

        st.download_button(label=f"📥 СКАЧАТЬ {zip_name}", data=zip_buffer.getvalue(), file_name=zip_name, mime="application/zip")

    except Exception as e:
        st.error(f"Произошла ошибка при обработке файла: {e}")
