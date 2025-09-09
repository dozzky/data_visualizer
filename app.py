import streamlit as st
import pandas as pd
import plotly.express as px
import json
from pathlib import Path

st.set_page_config(page_title="Аналитика путевых листов", layout="wide")
st.title("📊 Аналитика путевых листов")

#Загрузка данных
uploaded_file = st.file_uploader("Загрузите JSON", type="json")

if uploaded_file is None:
    st.info("Загрузите JSON-файл с данными.")
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

#Фильтры
with st.sidebar:
    st.header("Фильтры")
    selected_doc = st.multiselect("Документ (Ссылка)", df["Ссылка"].unique())
    selected_work = st.multiselect("Вид работ", df["ТехнологическиеОперацииВидРабот"].unique())
    selected_driver = st.multiselect("Водитель", df["Водитель"].unique())
    selected_equipment = st.multiselect("Оборудование", df["Оборудование"].unique())

if selected_doc:
    df = df[df["Ссылка"].isin(selected_doc)]
if selected_work:
    df = df[df["ТехнологическиеОперацииВидРабот"].isin(selected_work)]
if selected_driver:
    df = df[df["Водитель"].isin(selected_driver)]
if selected_equipment:
    df = df[df["Оборудование"].isin(selected_equipment)]

if df.empty:
    st.warning("Нет данных по выбранным фильтрам.")
    st.stop()

# === Выбор параметров для анализа ===
numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
if not numeric_cols:
    st.error("В данных нет числовых параметров для построения графиков.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    x_param = st.selectbox("Ось X", numeric_cols, index=0)
with col2:
    y_param = st.selectbox("Ось Y", numeric_cols, index=min(1, len(numeric_cols)-1))

#Построение графика
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

st.plotly_chart(fig, use_container_width=True)

#Таблица данных
with st.expander("Показать данные"):
    st.dataframe(df, use_container_width=True)
