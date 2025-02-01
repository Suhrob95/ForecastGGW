import streamlit as st
import pandas as pd
import openai
from dotenv import load_dotenv
import os
from forecasting import build_forecast  # Импортируем функцию обработки данных из модуля "Прогнозирование спроса"
import datetime

# Загружаем переменные из .env
load_dotenv()


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Предобработка данных из модуля "Прогнозирование спроса".
    """
    try:
        # Добавление даты на основе Year и Week
        df["Date"] = df.apply(
            lambda row: datetime.datetime.strptime(f"{int(row['Year'])}-{int(row['Week'])}-1", "%Y-%W-%w"),
            axis=1
        )
        df = df[df["Product"].notnull()]  # Убираем строки без продукта

        # Вызов функции build_forecast для дополнительной обработки данных
        forecasted_data = build_forecast(df)
        return forecasted_data
    except Exception as e:
        st.error(f"Ошибка предобработки данных: {e}")
        return pd.DataFrame()


def openai_chat(df: pd.DataFrame):
    """
    Чат-бот с использованием OpenAI API.
    Обрабатывает вопросы пользователя на основе отфильтрованных данных.
    """
    st.subheader("Спросите ИИ")

    # --- Проверяем, что df не None ---
    if df is None or df.empty:
        st.error("Данные не загружены или отсутствуют.")
        return

    # --- 1. Загружаем API-ключ из окружения ---
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        st.error("API-ключ OpenAI не найден. Проверьте файл .env.")
        return

    openai.api_key = openai_api_key

    # --- Список ресторанов ---
    restaurant_list = [
        "Samara Cosmoport", "Samara Mega", "Nijniy Novgorod Mega", "Nijniy Novgorod 7 Nebo",
        "Nijniy Novgorod Fantastika", "Nijniy Novgorod Nebo", "Kazan Mall", "Kazan Tandem",
        "Kazan Mega", "Kazan Koltso", "Kazan Yujniy", "Kazan Park House", "Moscow Metropolis",
        "Moscow Gagarinskiy", "Moscow Erevan Plaza", "Moscow Mega Tyopliy Stan", "Moscow Aviapark",
        "Moscow Afimall", "Khimki Mega", "Moscow RIO", "Moscow Fillion", "Moscow Columbus",
        "Moscow Kashirskoye Plaza", "Moscow Kaleydoscop", "Moscow Europolis", "Zelenograd Zelenopark",
        "Moscow Vegas", "Moscow Vodniy", "Moscow Mozaika", "Moscow Gorod", "Moscow Kuzminki Mall",
        "Moscow Mega Kotelniki", "Moscow Mega Kommunarka", "Moscow Salaris", "Nijnevartovsk GreenPark",
        "Ufa Mega", "Chelny Kvartal", "Ekaterinburg Veer Mall", "Ekaterinburg Greenvich",
        "Voronej Galereya Chijova", "Voronej Grad"
    ]

    # --- Список включенных товаров для подсказок ---
    included_products = [
        "П/Ф Говядина", "П/Ф Гагава", "П/Ф Курица в соусе", "П/Ф Лакомство от шефа", "П/Ф Цезарь", "П/Ф Чили",
        "П/Ф Кекиклим", "П/Ф Курица на суп", "П/Ф Картофель Фри 2,5 кг", "П/Ф Луковые кольца 1 кг",
        "Мозаика", "Пюре из баклажанов", "Соус Баффало", "Соус Песто", "Соус Сладкий перец",
        "Соус Тайский сладкий чили",
        "Торт манго-маракуйя", "Торт медовик", "Десерт фруктовый 'Сорбет' манго", "Мороженое 'Пломбир-ваниль'",
        "Мороженое с клубникой", "Мороженое шоколаденое с кус.шоколада", "Соус Балканский",
        "Makaroma Penne (Турция)", "Паста Bavette Barilla (Россия), 450г", "Паста Filini Barilla (Россия), 450г"
    ]

    # --- Выбор года (опционально) ---
    available_years = sorted(df['Year'].unique())
    selected_year = st.selectbox("Выберите год (необязательно):", ["Все годы"] + available_years)

    # --- Выбор ресторана (обязательно) ---
    available_restaurants = [col for col in restaurant_list if col in df.columns]
    if not available_restaurants:
        st.error("В датафрейме не найдено ни одного столбца с данными о ресторанах.")
        return

    selected_restaurant = st.selectbox("Выберите ресторан:", available_restaurants)
    if not selected_restaurant:
        st.warning("Пожалуйста, выберите ресторан для продолжения.")
        return

    # --- Фильтрация данных ---
    filtered_df = df.copy()
    if selected_year != "Все годы":
        filtered_df = filtered_df[filtered_df['Year'] == selected_year]

    if selected_restaurant not in filtered_df.columns:
        st.error(f"Данные для ресторана {selected_restaurant} отсутствуют.")
        return

    # Убираем из анализа продукты, не входящие в включенный список
    filtered_for_tips = filtered_df[filtered_df['Product'].isin(included_products)]

    # --- Выбор продукта (опционально) ---
    available_products = filtered_for_tips['Product'].unique()
    selected_product = st.selectbox("Выберите продукт (необязательно):", ["Все продукты"] + list(available_products))

    if selected_product != "Все продукты":
        filtered_for_tips = filtered_for_tips[filtered_for_tips['Product'] == selected_product]

    # --- Поле ввода для пользовательского вопроса ---
    user_question = st.text_area(
        "Ваш вопрос к модели (например, 'Сумма заказов П/Ф Чили' или 'Прогноз продаж П/Ф Цезарь'):", height=100)

    if st.button("Спросить у ИИ"):
        if user_question.strip():
            try:
                # Преобразование отфильтрованных данных в текстовый формат для анализа
                df_text = filtered_for_tips.to_csv(index=False)

                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",  # Используем указанную модель
                    messages=[
                        {"role": "system",
                         "content": "Ты - аналитик, помогай отвечать на вопросы по данным ресторана. Предоставляй "
                                    "аналитику и прогнозы на основе доступных данных."},
                        {"role": "user", "content": f"Вот данные ресторана: {df_text}. Вопрос: {user_question}"},
                    ],
                    temperature=0.2,
                    max_tokens=1000  # Ограничение на количество токенов
                )

                chat_answer = response.choices[0].message["content"]

                # Вывод результата
                st.write("### Ответ:")
                st.write(chat_answer)
            except Exception as e:
                st.error(f"Ошибка при обращении к ИИ: {str(e)}")
        else:
            st.warning("Пожалуйста, введите вопрос.")

    # --- Подсказки на основе отфильтрованных данных ---
    if not filtered_for_tips.empty:
        try:
            # Самый популярный продукт из списка включенных товаров
            top_product = filtered_for_tips.groupby('Product')[selected_restaurant].sum().idxmax()
            # Общий объем продаж в выбранном ресторане по включенным продуктам
            restaurant_sales = filtered_for_tips[selected_restaurant].sum()
            # Среднее количество заказов
            average_orders = filtered_for_tips[selected_restaurant].mean()

            st.info(f"Самый популярный продукт (производимые продукты) — {top_product}.")
            st.info(
                f"Продажи в ресторане {selected_restaurant} (производимые продукты) составляют {restaurant_sales:,}.")
            st.info(f"Среднее количество заказов в ресторане {selected_restaurant} — {average_orders:.2f}.")
        except Exception as e:
            st.error(f"Ошибка при анализе данных: {str(e)}")
