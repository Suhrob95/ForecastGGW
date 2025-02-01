import streamlit as st
import pandas as pd
import datetime
import io
from prophet import Prophet
from joblib import Parallel, delayed

# Список ресторанов
RESTAURANT_LIST = [
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


@st.cache_data
def preprocess_data(df: pd.DataFrame) -> pd.DataFrame | None:
    required_cols = {"Year", "Week", "Total", "Product"}
    if not required_cols.issubset(df.columns):
        st.error(f"Необходимые столбцы {required_cols} отсутствуют: {required_cols - set(df.columns)}")
        return None

    def year_week_to_date(y: int, w: int) -> datetime.date | None:
        try:
            return datetime.datetime.strptime(f"{y}-W{w}-1", "%G-W%V-%u").date()
        except ValueError:
            st.error(f"Некорректный формат года/недели: {y}, {w}")
            return None

    if "Date" not in df.columns:
        df["Date"] = df.apply(lambda row: year_week_to_date(int(row["Year"]), int(row["Week"])), axis=1)
        if df["Date"].isnull().any():
            st.error("Ошибки при преобразовании года/недели в дату. Проверьте данные.")
            return None
    else:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        if df["Date"].isnull().any():
            st.error("Некорректные даты в столбце 'Date'.")
            return None

    restaurant_cols_present = [col for col in RESTAURANT_LIST if
                               col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    if not restaurant_cols_present:
        st.warning("В данных отсутствуют числовые столбцы для указанных ресторанов.")

    df_agg = df.groupby(["Date", "Product"], as_index=False)["Total"].sum()

    agg_dict_rest = {}
    for rcol in restaurant_cols_present:
        if pd.api.types.is_numeric_dtype(df[rcol]):
            agg_dict_rest[rcol] = "sum"

    if agg_dict_rest:
        df_rest = df.groupby(["Date", "Product"], as_index=False).agg(agg_dict_rest)
        df_agg = pd.merge(df_agg, df_rest, on=["Date", "Product"], how="left")

    if "Case kg" in df_agg.columns:
        df_agg.drop(columns=["Case kg"], inplace=True)

    return df_agg


def forecast_prophet(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    df = df.rename(columns={"Date": "ds", "Total": "y"})
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=horizon, freq="W")
    forecast = model.predict(future)
    forecast = forecast[["ds", "yhat"]].rename(columns={"ds": "Date", "yhat": "Прогноз"})
    forecast["Прогноз"] = forecast["Прогноз"].round().astype(int)
    return forecast


def build_forecast(df: pd.DataFrame):
    today = datetime.date.today()
    st.info(f"Сегодняшняя дата: {today}. Прогнозируем недели после текущей.")

    st.subheader("Прогноз спроса на продукцию и рестораны")

    df = preprocess_data(df)
    if df is None or df.empty:
        st.error("Данные не прошли проверку или пусты.")
        return

    st.markdown("### Прогноз по конкретному продукту и ресторану")

    products = sorted(df["Product"].unique().tolist())
    sel_product = st.selectbox("Выберите продукт", products, key="sel_product")

    rest_cols_present = [c for c in RESTAURANT_LIST if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
    sel_restaurant = st.selectbox("Выберите ресторан", ["Суммарно"] + rest_cols_present, key="sel_restaurant")

    horizon_pr = st.slider("Горизонт (недель) [продукт+ресторан]", 1, 4, 2, key="horizon_pr")

    df_prod = df[df["Product"] == sel_product].copy()
    if df_prod.empty:
        st.warning("Нет строк с выбранным продуктом.")
        return

    if sel_restaurant == "Суммарно":
        df_prod["Sales"] = df_prod["Total"]
    else:
        df_prod["Sales"] = df_prod[sel_restaurant]

    df_prod_agg = df_prod.groupby("Date")["Sales"].sum().reset_index()
    if df_prod_agg.empty:
        st.warning("Нет данных для выбранного продукта и ресторана.")
        return

    df_prod_agg = df_prod_agg.rename(columns={"Date": "ds", "Sales": "y"})
    forecast_pr = forecast_prophet(df_prod_agg, horizon_pr)

    # Plot the forecast
    st.write(f"Прогноз для продукта '{sel_product}' и ресторана '{sel_restaurant}' на {horizon_pr} недель:")
    st.line_chart(forecast_pr.set_index("Date")["Прогноз"])

    # Sum the forecast over the selected horizon weeks and round to integer
    sum_forecast = int(forecast_pr['Прогноз'].sum())

    # Display the sum in a table with space-separated numbers
    st.write(pd.DataFrame({'Прогноз': [f"{sum_forecast:,}".replace(',', ' ')]}))
    st.success("Прогноз успешно построен!")
    st.markdown("---")

    st.markdown("## Прогноз по всем ресторанам (с суммированием по продуктам)")

    horizon_all_rest_prod = st.slider("Горизонт (недель) [Все рестораны и продукты]", 1, 4, 2,
                                      key="horizon_all_rest_prod")

    numeric_rest_cols = [c for c in RESTAURANT_LIST if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]

    if not numeric_rest_cols:
        st.warning("В данных отсутствуют числовые столбцы для ресторанов.")
        return

    if st.button("Сформировать прогноз по всем ресторанам (с суммированием)"):
        all_rest_prod_forecast = []
        with st.spinner("Выполняется прогнозирование (все рестораны и продукты)..."):
            for rest_ in numeric_rest_cols:
                dtemp = df.groupby(["Date", "Product"])[rest_].sum().reset_index()
                for prod_ in df["Product"].unique():
                    dtemp_prod = dtemp[dtemp["Product"] == prod_].copy()
                    if dtemp_prod.empty:
                        continue

                    dtemp_prod = dtemp_prod.rename(columns={"Date": "ds", rest_: "y"})
                    model = Prophet()
                    model.fit(dtemp_prod[["ds", "y"]])
                    future = model.make_future_dataframe(periods=horizon_all_rest_prod, freq="W")
                    forecast = model.predict(future)
                    forecast = forecast[["ds", "yhat"]].rename(columns={"ds": "Дата", "yhat": "Прогноз"})
                    forecast["Ресторан"] = rest_
                    forecast["Продукт"] = prod_
                    all_rest_prod_forecast.append(forecast)

        if all_rest_prod_forecast:
            df_all_rest_prod_forecast = pd.concat(all_rest_prod_forecast)

            # Sum the forecast over the selected horizon weeks for each restaurant and product
            df_all_rest_prod_forecast_agg = df_all_rest_prod_forecast.groupby(["Ресторан", "Продукт"])[
                "Прогноз"].sum().reset_index()
            df_all_rest_prod_forecast_agg["Прогноз"] = df_all_rest_prod_forecast_agg["Прогноз"].round().astype(int)

            # Pivot the table
            df_pivot = df_all_rest_prod_forecast_agg.pivot(index="Продукт", columns="Ресторан",
                                                           values="Прогноз").fillna(0)
            df_pivot = df_pivot.astype(int)
            df_pivot.reset_index(inplace=True)
            df_pivot.columns.name = None  # Remove the column hierarchy name

            st.markdown("### Таблица прогноза по продуктам и ресторанам")
            st.dataframe(df_pivot)

            # Download button for the pivot table
            buf = io.BytesIO()
            df_pivot.to_excel(buf, index=False, engine="xlsxwriter")
            buf.seek(0)
            st.download_button(
                label="Скачать таблицу в Excel",
                data=buf,
                file_name="forecast_table.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Display the aggregated forecast dataframe
            st.markdown("### Результат прогноза по всем ресторанам (с суммированием по продуктам)")
            st.dataframe(df_all_rest_prod_forecast_agg)

            # Download button for the aggregated forecast
            buf_all_rest_prod = io.BytesIO()
            with pd.ExcelWriter(buf_all_rest_prod, engine="xlsxwriter") as writer:
                df_all_rest_prod_forecast_agg.to_excel(writer, index=False, sheet_name="Forecast")

            st.download_button(
                "Скачать общий прогноз по ресторанам (с суммированием по продуктам) в Excel",
                data=buf_all_rest_prod,
                file_name="all_restaurants_products_forecast.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Нет данных для прогноза по ресторанам и продуктам.")


if __name__ == "__main__":
    st.set_page_config(page_title="Прогноз продаж", layout="wide")
    st.title("Прогнозирование продаж")

    uploaded_file = st.file_uploader("Загрузите файл Excel (xls, xlsx)", type=["xls", "xlsx"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            required_cols = {"Year", "Week", "Total", "Product"}
            if not required_cols.issubset(df.columns):
                st.error(f"Необходимые столбцы {required_cols} отсутствуют в загруженном файле.")
            else:
                build_forecast(df)
        except Exception as e:
            st.error(f"Произошла ошибка: {e}")
    else:
        st.info("Загрузите файл Excel для прогнозирования.")
