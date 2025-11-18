import streamlit as st
import pandas as pd
import math
import os

st.set_page_config(page_title="CSV Viewer", layout="wide")
st.title("CSV Viewer & Search")

if "df" not in st.session_state:
    st.session_state.df = None
if "filename" not in st.session_state:
    st.session_state.filename = None

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@st.cache_data(show_spinner=True)
def load_csv(path) -> pd.DataFrame:
    encodings_to_try = [
        "utf-8",
        "utf-8-sig",
        "cp1251",
        "latin1",
        "iso-8859-1"
    ]
    
    for enc in encodings_to_try:
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except Exception:
            pass
    
    st.error("Не удалось открыть CSV файл. Неизвестная кодировка.")
    return None

st.sidebar.header("Загрузка CSV")
uploaded_file = st.sidebar.file_uploader("Выберите CSV файл", type=["csv"])

if uploaded_file is not None:
    if st.session_state.filename != uploaded_file.name:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.filename = uploaded_file.name
        st.session_state.df = load_csv(file_path)

df = st.session_state.df

if df is None:
    st.info("Загрузите CSV файл слева, чтобы начать работу.")
else:
    st.success(f"Файл загружен: **{st.session_state.filename}**")
    st.write(f"Строк: {len(df):,}  |  Столбцов: {len(df.columns)}")

    st.subheader("Поиск и фильтрация")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        search_column = st.selectbox(
            "Столбец для поиска",
            options=["<по всем строкам>"] + list(df.columns),
            index=0,
        )

    with col2:
        query = st.text_input("Строка для поиска (подстрока, регистр не важен)")

    with col3:
        page_size = st.number_input(
            "Строк на страницу",
            min_value=10,
            max_value=10_000,
            value=100,
            step=10,
        )

    filtered_df = df

    if query:
        q = query.strip()
        if q:
            if search_column == "<по всем строкам>":
                mask = df.apply(
                    lambda row: q.lower() in " ".join(row.astype(str)).lower(),
                    axis=1,
                )
                filtered_df = df[mask]
            else:
                mask = df[search_column].astype(str).str.contains(
                    q, case=False, na=False
                )
                filtered_df = df[mask]

    st.write(f"Найдено строк: {len(filtered_df):,}")

    if len(filtered_df) == 0:
        st.warning("Нет строк, удовлетворяющих фильтру.")
    else:
        total_pages = math.ceil(len(filtered_df) / page_size)

        page = st.number_input(
            "Страница",
            min_value=1,
            max_value=max(total_pages, 1),
            value=1,
            step=1,
        )

        start = (page - 1) * page_size
        end = start + page_size

        st.caption(f"Показаны строки {start + 1}–{min(end, len(filtered_df))}")

        page_df = filtered_df.iloc[start:end]

        st.dataframe(page_df, use_container_width=True, hide_index=False)

        csv_page = page_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Скачать текущую страницу в CSV",
            csv_page,
            file_name=f"page_{page}.csv",
            mime="text/csv",
        )
