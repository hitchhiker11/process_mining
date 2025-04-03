import streamlit as st
import pandas as pd
from datetime import datetime

@st.cache_data # Кэшируем данные для производительности
def load_data(file_path='data/dataset.csv'):
    """
    Загружает и предобрабатывает данные из CSV файла.

    Args:
        file_path (str): Путь к файлу CSV.

    Returns:
        pd.DataFrame: Загруженный и обработанный DataFrame, или пустой DataFrame при ошибке.
    """
    try:
        # Указываем правильную кодировку и разделитель
        df = pd.read_csv(
            file_path,
            encoding='cp1251', # Очень вероятно, что это ваша кодировка
            sep='\t',          # Используем табуляцию как разделитель
            parse_dates=['start_time', 'end_time'],
            dayfirst=True      # Указываем, что день идет первым в дате (ДД.ММ.ГГГГ)
        )

        # Переименуем колонки для удобства (если нужно)
        # df.rename(columns={'Территория': 'territory', 'Оценка доставки': 'rating'}, inplace=True)
        # Оставляем оригинальные названия, т.к. они используются дальше

        # Преобразуем 'Оценка доставки' в числовой тип, ошибки превратятся в NaN
        df['Оценка доставки'] = pd.to_numeric(df['Оценка доставки'], errors='coerce')

        # Рассчитываем длительность этапа в минутах
        df['duration'] = (df['end_time'] - df['start_time']).dt.total_seconds() / 60
        # Обработка некорректной длительности (если end_time < start_time или NaN)
        df['duration'] = df['duration'].apply(lambda x: x if pd.notna(x) and x > 0 else 0)

        # Создание дополнительных признаков
        df['date'] = df['start_time'].dt.date
        df['hour'] = df['start_time'].dt.hour
        df['is_canceled'] = df['stage'].str.contains('Отмена', na=False).astype(int)

        # Добавляем статус заказа (упрощенно)
        # Находим последний этап для каждого заказа
        last_stage = df.loc[df.groupby('case')['end_time'].idxmax()]
        status_map = last_stage.set_index('case')['stage'].apply(
            lambda x: 'Отменен' if 'Отмена' in str(x) else ('Доставлен' if 'доставлен' in str(x) else 'В процессе')
        )
        df['order_status'] = df['case'].map(status_map)


        return df

    except FileNotFoundError:
        st.error(f"Файл '{file_path}' не найден. Убедитесь, что он существует и путь указан верно.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ошибка при загрузке или обработке данных: {e}")
        return pd.DataFrame()
