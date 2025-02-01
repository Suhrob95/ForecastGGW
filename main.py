import streamlit as st
import pandas as pd

# Импортируем наши внутренние модули (которые будут реализованы далее)
from data_loader import load_excel_files
from data_preprocessing import preprocess_data
from forecasting import build_forecast
from portion_calc import calculate_portions
from scenario_planning import scenario_planning
from analysis_restaurants import analyze_restaurants
from behavior_analysis import analyze_seasonal_trends
from openai_integration import openai_chat
from reports import generate_reports


# Визуализация может использоваться в других файлах,
# поэтому здесь обычно достаточно импортировать plotly или matplotlib при необходимости
# но если нужна своя функция, то import visualization

def main():
    """Основная функция приложения Streamlit."""

    st.set_page_config(page_title="ForecastGGW", layout="wide")

    st.title("ForecastGGW – Аналитика и прогнозирование для ресторанной сети")

    # Боковая панель навигации
    option = st.sidebar.selectbox(
        "Меню приложения",
        (
            "Загрузка данных",
            "Прогнозирование спроса",
            "Расчёт порционности",
            "Сценарное моделирование (Что если?)",
            "Анализ динамики ресторанов",
            "Анализ сезонных трендов заказов продуктов по классификациям",
            "Генерация отчётов",
            "Спросите ИИ"
        )
    )

    # Если пользователь не загрузил/не предобработал данные,
    # мы храним их в st.session_state["df_clean"] после обработки
    # Поэтому проверяем, доступен ли уже DataFrame
    if option == "Загрузка данных":
        st.header("Шаг 1: Загрузка Excel-файлов")
        df = load_excel_files()
        if df is not None:
            st.write("Пример загруженных данных (первые строки):")
            st.dataframe(df.head())

            st.write("Далее запустим предобработку данных...")
            df_clean = preprocess_data(df)
            st.write("После предобработки (первые строки):")
            st.dataframe(df_clean.head())

            # Сохраняем результат в session_state
            st.session_state["df_clean"] = df_clean

    elif option == "Прогнозирование спроса":
        st.header("Шаг 2: Прогнозирование спроса")
        if "df_clean" in st.session_state:
            build_forecast(st.session_state["df_clean"])
        else:
            st.warning("Пожалуйста, сначала загрузите и предобработайте данные (раздел 'Загрузка данных').")

    elif option == "Расчёт порционности":
        st.header("Расчёт порционности и оптимизация закупок")
        if "df_clean" in st.session_state:
            calculate_portions(st.session_state["df_clean"])
        else:
            st.warning("Сначала загрузите и предобработайте данные.")

    elif option == "Сценарное моделирование (Что если?)":
        st.header("Модуль, Что если?")
        if "df_clean" in st.session_state:
            scenario_planning(st.session_state["df_clean"])
        else:
            st.warning("Сначала загрузите и предобработайте данные.")

    elif option == "Анализ динамики ресторанов":
        st.header("Анализ динамики ресторанов")
        if "df_clean" in st.session_state:
            analyze_restaurants(st.session_state["df_clean"])
        else:
            st.warning("Сначала загрузите и предобработайте данные.")

    elif option == "Анализ сезонных трендов заказов продуктов по классификациям":

        st.header("Анализ заказанных продуктов")

        if "df_clean" in st.session_state:

            analyze_seasonal_trends(st.session_state["df_clean"])  # Убедитесь, что имя функции правильное

        else:

            st.warning("Сначала загрузите и предобработайте данные.")

    elif option == "Генерация отчётов":
        st.header("Формирование отчётов")
        if "df_clean" in st.session_state:
            generate_reports(st.session_state["df_clean"])
        else:
            st.warning("Сначала загрузите и предобработайте данные.")

    elif option == "Спросите ИИ":
        st.header("Чат-бот на естественном языке")
        if "df_clean" in st.session_state:
            openai_chat(st.session_state["df_clean"])
        else:
            st.warning("Сначала загрузите и предобработайте данные.")


if __name__ == "__main__":
    main()
