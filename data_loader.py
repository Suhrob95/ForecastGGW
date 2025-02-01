import streamlit as st
import pandas as pd


def load_excel_files():
    """
    Функция для загрузки Excel-файлов через Streamlit.
    Возвращает объединённый DataFrame или None, если файлы не выбраны
    или при возникновении ошибки структуры данных.
    """
    uploaded_files = st.file_uploader(
        "Загрузите один или несколько Excel-файлов",
        accept_multiple_files=True,
        type=["xlsx", "xls"]
    )

    if not uploaded_files:
        return None

    required_columns = ["Year", "Week", "Month", "Product", "Total"]
    combined_df = pd.DataFrame()

    month_mapping = {
        "январь": 1, "февраль": 2, "март": 3, "апрель": 4,
        "май": 5, "июнь": 6, "июль": 7, "август": 8,
        "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }

    for file in uploaded_files:
        try:
            df_temp = pd.read_excel(file)
            if df_temp.empty:
                st.error(f"Файл {file.name} пустой или не содержит данных.")
                continue
        except Exception as e:
            st.error(f"Ошибка чтения файла {file.name}: {str(e)}")
            continue

        missing_cols = [col for col in required_columns if col not in df_temp.columns]
        if missing_cols:
            st.error(f"Файл {file.name} не содержит столбцов: {missing_cols}")
            continue

        try:
            df_temp["Year"] = pd.to_numeric(df_temp["Year"], errors="coerce", downcast="integer")
            df_temp["Month"] = df_temp["Month"].str.strip().map(month_mapping)
            df_temp["Week"] = pd.to_numeric(df_temp["Week"], errors="coerce", downcast="integer")
            df_temp["Total"] = pd.to_numeric(df_temp["Total"], errors="coerce")
        except Exception as e:
            st.error(f"Ошибка преобразования столбцов в файле {file.name}: {str(e)}")
            continue

        if df_temp[required_columns].isnull().any().any():
            st.warning(f"Удалены строки с пропусками в файле {file.name}.")
            df_temp = df_temp.dropna(subset=required_columns)

        combined_df = pd.concat([combined_df, df_temp], ignore_index=True)

    if combined_df.empty:
        st.warning("Обработанные данные пусты.")
        return None

    if combined_df.duplicated(subset=["Year", "Week", "Product"]).any():
        st.warning("Удалены дубликаты.")
        combined_df.drop_duplicates(subset=["Year", "Week", "Product"], inplace=True)

    zero_total_ratio = (combined_df["Total"] <= 0).mean()
    if zero_total_ratio > 0.5:
        st.warning(f"Более 50% значений 'Total' некорректны. Проверьте данные.")
        return None

    st.success("Файлы успешно загружены и обработаны!")
    return combined_df
