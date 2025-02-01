import streamlit as st
import pandas as pd
import plotly.express as px


def analyze_restaurants(df: pd.DataFrame):
    """
    Анализ продаж ресторанов с различными визуализациями.
    """
    st.title("Анализ продаж в ресторанах")

    # --- Список продуктов для анализа ---
    selected_products = [
        "П/Ф Говядина",
        "П/Ф Гагава",
        "П/Ф Курица в соусе",
        "П/Ф Лакомство от шефа",
        "П/Ф Цезарь",
        "П/Ф Чили",
        "П/Ф Кекиклим",
        "П/Ф Курица на суп",
        "П/Ф Картофель Фри 2,5 кг",
        "П/Ф Луковые кольца 1 кг",
        "Мозаика",
        "Пюре из баклажанов",
        "Соус Баффало",
        "Соус Песто",
        "Соус Сладкий перец"
    ]

    # Фильтруем данные только по указанным продуктам
    df_filtered = df[df["Product"].isin(selected_products)]
    if df_filtered.empty:
        st.warning("Нет данных по указанным продуктам.")
        return

    # --- Определяем ресторанные столбцы ---
    base_cols = {"Year", "Month", "Product", "Total", "Week", "Case kg", "SeasonFlag", "Date"}
    restaurant_cols = [col for col in df.columns if col not in base_cols]

    if not restaurant_cols:
        st.warning("В данных не обнаружено столбцов с ресторанами. Проверьте формат данных.")
        return

    # --- Фильтры: выбор года, города, ресторана и продукта ---
    st.sidebar.header("Фильтры анализа")
    selected_year = st.sidebar.selectbox("Выберите год", sorted(df["Year"].unique()))

    cities = set()
    for col in restaurant_cols:
        city_name = col.split()[0]
        cities.add(city_name)
    cities = list(cities)

    if not cities:
        st.warning("Не удалось определить города из данных.")
        return

    selected_city = st.sidebar.selectbox("Выберите город", cities)

    city_cols = [col for col in restaurant_cols if col.startswith(selected_city)]
    if not city_cols:
        st.warning(f"В городе {selected_city} не найдено ресторанов.")
        return

    selected_restaurant = st.sidebar.selectbox("Выберите ресторан", city_cols)
    selected_product = st.sidebar.selectbox("Выберите продукт для анализа", selected_products)

    # --- Анализ динамики ресторана ---
    st.subheader(f"Динамика продаж продукта '{selected_product}' в ресторане: {selected_restaurant}")

    df_rest = df_filtered[(df_filtered["Product"] == selected_product)]

    # Преобразуем столбец ресторана в числовой формат
    if not pd.api.types.is_numeric_dtype(df_rest[selected_restaurant]):
        df_rest[selected_restaurant] = pd.to_numeric(df_rest[selected_restaurant], errors='coerce')

    df_rest = df_rest.groupby(["Year", "Month"])[selected_restaurant].sum().reset_index()
    df_rest["Дата"] = pd.to_datetime(df_rest[["Year", "Month"]].assign(DAY=1))

    fig_line = px.line(
        df_rest,
        x="Дата",
        y=selected_restaurant,
        title=f"Динамика продаж продукта '{selected_product}' в ресторане {selected_restaurant}",
        labels={"Дата": "Месяц", selected_restaurant: "Продажи"},
        markers=True
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # --- Круговая диаграмма продаж продуктов в ресторане ---
    st.subheader("Доля продуктов в продажах ресторана")

    df_dynamic = df_filtered.groupby(["Year", "Product"])[selected_restaurant].sum(numeric_only=True).reset_index()
    fig_pie = px.pie(
        df_dynamic[df_dynamic["Year"] == selected_year],
        names="Product",
        values=selected_restaurant,
        title=f"Доля продаж продуктов в ресторане {selected_restaurant} за {selected_year} год",
        hole=0.3,
        width=800,
        height=800
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # --- Сравнительный анализ по городам ---
    st.subheader("Сравнительный анализ по городам")

    if city_cols:
        df_city = (
            df_filtered[(df_filtered["Product"] == selected_product) & (df_filtered["Year"] == selected_year)]
            .groupby(city_cols)
            .sum(numeric_only=True)
            .reset_index()
        )

        df_city = df_city.melt(value_vars=city_cols, var_name="Ресторан", value_name="Продажи")

        fig_city = px.bar(
            df_city,
            x="Ресторан",
            y="Продажи",
            title=f"Продажи продукта '{selected_product}' в ресторанах города {selected_city} за {selected_year} год",
            labels={"Ресторан": "Ресторан", "Продажи": "Сумма продаж"}
        )
        st.plotly_chart(fig_city, use_container_width=True)

    st.success("Анализ завершён! Вы можете выбрать другие параметры.")

