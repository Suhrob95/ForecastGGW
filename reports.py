import streamlit as st
import pandas as pd
import io
import plotly.express as px


def generate_reports(df: pd.DataFrame):
    """
    Генерация отчётов в Excel по разрешённым продуктам и фильтрацией по году.
    """
    st.subheader("Формирование отчётов")

    # Разрешённые продукты
    allowed_products = [
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
        "Соус Сладкий перец",
        "Соус Тайский сладкий чили",
        "Сироп малина",
        "Сироп грейпфрут",
        "Сироп карамельный",
        "Сироп ванильный",
        "Торт манго-маракуйя",
        "Торт медовик",
        "Десерт фруктовый \"Сорбет\" манго",
        "Мороженое \"Пломбир-ваниль\"",
        "Мороженое с клубникой",
        "Мороженое шоколаденое с кус.шоколада",
        "Соус Балканский",
        "Кофе",
        "Чечевица",
        "Makaroma Penne (Турция)",
        "Паста Bavette Barilla (Россия), 450г",
        "Паста Filini Barilla (Россия), 450г"
    ]

    # Фильтрация данных
    df = df[df['Product'].isin(allowed_products)]

    # Фильтр по году
    available_years = df['Year'].unique()
    selected_year = st.selectbox("Выберите год для анализа", sorted(available_years))
    df = df[df['Year'] == selected_year]

    # Выбор типа отчёта
    report_type = st.selectbox("Выберите тип отчёта", [
        "Итоговый отчёт по всей сети",
        "Топ-10 продуктов",
        "Рейтинги ресторанов"
    ])

    report_df = pd.DataFrame()

    if report_type == "Итоговый отчёт по всей сети":
        st.write("Сформируем сводный отчёт по столбцу 'Total' (общие продажи).")
        summary = df.groupby("Product")['Total'].sum().reset_index()
        summary['Total'] = summary['Total'].astype(int).apply(lambda x: f"{x:,}".replace(",", " "))
        summary = summary.sort_values("Total", ascending=False)
        st.dataframe(summary)
        report_df = summary

    elif report_type == "Топ-10 продуктов":
        st.write("Определим топ-10 продуктов по объёму продаж (Total).")
        product_sales = df.groupby("Product")['Total'].sum().sort_values(ascending=False).head(10)
        top10_df = product_sales.reset_index()
        top10_df['Total'] = top10_df['Total'].astype(int).apply(lambda x: f"{x:,}".replace(",", " "))
        st.dataframe(top10_df)
        report_df = top10_df

    elif report_type == "Рейтинги ресторанов":
        st.write("Покажем рейтинги ресторанов по продажам.")
        restaurant_cols = []
        for col in df.columns:
            if col not in {"Week", "Year", "Month", "Product", "Total", "SeasonFlag", "HolidayFlag", "Case kg"}:
                restaurant_cols.append(col)

        if restaurant_cols:
            rest_sums = df[restaurant_cols].sum().sort_values(ascending=False)
            rest_df = rest_sums.reset_index()
            rest_df.columns = ["Ресторан", "Продажи"]
            rest_df['Продажи'] = rest_df['Продажи'].astype(int).apply(lambda x: f"{x:,}".replace(",", " "))
            st.dataframe(rest_df)

            # График
            fig = px.bar(rest_df, x="Ресторан", y="Продажи", title="Рейтинги ресторанов по продажам")
            st.plotly_chart(fig)

            report_df = rest_df
        else:
            st.warning("Ресторанные столбцы не найдены. Рейтинг невозможен.")

    # Кнопка для экспорта отчёта в Excel
    if not report_df.empty:
        st.write("---")
        st.write("Скачать отчёт в Excel:")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            report_df.to_excel(writer, index=False, sheet_name="Отчёт")
        output.seek(0)  # Перемещение курсора в начало BytesIO
        excel_data = output.read()

        st.download_button(
            label="Скачать Excel",
            data=excel_data,
            file_name=f"report_{selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.info("Отчёт сгенерирован! Выберите тип отчёта и скачайте Excel-файл при необходимости.")
