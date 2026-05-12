import streamlit as st
import pandas as pd
import io
from datetime import timedelta

st.set_page_config(page_title="Global24 Converter", page_icon="📊")

st.title("📊 Конвертер GLOBAL24")
st.info("Конвертация Excel в формат для эфирной сетки")

uploaded_file = st.file_uploader("Выберите файл .xls", type=["xls", "xlsx"])

if uploaded_file:
    try:
        # Читаем Excel
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        # Индексы: 2 - время блока, 6 - название ролика, 9 - ID
        df_res = df.iloc[:, [2, 6, 9]].copy()
        df_res.columns = ['Время_Excel', 'Название', 'ID']

        # 1. Протягиваем время блока вниз на ролики
        df_res['Время_Excel'] = df_res['Время_Excel'].ffill()

        # 2. Убираем строки, где нет названия ролика
        df_res = df_res.dropna(subset=['Название'])

        # 3. Конвертируем дробное число Excel в формат ЧЧ:ММ:СС
        def convert_time(x):
            try:
                if pd.isna(x): return ""
                seconds = int(round(x * 86400))
                return str(timedelta(seconds=seconds))
            except:
                return str(x)

        df_res['Время'] = df_res['Время_Excel'].apply(convert_time)

        # 4. Чистим ID и склеиваем с названием
        df_res['ID'] = pd.to_numeric(df_res['ID'], errors='coerce').fillna(0).astype(int).astype(str)
        df_res['Результат'] = df_res['ID'] + ' ' + df_res['Название'].astype(str)

        # Финальный результат
        final_table = df_res[['Время', 'Результат']]

        st.subheader("Предпросмотр:")
        st.dataframe(final_table, use_container_width=True)

        # Скачивание
        csv_buffer = io.StringIO()
        final_table.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
        
        st.download_button(
            label="📥 Скачать готовый CSV",
            data=csv_buffer.getvalue(),
            file_name=f"Ready_{uploaded_file.name.split('.')[0]}.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Ошибка: {e}")
