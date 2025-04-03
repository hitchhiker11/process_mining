import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

def render_details_tab(filtered_df):
    """Отрисовывает вкладку 'Детализация'."""
    st.header("Детальный анализ процессов")

    # 1. Динамика по территории (например, динамика отмен)
    st.subheader("Динамика количества отмен по дням")
    # Группируем по дате и считаем уникальные отмененные заказы
    daily_cancel_cases = filtered_df[filtered_df['is_canceled'] == 1].groupby('date')['case'].nunique().reset_index()

    if not daily_cancel_cases.empty:
        # Создаем полный диапазон дат для непрерывности графика
        date_range = pd.date_range(start=filtered_df['date'].min(), end=filtered_df['date'].max())
        full_date_df = pd.DataFrame(date_range, columns=['date'])
        full_date_df['date'] = full_date_df['date'].dt.date # Оставляем только дату

        # Объединяем с данными об отменах, заполняем пропуски нулями
        daily_cancel_full = pd.merge(full_date_df, daily_cancel_cases, on='date', how='left').fillna(0)

        fig_daily_cancel = px.line(daily_cancel_full, x='date', y='case',
                                   title='Количество отмененных заказов по дням',
                                   labels={'date': 'Дата', 'case': 'Кол-во отмен'})
        fig_daily_cancel.update_traces(mode='lines+markers')
        st.plotly_chart(fig_daily_cancel, use_container_width=True)
    else:
        st.info("Нет данных по отменам для отображения динамики.")

    # 2. Сравнение с нормативами
    st.subheader("Сравнение средней фактической длительности этапов с нормативами")
    # --- Нормативы (можно вынести в конфиг) ---
    norms = {
        'Сборка заказа': 30,
        'Упаковка товара': 10,
        'Доставка заказа': 45,
        'Передача товара курьеру': 5
        # Добавьте другие этапы и их нормативы
    }
    st.write("Используемые нормативы (минуты):")
    st.json(norms) # Показываем нормативы в виде JSON

    # Рассчитываем среднюю фактическую длительность только для НЕ отмененных этапов
    actual_duration = filtered_df[filtered_df['is_canceled'] == 0].groupby('stage')['duration'].mean().reset_index()

    comparison_data = []
    stages_in_data = actual_duration['stage'].unique()

    for stage_norm, norm_value in norms.items():
        # Ищем точное совпадение или частичное, если нужно
        # В данном случае ищем точное совпадение с ключом словаря norms
        actual_value_series = actual_duration[actual_duration['stage'] == stage_norm]['duration']

        if not actual_value_series.empty:
            actual_value = actual_value_series.iloc[0]
            comparison_data.append({'Этап': stage_norm, 'Тип': 'Факт', 'Длительность (мин)': actual_value})
            comparison_data.append({'Этап': stage_norm, 'Тип': 'Норматив', 'Длительность (мин)': norm_value})
        else:
            # Если этап из норматива не найден в данных, показываем только норматив
            comparison_data.append({'Этап': stage_norm, 'Тип': 'Факт', 'Длительность (мин)': 0}) # Факт = 0
            comparison_data.append({'Этап': stage_norm, 'Тип': 'Норматив', 'Длительность (мин)': norm_value})
            st.caption(f"⚠️ Этап '{stage_norm}' из нормативов не найден в фактических данных за выбранный период.")

    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)
        fig_comparison = px.bar(comparison_df,
                                x='Этап',
                                y='Длительность (мин)',
                                color='Тип', # Разделяем по цвету Факт/Норматив
                                barmode='group', # Группируем бары рядом
                                title='Сравнение фактической длительности этапов с нормативами',
                                labels={'value': 'Длительность (мин)', 'variable': 'Тип'},
                                text_auto='.1f') # Показываем значения на барах
        st.plotly_chart(fig_comparison, use_container_width=True)
    else:
        st.warning("Не удалось собрать данные для сравнения с нормативами.")


    # 3. Причины отмен (анализируем этап, на котором произошла отмена)
    st.subheader("Анализ причин отмен (по этапу)")
    canceled_stages_df = filtered_df[filtered_df['is_canceled'] == 1]

    if not canceled_stages_df.empty:
        reason_counts = canceled_stages_df['stage'].value_counts().reset_index()
        reason_counts.columns = ['Причина (этап отмены)', 'Количество']

        fig_reasons = px.bar(reason_counts,
                             x='Количество',
                             y='Причина (этап отмены)',
                             orientation='h', # Горизонтальный бар для лучшей читаемости
                             title='Распределение причин отмен (по этапу)',
                             text_auto=True) # Показываем количество на барах
        fig_reasons.update_layout(yaxis={'categoryorder':'total ascending'}) # Сортируем причины по количеству
        st.plotly_chart(fig_reasons, use_container_width=True)
    else:
        st.info("Нет данных по отмененным заказам для анализа причин.")
