import streamlit as st
import pandas as pd
import plotly.express as px


def analyze_seasonal_trends(df: pd.DataFrame):

    """
    Модуль для анализа сезонных трендов продаж продуктов по классификациям.
    """
    st.title("Анализ сезонных трендов заказов продуктов по классификациям")

    # --- Классификации продуктов ---
    classifications = {
        "Мясные ПФ собственного производства": [
            "П/Ф Говядина", "П/Ф Гагава", "П/Ф Курица в соусе", "П/Ф Лакомство от шефа",
            "П/Ф Цезарь", "П/Ф Чили", "П/Ф Кекиклим", "П/Ф Курица на суп"
        ],
        "Соуса собственного производства": [
            "Пюре из баклажанов", "Соус Баффало", "Соус Песто", "Соус Сладкий перец", "Соус Тайский сладкий чили"
        ],
        "Горячие напитки": [
            "Кофе", "Чай зеленый Гринфилд Хармони Лэнд 250гр. ( класс-ий )",
            "Чай зеленый Гринфилд Флаинг Драгон 100пак. ( класс-ий )",
            "Чай зеленый Гринфилд Гарден Минт 250гр.(мятный)",
            "Чай черный Гринфилд Рич Цейлон 250гр. (класс-ий)",
            "Чай черный Гринфилд Карибиан Фрут 250гр. ( фруктовый )",
            "Чай черный Гринфилд Маунтэн Тайм 250гр. ( чабрец )", "Чай черный Гринфилд Голден Цейлон 100пак. (класс-ий)"
        ],
        "Холодные напитки": [
            "Добрый Кола ЖБ 0,33", "Добрый Кола Zero ЖБ 0,33", "Добрый Апельсин ЖБ 0,33",
            "Добрый Лимон-Лайм ЖБ 0,33", "Rich чай черный персик ПЭТ 0,5", "Rich чай черный лимон ПЭТ 0,5",
            "Бон-Аква нгаз пэт 0.5", "Бон-Аква сгаз пэт 0.5"
        ],
        "Десерты": [
            "Торт манго-маракуйя", "Торт медовик", "Десерт фруктовый \"Сорбет\" манго",
            "Мороженое \"Пломбир-ваниль\"", "Мороженое с клубникой",
            "Мороженое шоколаденое с кус.шоколада", "Мозаика"
        ]
    }

    # --- Фильтрация данных ---
    all_products = [product for products in classifications.values() for product in products]
    df_filtered = df[df["Product"].isin(all_products)]
    if df_filtered.empty:
        st.warning("Нет данных по указанным продуктам.")
        return

    # --- Выбор года ---
    selected_year = st.sidebar.selectbox("Выберите год для анализа", sorted(df["Year"].unique()))
    df_year = df_filtered[df_filtered["Year"] == selected_year]

    # --- Фильтрация ресторанов ---
    restaurants = [
        "Samara Cosmoport", "Samara Mega", "Nijniy Novgorod Mega", "Nijniy Novgorod 7 Nebo",
        "Nijniy Novgorod Fantastika", "Nijniy Novgorod Nebo", "Kazan Mall", "Kazan Tandem", "Kazan Mega",
        "Kazan Koltso", "Kazan Yujniy", "Kazan Park House", "Moscow Metropolis", "Moscow Gagarinskiy",
        "Moscow Erevan Plaza", "Moscow Mega Tyopliy Stan", "Moscow Aviapark", "Moscow Afimall", "Khimki Mega",
        "Moscow RIO", "Moscow Fillion", "Moscow Columbus", "Moscow Kashirskoye Plaza", "Moscow Kaleydoscop",
        "Moscow Europolis", "Zelenograd Zelenopark", "Moscow Vegas", "Moscow Vodniy", "Moscow Mozaika",
        "Moscow Gorod", "Moscow Kuzminki Mall", "Moscow Mega Kotelniki", "Moscow Mega Kommunarka",
        "Moscow Salaris", "Nijnevartovsk GreenPark", "Ufa Mega", "Chelny Kvartal", "Ekaterinburg Veer Mall",
        "Ekaterinburg Greenvich", "Voronej Galereya Chijova", "Voronej Grad"
    ]

    restaurant_cols = [col for col in df_year.columns if col in restaurants]
    if not restaurant_cols:
        st.warning("В данных нет ресторанов из списка.")
        return

    # --- Определяем сезоны ---
    winter_weeks = {1, 2, 3, 4, 5, 6, 7, 8, 9, 47, 48, 49, 50, 51, 52}
    summer_weeks = {21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32}
    holiday_weeks = {1, 2, 7, 8, 10, 19, 20, 23, 25, 47, 51, 52}
    regular_weeks = {11, 12, 13, 14, 15, 16, 17, 18, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46}

    df_year["Season"] = df_year["Week"].apply(
        lambda x: "Зима" if x in winter_weeks else
        "Лето" if x in summer_weeks else
        "Праздники" if x in holiday_weeks else
        "Обычные недели"
    )

    # --- Подсчёт общей суммы ---
    st.subheader(f"Общее количество продаж по классификациям за {selected_year} год")
    classification_totals = []

    for classification, products in classifications.items():
        total_sales = df_year[df_year["Product"].isin(products)]["Total"].sum()
        classification_totals.append({"Классификация": classification, "Общее количество": total_sales})

    totals_df = pd.DataFrame(classification_totals)
    st.dataframe(totals_df)

    # --- График по классификациям ---
    fig_totals = px.bar(
        totals_df,
        x="Классификация",
        y="Общее количество",
        title="Общее количество продаж по классификациям",
        labels={"Общее количество": "Сумма продаж", "Классификация": "Классификация"}
    )
    st.plotly_chart(fig_totals, use_container_width=True)

    # --- Средние продажи за одну неделю ---
    week_counts = {
        "Зима": len(winter_weeks),
        "Лето": len(summer_weeks),
        "Праздники": len(holiday_weeks),
        "Обычные недели": len(regular_weeks)
    }

    season_sales = df_year.groupby("Season")["Total"].sum().reset_index()
    season_sales["Среднее значение за неделю"] = season_sales.apply(
        lambda row: row["Total"] / week_counts[row["Season"]], axis=1
    )

    avg_regular_week = season_sales[season_sales["Season"] == "Обычные недели"]["Среднее значение за неделю"].values[0]

    # Преобразуем в проценты относительно обычных недель
    season_sales["Среднее значение (в процентах)"] = (
                                                             season_sales[
                                                                 "Среднее значение за неделю"] / avg_regular_week
                                                     ) * 100

    # --- Круговая диаграмма ---
    st.subheader(f"Средние продажи по сезонам за одну неделю ({selected_year})")
    fig_season = px.pie(
        season_sales,
        names="Season",
        values="Среднее значение (в процентах)",
        title=f"Средние продажи по сезонам за одну неделю ({selected_year})"
    )
    fig_season.update_layout(
        width=600,
        height=600
    )
    st.plotly_chart(fig_season, use_container_width=False)

    st.success("Анализ завершён! Вы можете выбрать другие параметры.")
