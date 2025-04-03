import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import numpy as np

def render_resources_tab(filtered_df):
    """Отрисовывает вкладку 'Ресурсы'."""
    st.header("Анализ ресурсов и загрузки")

    # 1. Heatmap скорости сборки
    st.subheader("Тепловая карта средней скорости этапов по часам и территориям")

    # Выбор этапа для анализа
    stage_options = ['Все этапы'] + sorted(filtered_df['stage'].unique().tolist())
    selected_stage_for_heatmap = st.selectbox("Выберите этап для анализа скорости:", stage_options)

    heatmap_data = filtered_df[filtered_df['is_canceled'] == 0].copy() # Исключаем отмененные

    if selected_stage_for_heatmap != 'Все этапы':
         heatmap_data = heatmap_data[heatmap_data['stage'] == selected_stage_for_heatmap]

    if not heatmap_data.empty:
        # Группируем по территории и часу, считаем среднюю длительность
        speed_pivot = pd.pivot_table(heatmap_data,
                                     values='duration',
                                     index='Территория',
                                     columns='hour',
                                     aggfunc=np.mean) # Используем numpy.mean

        if not speed_pivot.empty:
            fig_heatmap = px.imshow(speed_pivot,
                                    labels=dict(x="Час начала этапа", y="Территория", color="Средняя длительность (мин)"),
                                    title=f"Средняя длительность этапа '{selected_stage_for_heatmap}' (минуты)",
                                    text_auto=".1f", # Отображать значения с 1 знаком после запятой
                                    aspect="auto", # Автоматический подбор соотношения сторон
                                    color_continuous_scale="RdYlGn_r") # Красно-Желто-Зеленая шкала (красный = долго)
            fig_heatmap.update_xaxes(side="top", dtick=1) # Ось X сверху, метки каждый час
            fig_heatmap.update_yaxes(dtick=1)
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info(f"Нет данных для построения тепловой карты для этапа '{selected_stage_for_heatmap}' с выбранными фильтрами.")
    else:
        st.info(f"Нет данных для этапа '{selected_stage_for_heatmap}' с выбранными фильтрами.")


    # 2. График Ганта для примера заказа
    st.subheader("График Ганта для примера заказа")
    # Выбираем один случайный НЕ отмененный заказ из отфильтрованных данных
    non_canceled_cases = filtered_df[filtered_df['order_status'] != 'Отменен']['case'].unique()
    if len(non_canceled_cases) > 0:
        example_case_id = np.random.choice(non_canceled_cases)
        gantt_df = filtered_df[filtered_df['case'] == example_case_id].sort_values(by='start_time')

        st.write(f"Показан график для заказа: **{example_case_id}**")

        fig_gantt = px.timeline(gantt_df,
                                x_start="start_time",
                                x_end="end_time",
                                y="stage",
                                color="stage", # Раскрашиваем по этапам
                                labels={"stage": "Этап"},
                                title=f"Временная диаграмма выполнения заказа {example_case_id}")
        fig_gantt.update_yaxes(autorange="reversed") # Этапы сверху вниз в порядке выполнения
        fig_gantt.update_layout(showlegend=False) # Можно скрыть легенду, если этапы подписаны на оси Y
        st.plotly_chart(fig_gantt, use_container_width=True)
    else:
        st.info("Нет выполненных или находящихся в процессе заказов для отображения примера графика Ганта.")


    # 3. График "Загрузка vs. Качество" (используем Оценку доставки)
    st.subheader("Зависимость оценки доставки от часовой загрузки")
    st.info("ℹ️ Анализируется средняя оценка успешно доставленных заказов в зависимости от среднего количества заказов, стартовавших в этот час.")

    # Рассчитываем среднее количество уникальных заказов, начатых в каждый час
    hourly_load = filtered_df.groupby(['date', 'hour'])['case'].nunique().reset_index()
    avg_hourly_load = hourly_load.groupby('hour')['case'].mean().reset_index().rename(columns={'case': 'avg_orders_per_hour'})

    # Рассчитываем среднюю оценку доставленных заказов по часам
    delivered_orders = filtered_df[filtered_df['order_status'] == 'Доставлен'].copy()
    # Убираем заказы без оценки
    delivered_orders.dropna(subset=['Оценка доставки'], inplace=True)

    if not delivered_orders.empty:
        # Нужна оценка для каждого заказа, берем первую непустую оценку, если их несколько
        order_ratings = delivered_orders.groupby('case')['Оценка доставки'].first().reset_index()
        # Добавляем час начала заказа
        order_start_hour = delivered_orders[['case', 'hour']].drop_duplicates(subset=['case'])
        ratings_with_hour = pd.merge(order_ratings, order_start_hour, on='case')

        # Усредняем оценку по часам
        avg_hourly_rating = ratings_with_hour.groupby('hour')['Оценка доставки'].mean().reset_index()

        # Объединяем загрузку и качество
        load_vs_quality_df = pd.merge(avg_hourly_load, avg_hourly_rating, on='hour')

        if not load_vs_quality_df.empty:
            fig_load_quality = px.scatter(load_vs_quality_df,
                                          x='avg_orders_per_hour',
                                          y='Оценка доставки',
                                          labels={
                                              'avg_orders_per_hour': 'Среднее кол-во заказов, начатых в час',
                                              'Оценка доставки': 'Средняя оценка доставленных заказов'
                                          },
                                          title='Зависимость оценки доставки от часовой загрузки',
                                          hover_data=['hour'], # Показываем час при наведении
                                          trendline="ols", # Добавляем линию тренда
                                          trendline_color_override="red")
            fig_load_quality.update_traces(marker=dict(size=10))
            st.plotly_chart(fig_load_quality, use_container_width=True)
        else:
            st.info("Недостаточно данных (после фильтрации и удаления заказов без оценки) для анализа зависимости оценки от загрузки.")
    else:
        st.info("Нет успешно доставленных заказов с оценками в выбранном периоде/территории для анализа.")
