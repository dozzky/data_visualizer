import streamlit as st
import pandas as pd
import plotly.express as px
import json
from pathlib import Path
import re

st.set_page_config(page_title="Аналитика путевых листов", layout="wide")
st.title("📊 Аналитика путевых листов")

# === Загрузка данных ===
uploaded_file = st.file_uploader("Загрузите JSON", type="json")

if uploaded_file is None:
    st.info("Загрузите JSON-файл с данными. Пример лежит в папке `data/example.json`.")
    example_path = Path("data/example.json")
    if example_path.exists():
        with open(example_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    else:
        st.stop()
else:
    data = json.load(uploaded_file)
    df = pd.DataFrame(data)

# === Парсинг даты из поля "Ссылка" ===
def extract_datetime(s: str):
    match = re.search(r"от (\d{2}\.\d{2}\.\d{4} \d{1,2}:\d{2}:\d{2})", s)
    if match:
        return pd.to_datetime(match.group(1), format="%d.%m.%Y %H:%M:%S", errors="coerce")
    return None

df["ДатаДокумента"] = df["Ссылка"].apply(extract_datetime)

# === Фильтры ===
with st.sidebar:
    st.header("Фильтры")
    selected_doc = st.multiselect("Документ (Ссылка)", df["Ссылка"].unique())
    selected_work = st.multiselect("Вид работ", df["ТехнологическиеОперацииВидРабот"].unique())
    selected_driver = st.multiselect("Водитель", df["Водитель"].unique())
    selected_equipment = st.multiselect("Оборудование", df["Оборудование"].unique())
    
    min_date, max_date = df["ДатаДокумента"].min(), df["ДатаДокумента"].max()
    date_range = st.date_input(
        "Период (Дата документа)",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

# Применяем фильтры
if selected_doc:
    df = df[df["Ссылка"].isin(selected_doc)]
if selected_work:
    df = df[df["ТехнологическиеОперацииВидРабот"].isin(selected_work)]
if selected_driver:
    df = df[df["Водитель"].isin(selected_driver)]
if selected_equipment:
    df = df[df["Оборудование"].isin(selected_equipment)]

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df = df[(df["ДатаДокумента"] >= start_date) & (df["ДатаДокумента"] <= end_date)]

if df.empty:
    st.warning("Нет данных по выбранным фильтрам.")
    st.stop()

# === KPI расчёты ===
df["KPI_л_на_тонну"] = df["РасходТоплива"] / df["ТехнологическиеОперацииКоличествоНоменклатурыВсего"]
df["KPI_л_на_100ткм"] = df["РасходТоплива"] / (df["ТехнологическиеОперацииГрузооборот"] / 100)
df["KPI_сред_тонн_на_операцию"] = df["ТехнологическиеОперацииКоличествоНоменклатурыВсего"] / df["ТехнологическиеОперацииКоличествоОперацийВсего"]
df["KPI_производительность_тн_в_час"] = df["ТехнологическиеОперацииКоличествоНоменклатурыВсего"] / df["ПоказателиОборудованияПоУчасткамПродолжительность"]

# === Справочник KPI ===
with st.expander("ℹ️ Справочник KPI"):
    st.markdown("""
    - **Удельный расход топлива, л/тн** = `РасходТоплива / ТехнологическиеОперацииКоличествоНоменклатурыВсего`  
    - **Удельный расход топлива, л/100ткм** = `РасходТоплива / (ТехнологическиеОперацииГрузооборот / 100)`  
    - **Среднее количество тонн на операцию** = `ТехнологическиеОперацииКоличествоНоменклатурыВсего / ТехнологическиеОперацииКоличествоОперацийВсего`  
    - **Производительность, тн/ч** = `ТехнологическиеОперацииКоличествоНоменклатурыВсего / ПоказателиОборудованияПоУчасткамПродолжительность`  
    """)

# === Основные KPI (средние значения) ===
st.subheader("📈 Производственные KPI")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Удельный расход топлива, л/тн", f"{df['KPI_л_на_тонну'].mean():.2f}")
col2.metric("Удельный расход топлива, л/100ткм", f"{df['KPI_л_на_100ткм'].mean():.2f}")
col3.metric("Средн. тонн на операцию", f"{df['KPI_сред_тонн_на_операцию'].mean():.2f}")
col4.metric("Производительность, тн/ч", f"{df['KPI_производительность_тн_в_час'].mean():.2f}")

with st.expander("📊 Подробности KPI по каждой записи"):
    st.dataframe(df[[
        "Ссылка", "Оборудование", "Водитель",
        "KPI_л_на_тонну", "KPI_л_на_100ткм",
        "KPI_сред_тонн_на_операцию", "KPI_производительность_тн_в_час"
    ]], use_container_width=True)

# === KPI по водителям (рейтинг) ===
st.subheader("👷 KPI по водителям")

df_driver = df.groupby("Водитель", as_index=False).agg({
    "KPI_л_на_тонну": "mean",
    "KPI_л_на_100ткм": "mean",
    "KPI_сред_тонн_на_операцию": "mean",
    "KPI_производительность_тн_в_час": "mean"
})

st.dataframe(df_driver, use_container_width=True)

fig_driver = px.bar(
    df_driver.sort_values("KPI_л_на_тонну"),
    x="Водитель",
    y="KPI_л_на_тонну",
    title="Рейтинг по удельному расходу топлива (л/тн)",
    labels={"KPI_л_на_тонну": "л/тн"},
)
st.plotly_chart(fig_driver, use_container_width=True)

# === KPI по маршрутам (УчастокРабот + УчастокРазгрузки) ===
st.subheader("🚛 KPI по маршрутам")

df["Маршрут"] = df["ТехнологическиеОперацииУчастокРабот"] + " → " + df["ТехнологическиеОперацииУчастокРазгрузки"]

df_route = df.groupby("Маршрут", as_index=False).agg({
    "KPI_л_на_тонну": "mean",
    "KPI_л_на_100ткм": "mean",
    "KPI_сред_тонн_на_операцию": "mean",
    "KPI_производительность_тн_в_час": "mean"
})

st.dataframe(df_route, use_container_width=True)

fig_route = px.bar(
    df_route.sort_values("KPI_л_на_100ткм"),
    x="Маршрут",
    y="KPI_л_на_100ткм",
    title="Рейтинг маршрутов по удельному расходу (л/100ткм)",
    labels={"KPI_л_на_100ткм": "л/100ткм"},
)
st.plotly_chart(fig_route, use_container_width=True)

# === Выбор параметров для анализа (графики) ===
st.subheader("📊 Визуализация данных")

numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
if not numeric_cols:
    st.error("В данных нет числовых параметров для построения графиков.")
    st.stop()

graph_type = st.radio("Тип графика", ["Scatter (точки)", "Line (линия)"], horizontal=True)

if graph_type == "Scatter (точки)":
    col1, col2 = st.columns(2)
    with col1:
        x_param = st.selectbox("Ось X", numeric_cols, index=0)
    with col2:
        y_param = st.selectbox("Ось Y", numeric_cols, index=min(1, len(numeric_cols)-1))

    highlight_cols = [
        "ТехнологическиеОперацииГрузооборот",
        "ТехнологическиеОперацииКоличествоОперацийВсего",
        "ТехнологическиеОперацииКоличествоНоменклатурыВсего",
        "ПоказателиОборудованияПоУчасткамПродолжительность",
    ]

    if y_param in highlight_cols or x_param in highlight_cols:
        fig = px.scatter(
            df,
            x=x_param,
            y=y_param,
            color="ТехнологическиеОперацииВидРабот",
            hover_data=["Ссылка", "Оборудование", "Водитель"]
        )
    else:
        fig = px.scatter(
            df,
            x=x_param,
            y=y_param,
            hover_data=["Ссылка", "Оборудование", "Водитель"]
        )

elif graph_type == "Line (линия)":
    y_param = st.selectbox("Параметр по оси Y", numeric_cols, index=0)
    group_by = st.selectbox("Группировать по", ["Нет", "ТехнологическиеОперацииВидРабот", "Оборудование", "Водитель"])

    if group_by == "Нет":
        fig = px.line(
            df.sort_values("ДатаДокумента"),
            x="ДатаДокумента",
            y=y_param,
            markers=True,
            hover_data=["Ссылка", "Оборудование", "Водитель"]
        )
    else:
        fig = px.line(
            df.sort_values("ДатаДокумента"),
            x="ДатаДокумента",
            y=y_param,
            color=group_by,
            markers=True,
            hover_data=["Ссылка", "Оборудование", "Водитель"]
        )

st.plotly_chart(fig, use_container_width=True)

# === Таблица данных ===
with st.expander("Показать данные"):
    st.dataframe(df, use_container_width=True)
