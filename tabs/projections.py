import streamlit as st
import pandas as pd
import plotly.express as px

def render_projections_tab(filtered_df):
    """Отрисовывает вкладку 'Прогнозы'."""
    st.header("Прогнозы и риски")

    # 1. Топ рисковых заказов (Отмененные заказы)
    st.subheader("Отмененные заказы")
    canceled_orders_df = filtered_df[filtered_df['is_canceled'] == 1]
    unique_canceled_cases = canceled_orders_df.drop_duplicates(subset=['case'])

    st.metric("Количество отмененных заказов", len(unique_canceled_cases))

    if not unique_canceled_cases.empty:
        st.write("Детализация отмененных заказов (показан этап отмены):")
        # Показываем ID, этап отмены и время начала этапа отмены
        st.dataframe(unique_canceled_cases[['case', 'stage', 'start_time']].rename(columns={
            'case': 'Заказ',
            'stage': 'Стадия отмены',
            'start_time': 'Время отмены'
        }), use_container_width=True)
    else:
        st.info("Нет отмененных заказов за выбранный период и по выбранной территории.")

    # 2. Важность факторов (пример)
    st.subheader("Важность факторов в модели ML (Пример)")
    st.info("ℹ️ Этот график показывает примерные данные. Для реального анализа подключите результаты вашей ML модели.")
    # Пример данных важности факторов
    feature_importance = pd.DataFrame({
        'Фактор': ['Время суток', 'Территория', 'Загрузка курьеров', 'Тип товаров', 'Длительность сборки'],
        'Важность': [0.35, 0.25, 0.20, 0.15, 0.05] # Примерные значения
    })
    fig_fi = px.bar(feature_importance.sort_values(by='Важность', ascending=True),
                    x='Важность',
                    y='Фактор',
                    orientation='h',
                    title="Пример: Факторы, влияющие на риск отмены/задержки")
    fig_fi.update_layout(yaxis_title=None) # Убрать заголовок оси Y
    st.plotly_chart(fig_fi, use_container_width=True)

    # 3. A/B-тесты (плейсхолдер)
    st.subheader("A/B-тесты")
    st.info("ℹ️ Раздел для отображения результатов A/B-тестирования.")
    with st.expander("Подробнее об A/B-тестах"):
        st.write("""
        Здесь можно сравнивать эффективность различных изменений в процессе или интерфейсе:
        - **Пример 1:** Сравнение конверсии в заказ при разных вариантах оформления кнопки "Заказать".
        - **Пример 2:** Влияние нового алгоритма распределения заказов на среднее время доставки (Группа A - старый алгоритм, Группа B - новый).
        - **Пример 3:** Эффективность различных скидочных механик на средний чек.

        Для реализации требуется настроить сбор данных, разделяя пользователей или заказы на контрольную (A) и тестовую (B) группы, и затем анализировать ключевые метрики для каждой группы.
        """)
    # Закомментированный пример графика для A/B теста
    # try:
    #     # Загрузите или сформируйте данные A/B теста
    #     ab_data = pd.DataFrame({'Группа': ['A (Контроль)', 'B (Тест)'], 'Среднее время доставки (мин)': [45.2, 41.8]})
    #     fig_ab = px.bar(ab_data, x='Группа', y='Среднее время доставки (мин)',
    #                     title='Пример A/B теста: Время доставки',
    #                     color='Группа', text_auto=True)
    #     st.plotly_chart(fig_ab, use_container_width=True)
    # except Exception as e:
    #     st.warning(f"Не удалось построить пример графика A/B теста: {e}")
