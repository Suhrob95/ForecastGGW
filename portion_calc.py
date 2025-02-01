import streamlit as st
import pandas as pd
import plotly.express as px
import io


def calculate_portions(df: pd.DataFrame):
    """
    Расчёт количества порций и рекомендации по закупкам.
    Предполагается, что:
      - df содержит столбцы Product, Total, Year, Week.
      - у нас есть справочник (dict) с весом одной порции для каждого продукта.
    """
    st.subheader("Расчёт порционности и оптимизация закупок")

    # Шаг 1. Справочник весов порций (kg на одну порцию)
    portion_dict = {
        "П/Ф Говядина": 0.2,
        "П/Ф Гагава": 0.2,
        "П/Ф Курица в соусе": 0.2,
        "П/Ф Лакомство от шефа": 0.2,
        "П/Ф Цезарь": 0.2,
        "П/Ф Чили": 0.2,
        "П/Ф Кекиклим": 0.2,
        "П/Ф Курица на суп": 0.25,
        "П/Ф Картофель Фри 2,5 кг": 0.1,
        "П/Ф Луковые кольца 1 кг": 0.1,
        "Мозаика": 0.09,
        "Пюре из баклажанов": 0.1,
        "Соус Баффало": 0.02,
        "Соус Песто": 0.04,
        "Соус Сладкий перец": 0.02
    }

    # Шаг 2. Проверка наличия необходимых столбцов
    required_columns = {"Year", "Week", "Product", "Total"}
    if not required_columns.issubset(df.columns):
        st.error(f"Необходимые столбцы отсутствуют в данных: {required_columns - set(df.columns)}")
        return

    # Шаг 3. Выбор года и недели для анализа
    years = df["Year"].unique()
    selected_year = st.selectbox("Выберите год для анализа", years)

    weeks = df[df["Year"] == selected_year]["Week"].unique()
    selected_week = st.selectbox("Выберите неделю для анализа", sorted(weeks))

    # Фильтруем данные за выбранный год и неделю
    df_selected_period = df[(df["Year"] == selected_year) & (df["Week"] == selected_week)]
    if df_selected_period.empty:
        st.warning(f"Нет данных за выбранный период: год {selected_year}, неделя {selected_week}.")
        return

    # Шаг 4. Фильтруем продукты, указанные в справочнике порций
    df_selected_period = df_selected_period[df_selected_period["Product"].isin(portion_dict.keys())]
    if df_selected_period.empty:
        st.warning("Нет продуктов из справочника порций в данных за выбранный период.")
        return

    # Шаг 5. Расчёт порций для каждого продукта
    st.write(f"Результаты расчёта для выбранного периода: год **{selected_year}**, неделя **{selected_week}**")
    results = []
    for product in df_selected_period["Product"].unique():
        total_kg = df_selected_period[df_selected_period["Product"] == product]["Total"].sum()
        weight_per_portion = portion_dict[product]
        portion_count = total_kg / weight_per_portion
        results.append({
            "Продукт": product,
            "Общий вес (кг)": int(total_kg),  # Приводим к целому числу
            "Вес одной порции (кг)": weight_per_portion,
            "Количество порций": int(portion_count)  # Убираем дробную часть
        })

    # Создание DataFrame с форматированием
    results_df = pd.DataFrame(results)

    # Форматирование чисел: убираем запятые
    results_df["Количество порций"] = results_df["Количество порций"].apply(lambda x: f"{x:,}".replace(",", ""))

    # Визуализация с помощью Plotly
    st.write("### Визуализация данных:")
    fig = px.bar(
        results_df,
        x="Продукт",
        y="Количество порций",
        title=f"Количество порций по каждому продукту ({selected_year}, неделя {selected_week})",
        labels={"Количество порций": "Количество порций", "Продукт": "Продукт"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Вывод таблицы
    st.write("### Таблица результатов:")
    st.dataframe(results_df)

    # Кнопка для скачивания Excel-отчёта
    st.write("### Скачивание отчёта")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        results_df.to_excel(writer, index=False, sheet_name="Portions Report")
    excel_data = output.getvalue()

    st.download_button(
        label="Скачать отчёт в формате Excel",
        data=excel_data,
        file_name=f"Portions_Report_{selected_year}_Week_{selected_week}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Сохранение данных в session_state для возможного экспорта
    st.session_state["portion_results"] = results_df

    st.success("Расчёт завершён!")
