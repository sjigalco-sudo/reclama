
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Global24 Converter", page_icon="📊")

st.title("📊 Конвертер отчетов GLOBAL24")
st.markdown("---")
st.info("Загрузите ваш файл .xls, чтобы объединить ID и названия ролика.")

uploaded_file = st.file_uploader("Выберите файл .xls или .xlsx", type=["xls", "xlsx"])

if uploaded_file:
    try:
        # Читаем файл
        df = pd.read_excel(uploaded_file, skiprows=6)
        
        if df.shape[1] < 10:
            st.error("В файле недостаточно столбцов. Проверьте формат.")
        else:
            # Выбираем время (2), название (6) и ID (9)
            df_processed = df.iloc[:, [2, 6, 9]].copy()
            df_processed.columns = ['Время', 'Название', 'ID']

            # Протягиваем время вниз
            df_processed['Время'] = df_processed['Время'].ffill()

            # Убираем строки без названия
            df_processed = df_processed.dropna(subset=['Название'])

            # Форматируем ID (убираем .0)
            df_processed['ID'] = pd.to_numeric(df_processed['ID'], errors='coerce').fillna(0).astype(int).astype(str)

            # Склеиваем ID и Название
            df_processed['Результат'] = df_processed['ID'] + ' ' + df_processed['Название'].astype(str)

            final_table = df_processed[['Время', 'Результат']]

            st.subheader("Результат:")
            st.dataframe(final_table, use_container_width=True)

            # Готовим CSV
            csv_buffer = io.StringIO()
            final_table.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
            
            st.download_button(
                label="📥 Скачать готовый CSV",
                data=csv_buffer.getvalue(),
                file_name=f"Processed_{uploaded_file.name.split('.')[0]}.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"Ошибка: {e}")
