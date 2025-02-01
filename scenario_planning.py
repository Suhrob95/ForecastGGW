import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io


def scenario_planning(df: pd.DataFrame):
    """
    Модуль "Что если". Позволяет моделировать разные сценарии:
      - Открытие новых ресторанов
      - Изменение цены на продукт (влияние на спрос)
      - Коррекция нормы порции
      - Любые другие факторы, задаваемые пользователем
    """
    st.subheader("Сценарное моделирование")

    # Список продуктов для анализа
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

    # Шаг 1. Выбор ресторана или общих показателей
    restaurant_cols = [col for col in df.columns if
                       col not in {"Year", "Month", "Case kg", "Week", "Product", "Total", "SeasonFlag"}]
    restaurant_selection = st.selectbox("Выберите ресторан или общий показатель:",
                                        ["Общие показатели"] + restaurant_cols)

    if restaurant_selection == "Общие показатели":
        # Рассчитываем среднее значение продаж за неделю по всем годам и ресторанам
        df_filtered["Base Sales"] = df_filtered.groupby(["Year", "Week", "Product"])["Total"].transform("mean")
        overall_base_sales = df_filtered.groupby("Product")["Base Sales"].mean().reset_index()
        overall_base_sales.columns = ["Продукт", "Базовые продажи"]
    else:
        # Рассчитываем только по выбранному ресторану
        if restaurant_selection not in df.columns:
            st.error("Выбранный ресторан отсутствует в данных.")
            return
        df_filtered = df_filtered[df_filtered[restaurant_selection] > 0]
        df_filtered["Base Sales"] = df_filtered[restaurant_selection]
        overall_base_sales = df_filtered.groupby("Product")["Base Sales"].mean().reset_index()
        overall_base_sales.columns = ["Продукт", "Базовые продажи"]

    # Шаг 2. Пользователь задаёт ключевые параметры
    st.write("1) Изменение цены на каждый продукт (или общее изменение для всех продуктов).")

    # Вариант изменения цен: индивидуально или для всех
    price_change_type = st.radio("Выберите способ изменения цен:",
                                 ("Индивидуально по каждому продукту", "Общее изменение для всех продуктов"))

    # Словарь для хранения изменений цены
    price_changes = {}

    if price_change_type == "Индивидуально по каждому продукту":
        for product in selected_products:
            price_changes[product] = st.slider(f"Изменение цены для {product} (%)", min_value=-50, max_value=100,
                                               value=0, step=5)
    else:
        global_price_change = st.slider("Общее изменение цены для всех продуктов (%)", min_value=-50, max_value=100,
                                        value=0, step=5)
        for product in selected_products:
            price_changes[product] = global_price_change

    st.write("2) Изменение нормы порции (если мы хотим увеличить/уменьшить размер).")
    portion_change_percent = st.slider("Изменение нормы порции, %", min_value=-50, max_value=50, value=0, step=5)

    st.write("3) Количество новых ресторанов, которые планируется открыть.")
    new_restaurants_count = st.number_input("Число новых ресторанов", min_value=0, max_value=50, value=0, step=1)

    st.write("4) Прочие факторы (например, планируемая акция).")
    promo_change_percent = st.slider("Укажите процент повышения спроса при акции (%)", min_value=0, max_value=100,
                                     value=20, step=5)

    # Шаг 3. Расчёт сценарных продаж для каждого продукта
    scenario_sales = []
    elasticity = -1.0  # Эластичность цены
    for _, row in overall_base_sales.iterrows():
        product = row["Продукт"]
        base_sales = row["Базовые продажи"]

        # Изменение цены
        price_factor = 1.0 + (price_changes[product] / 100.0) * elasticity
        new_sales = base_sales * price_factor

        # Изменение нормы порции
        portion_factor = 1.0 + (portion_change_percent / 100.0)
        new_sales *= portion_factor

        # Учёт новых ресторанов
        new_restaurant_factor = 0.05  # Каждый новый ресторан даёт 5% от базовых продаж
        new_sales += new_restaurants_count * (base_sales * new_restaurant_factor)

        # Промо-акция
        new_sales *= 1.0 + (promo_change_percent / 100.0)

        # Добавляем результат в список
        scenario_sales.append({"Продукт": product, "Базовые продажи": base_sales, "Сценарные продажи": new_sales})

    # Шаг 4. Создание DataFrame для отображения результатов
    scenario_df = pd.DataFrame(scenario_sales)
    scenario_df["Изменение (%)"] = ((scenario_df["Сценарные продажи"] - scenario_df["Базовые продажи"]) /
                                    scenario_df["Базовые продажи"] * 100).round(2)

    # Вывод таблицы
    st.write("### Таблица результатов:")
    st.dataframe(scenario_df)

    # Кнопка для скачивания отчёта в формате Excel
    st.write("### Скачивание отчёта:")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        scenario_df.to_excel(writer, index=False, sheet_name="Scenario Report")
    excel_data = output.getvalue()

    st.download_button(
        label="Скачать отчёт в формате Excel",
        data=excel_data,
        file_name="Сценарное_моделирование.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Шаг 5. Построение графиков
    st.write("### Визуализация данных:")

    # График сравнения базовых и сценарных продаж
    fig = px.bar(
        scenario_df,
        x="Продукт",
        y=["Базовые продажи", "Сценарные продажи"],
        title="Сравнение базовых и сценарных продаж",
        labels={"value": "Продажи", "Продукт": "Продукт"},
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True)

    # График изменения продаж в процентах
    fig_change = px.bar(
        scenario_df,
        x="Продукт",
        y="Изменение (%)",
        title="Изменение продаж в процентах",
        labels={"Изменение (%)": "Изменение (%)", "Продукт": "Продукт"}
    )
    st.plotly_chart(fig_change, use_container_width=True)

    st.success("Сценарий рассчитан! Можете менять параметры и смотреть результат.")
