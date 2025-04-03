import streamlit as st
import pandas as pd
from datetime import datetime

# Импортируем функции из наших модулей
from data_loader import load_data
from tabs.projections import render_projections_tab
from tabs.resources import render_resources_tab
from tabs.details import render_details_tab

# --- Настройка страницы ---
st.set_page_config(
    page_title="Дашборд Анализа Заказов",
    page_icon="📊",
    layout="wide" # Используем широкую раскладку
)

st.title("📊 Дашборд Анализа Процессов Заказов")

# --- Загрузка данных ---
# Укажите правильный путь к вашему файлу
DATA_PATH = 'data/dataset.csv'
df = load_data(DATA_PATH)

# --- Основная логика ---
if not df.empty:
    st.sidebar.header('Фильтры')

    # --- Фильтры в сайдбаре ---
    # Фильтр по территории
    territory_list = ['Все территории'] + sorted(df['Территория'].astype(str).unique().tolist())
    selected_territory = st.sidebar.selectbox('Территория', territory_list)

    # Фильтр по дате
    min_date = df['date'].min()
    max_date = df['date'].max()
    # Используем try-except на случай, если min_date > max_date (редко, но возможно при малых данных)
    try:
        start_date, end_date = st.sidebar.date_input(
            'Диапазон дат',
            value=[min_date, max_date], # Устанавливаем значение по умолчанию
            min_value=min_date,
            max_value=max_date
        )
    except st.errors.StreamlitAPIException:
         st.sidebar.error("Некорректный диапазон дат в данных.")
         start_date, end_date = min_date, max_date # Используем мин/макс как запасной вариант

    # --- Фильтрация данных ---
    # Конвертируем start_date и end_date обратно в datetime.date для сравнения
    start_date_dt = pd.to_datetime(start_date).date()
    end_date_dt = pd.to_datetime(end_date).date()

    # Применяем фильтры
    filtered_df = df[
        (df['date'] >= start_date_dt) &
        (df['date'] <= end_date_dt)
    ]
    if selected_territory != 'Все территории':
        # Сравниваем как строки на всякий случай, если 'Территория' смешанного типа
        filtered_df = filtered_df[filtered_df['Территория'].astype(str) == selected_territory]

    # --- Проверка наличия данных после фильтрации ---
    if filtered_df.empty:
        st.warning("⚠️ Нет данных для отображения с выбранными фильтрами.")
    else:
        st.success(f"Загружено и отфильтровано {len(filtered_df)} записей этапов ({filtered_df['case'].nunique()} уникальных заказов).")

        # --- Создание вкладок ---
        tab_titles = ["Прогнозы", "Ресурсы", "Детализация"]
        tab1, tab2, tab3 = st.tabs(tab_titles)

        with tab1:
            render_projections_tab(filtered_df)

        with tab2:
            render_resources_tab(filtered_df)

        with tab3:
            render_details_tab(filtered_df)

        # --- Информация о фильтрах и обновлении ---
        st.sidebar.write("---")
        st.sidebar.info(f"Территория: **{selected_territory}**")
        st.sidebar.info(f"Период: **{start_date_dt.strftime('%d.%m.%Y')}** - **{end_date_dt.strftime('%d.%m.%Y')}**")
        st.sidebar.info(f"Данные обновлены: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

else:
    # Это сообщение будет показано, если load_data вернул пустой DataFrame
    st.error("Не удалось загрузить или обработать данные. Дальнейшее отображение невозможно.")
