import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from datetime import datetime

# Загрузка и предобработка данных
@st.cache_data
def load_data():
    # !!! Убедитесь, что путь к файлу 'dataset.csv' правильный !!!
    try:
        df = pd.read_csv('dataset.csv', parse_dates=['start_time', 'end_time'])
        df['duration'] = (df['end_time'] - df['start_time']).dt.total_seconds() / 60  # в минутах
        # Обработка возможных пропусков в duration, если end_time < start_time
        df['duration'] = df['duration'].apply(lambda x: x if x > 0 else 0)
        return df
    except FileNotFoundError:
        st.error("Файл 'dataset.csv' не найден. Пожалуйста, убедитесь, что он находится в той же директории, что и скрипт, или укажите правильный путь.")
        return pd.DataFrame() # Возвращаем пустой DataFrame, чтобы избежать ошибок ниже
    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {e}")
        return pd.DataFrame()

df = load_data()

# Проверяем, загрузились ли данные
if not df.empty:
    # Создание признаков
    df['date'] = df['start_time'].dt.date
    df['hour'] = df['start_time'].dt.hour
    # Используем .str.contains для большей надежности
    df['is_canceled'] = df['stage'].str.contains('Отмена', na=False).astype(int)
    df['status'] = df['stage'].apply(lambda x: 'Canceled' if 'Отмена' in str(x) else ('Delivered' if 'доставлен' in str(x) else 'In Progress'))

    # Сайдбар с фильтрами
    st.sidebar.header('Фильтры')
    # Добавляем опцию "Все территории"
    territory_list = ['Все территории'] + sorted(df['Территория'].unique().tolist())
    selected_territory = st.sidebar.selectbox('Территория', territory_list)

    min_date = df['date'].min()
    max_date = df['date'].max()
    start_date, end_date = st.sidebar.date_input('Диапазон дат', [min_date, max_date])

    # Фильтрация данных
    # Конвертируем start_date и end_date в datetime для сравнения
    start_date_dt = pd.to_datetime(start_date).date()
    end_date_dt = pd.to_datetime(end_date).date()

    # Применяем фильтры
    filtered_df = df[
        (df['date'] >= start_date_dt) &
        (df['date'] <= end_date_dt)
    ]
    # Фильтр по территории, если выбрана конкретная территория
    if selected_territory != 'Все территории':
        filtered_df = filtered_df[filtered_df['Территория'] == selected_territory]

    # Проверка, есть ли данные после фильтрации
    if filtered_df.empty:
        st.warning("Нет данных для отображения с выбранными фильтрами.")
    else:
        # Вкладки
        tab1, tab2, tab3 = st.tabs(["Прогнозы", "Ресурсы", "Детализация"])

        with tab1:  # Прогнозы
            st.header("Прогнозы и риски")

            # Отмененные заказы (ранее "Топ рисковых")
            canceled_orders_df = filtered_df[filtered_df['is_canceled'] == 1]
            st.subheader(f"Отмененные заказы ({len(canceled_orders_df['case'].unique())} шт.)")
            if not canceled_orders_df.empty:
                # Показываем не только ID, но и стадию отмены и время начала
                st.dataframe(canceled_orders_df[['case', 'stage', 'start_time']].drop_duplicates(subset=['case']).rename(columns={
                    'case': 'Заказ',
                    'stage': 'Стадия отмены',
                    'start_time': 'Время начала (первого этапа)'
                }))
            else:
                st.write("Нет отмененных заказов за выбранный период.")

            # Важность факторов (пример)
            st.subheader("Важность факторов в модели ML (Пример)")
            st.info("Здесь должны отображаться реальные данные из вашей ML модели предсказания рисков (отмены, задержки и т.д.)")
            feature_importance = pd.DataFrame({
                'Фактор': ['Длительность сборки', 'Время суток', 'Территория', 'Нагрузка'],
                'Важность': [0.45, 0.3, 0.15, 0.1] # Пример данных
            })
            fig_fi = px.bar(feature_importance, x='Важность', y='Фактор', orientation='h', title="Пример важности факторов")
            st.plotly_chart(fig_fi)

            # A/B-тесты (плейсхолдер)
            st.subheader("A/B-тесты")
            st.info("Раздел для отображения результатов A/B-тестов.")
            st.write("""
            Здесь можно сравнивать эффективность различных подходов, например:
            - Влияние изменения интерфейса на конверсию в заказ.
            - Сравнение скорости доставки при разных стратегиях логистики (группа A vs группа B).
            - Эффективность разных промо-акций.

            Для реализации требуется сбор данных по разным группам A/B теста.
            """)
            # Пример графика (можно добавить, если есть данные)
            # ab_data = pd.DataFrame({'Группа': ['A', 'B'], 'Конверсия': [0.12, 0.15]})
            # fig_ab = px.bar(ab_data, x='Группа', y='Конверсия', title='Пример результата A/B теста')
            # st.plotly_chart(fig_ab)


        with tab2:  # Ресурсы
            st.header("Управление ресурсами")

            # Heatmap скорости (длительности этапов по часам)
            st.subheader("Heatmap средней длительности этапов по часам")
            # Убираем отмененные этапы из расчета средней длительности
            pivot_df = filtered_df[filtered_df['is_canceled'] == 0]
            if not pivot_df.empty:
                pivot = pivot_df.pivot_table(index='stage', columns='hour', values='duration', aggfunc='mean')
                fig_heatmap = px.imshow(pivot,
                                        labels=dict(x="Час начала этапа", y="Этап", color="Средняя длительность (мин)"),
                                        title="Средняя длительность этапов (мин) по часам дня")
                fig_heatmap.update_xaxes(side="top")
                st.plotly_chart(fig_heatmap)
            else:
                st.write("Недостаточно данных для построения heatmap.")

            # График Ганта
            st.subheader("График Ганта для примера заказа")
            # Попробуем взять последний активный или доставленный заказ для примера, если есть
            example_case_df = filtered_df[filtered_df['status'] != 'Canceled']
            if not example_case_df.empty:
                sample_case = example_case_df.iloc[-1]['case']
                st.write(f"Показан график для заказа: **{sample_case}**")
                gantt_data = filtered_df[filtered_df['case'] == sample_case][['stage', 'start_time', 'end_time', 'Территория']].sort_values(by='start_time')
                if not gantt_data.empty:
                    # Используем Plotly Express для Ганта (более современный)
                    fig_gantt = px.timeline(gantt_data, x_start="start_time", x_end="end_time", y="stage",
                                            color="Территория", title=f"График Ганта для заказа {sample_case}")
                    fig_gantt.update_yaxes(autorange="reversed") # Чтобы первый этап был сверху
                    st.plotly_chart(fig_gantt)
                else:
                    st.write("Не удалось найти данные для примера графика Ганта.")
            else:
                # Если нет активных/доставленных, попробуем отмененный
                example_case_df_canceled = filtered_df[filtered_df['status'] == 'Canceled']
                if not example_case_df_canceled.empty:
                    sample_case = example_case_df_canceled.iloc[0]['case']
                    st.write(f"Показан график для отмененного заказа: **{sample_case}**")
                    gantt_data = filtered_df[filtered_df['case'] == sample_case][['stage', 'start_time', 'end_time', 'Территория']].sort_values(by='start_time')
                    if not gantt_data.empty:
                         fig_gantt = px.timeline(gantt_data, x_start="start_time", x_end="end_time", y="stage",
                                            color="Территория", title=f"График Ганта для заказа {sample_case}")
                         fig_gantt.update_yaxes(autorange="reversed")
                         st.plotly_chart(fig_gantt)
                    else:
                        st.write("Не удалось найти данные для примера графика Ганта.")
                else:
                    st.write("Нет заказов для отображения графика Ганта.")


            # Загрузка vs. Качество (используем длительность как прокси качества)
            st.subheader("Загрузка vs. Качество (средняя длительность)")
            st.info("Анализ зависимости средней длительности всех этапов заказа от количества заказов, начатых в тот же час.")
            if not filtered_df.empty:
                # Рассчитываем количество уникальных заказов, начатых в каждый час
                hourly_load = filtered_df.groupby(['date', 'hour'])['case'].nunique().reset_index()
                hourly_load = hourly_load.rename(columns={'case': 'orders_started_per_hour'})

                # Рассчитываем среднюю общую длительность заказов, начатых в каждый час
                # Сначала найдем общую длительность каждого заказа
                order_total_duration = filtered_df[filtered_df['is_canceled'] == 0].groupby('case')['duration'].sum().reset_index()
                order_total_duration = order_total_duration.rename(columns={'duration': 'total_order_duration'})
                # Добавим час начала заказа
                order_start_hour = filtered_df[['case', 'hour']].drop_duplicates(subset=['case'])
                order_duration_with_hour = pd.merge(order_total_duration, order_start_hour, on='case')

                # Теперь усредним по часам
                avg_duration_per_hour = order_duration_with_hour.groupby('hour')['total_order_duration'].mean().reset_index()

                # Объединяем загрузку и среднюю длительность по часам (усредняя загрузку по всем дням)
                avg_hourly_load = hourly_load.groupby('hour')['orders_started_per_hour'].mean().reset_index()
                load_vs_quality_df = pd.merge(avg_hourly_load, avg_duration_per_hour, on='hour')

                if not load_vs_quality_df.empty:
                    fig_load_quality = px.scatter(load_vs_quality_df,
                                                  x='orders_started_per_hour',
                                                  y='total_order_duration',
                                                  labels={
                                                      'orders_started_per_hour': 'Среднее кол-во заказов, начатых в час',
                                                      'total_order_duration': 'Средняя общая длительность заказа (мин)'
                                                  },
                                                  title='Зависимость средней длительности заказа от часовой загрузки',
                                                  hover_data=['hour'])
                    fig_load_quality.update_traces(marker=dict(size=10))
                    st.plotly_chart(fig_load_quality)
                else:
                    st.write("Недостаточно данных для анализа загрузки и качества.")
            else:
                st.write("Недостаточно данных для анализа загрузки и качества.")


        with tab3:  # Детализация
            st.header("Детальный анализ")

            # Динамика отмен по дням (для выбранной территории или всех)
            st.subheader(f"Динамика отмен по дням ({selected_territory})")
            daily_cancel = filtered_df.groupby('date')['is_canceled'].sum().reset_index()
            if not daily_cancel.empty:
                fig_daily_cancel = px.line(daily_cancel, x='date', y='is_canceled',
                                           title=f'Количество отмененных заказов по дням ({selected_territory})',
                                           labels={'date': 'Дата', 'is_canceled': 'Кол-во отмен'})
                st.plotly_chart(fig_daily_cancel)
            else:
                st.write("Нет данных для отображения динамики отмен.")

            # Сравнение с нормативами
            st.subheader("Сравнение средней фактической длительности этапов с нормативами")
            # Нормативы (можно вынести в конфигурацию или отдельный файл)
            norms = {'Сборка': 30, 'Упаковка': 10, 'Доставка': 45} # Пример нормативов
            st.write(f"Используемые нормативы (в минутах): {norms}")

            # Рассчитываем среднюю фактическую длительность только для НЕ отмененных этапов
            actual_duration = filtered_df[filtered_df['is_canceled'] == 0].groupby('stage')['duration'].mean().reset_index()

            # Создаем DataFrame для сравнения
            comparison_data = []
            for stage, norm_value in norms.items():
                # Ищем фактическое значение для этапа
                actual_value = actual_duration[actual_duration['stage'].str.contains(stage, case=False, na=False)]['duration']
                if not actual_value.empty:
                    comparison_data.append({'Этап': stage, 'Факт': actual_value.values[0], 'Норматив': norm_value})
                else:
                    # Если этап не найден в данных, факт = 0
                    comparison_data.append({'Этап': stage, 'Факт': 0, 'Норматив': norm_value})

            comparison_df = pd.DataFrame(comparison_data)

            if not comparison_df.empty:
                fig_comparison = px.bar(comparison_df, x='Этап', y=['Факт', 'Норматив'],
                                        barmode='group', # Группируем бары рядом для сравнения
                                        title='Сравнение фактической длительности этапов с нормативами',
                                        labels={'value': 'Длительность (мин)', 'variable': 'Тип'})
                st.plotly_chart(fig_comparison)
            else:
                st.write("Недостаточно данных для сравнения с нормативами.")

            # Причины отмен
            st.subheader("Анализ причин отмен")
            canceled_stages = filtered_df[filtered_df['is_canceled'] == 1]['stage']
            if not canceled_stages.empty:
                reason_counts = canceled_stages.value_counts().reset_index()
                reason_counts.columns = ['Причина (этап отмены)', 'Количество']

                fig_reasons = px.bar(reason_counts,
                                     x='Количество',
                                     y='Причина (этап отмены)',
                                     orientation='h', # Горизонтальный бар для лучшей читаемости причин
                                     title='Распределение причин отмен (по этапу)')
                st.plotly_chart(fig_reasons)
            else:
                st.write("Нет данных по отмененным заказам для анализа причин.")

        st.write("---")
        st.write(f"Данные отфильтрованы для территории: **{selected_territory}**")
        st.write(f"Период: **{start_date_dt.strftime('%Y-%m-%d')}** - **{end_date_dt.strftime('%Y-%m-%d')}**")
        st.write(f"Данные обновлены: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

else:
    st.error("Не удалось загрузить или обработать данные. Дальнейшее отображение невозможно.")