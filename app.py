import streamlit as st
import pandas as pd
import io
from datetime import timedelta

st.set_page_config(page_title="Global24 Converter", page_icon="📊")

st.title("📊 Конвертер GLOBAL24")
st.markdown("---")
st.info("Загрузите Excel-файл. Программа автоматически объединит блоки и ролики.")

uploaded_file = st.file_uploader("Выберите файл .xls или .xlsx", type=["xls", "xlsx"])

if uploaded_file:
    try:
        # Читаем файл (пропускаем 6 строк мусора)
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Нам нужны: 2 (время блока), 6 (название ролика), 9 (ID)
        df_res = df.iloc[:, [2, 6, 9]].copy()
        df_res.columns = ['Raw_Time', 'Name', 'ID']

        # 1. Протягиваем время блока вниз на все ролики этого блока
        df_res['Raw_Time'] = df_res['Raw_Time'].ffill()

        # 2. Убираем строки, где нет названия ролика (пустые или технические)
        df_res = df_res.dropna(subset=['Name'])

        # 3. Конвертируем дробное время Excel в формат ЧЧ:ММ:СС
        def format_excel_time(x):
            try:
                if pd.isna(x) or isinstance(x, str): return str(x)
                # Excel хранит время как долю суток (0.25 = 6 утра)
                total_seconds = int(round(x * 86400))
                return str(timedelta(seconds=total_seconds)).zfill(8)
            except:
                return str(x)

        df_res['Время'] = df_res['Raw_Time'].apply(format_excel_time)

        # 4. Чистим ID (убираем .0) и склеиваем: "ID Название"
        df_res['ID'] = pd.to_numeric(df_res['ID'], errors='coerce').fillna(0).astype(int).astype(str)
        df_res['ID + Название'] = df_res['ID'] + ' ' + df_res['Name'].astype(str)

        # Оставляем только два финальных столбца
        final_table = df_res[['Время', 'ID + Название']]

        # Показываем результат пользователю
        st.subheader("Предпросмотр готовых данных:")
        st.dataframe(final_table, use_container_width=True)

        # Кнопка скачивания CSV
        csv_buffer = io.StringIO()
        final_table.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
        
        st.download_button(
            label="📥 Скачать результат для эфира (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"Ready_{uploaded_file.name.split('.')[0]}.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Произошла ошибка: {e}")
