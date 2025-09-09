import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.title("📊 Аналитика путевых листов")

# Загрузка файла
uploaded_file = st.file_uploader("Загрузите JSON", type="json")
if uploaded_file:
    data = json.load(uploaded_file)
    df = pd.DataFrame(data)

    # Категориальные фильтры
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_doc = st.multiselect("Документ (Ссылка)", df["Ссылка"].unique())
    with col2:
        selected_work = st.multiselect("Вид работ", df["ТехнологическиеОперацииВидРабот"].unique())
    with col3:
        selected_driver = st.multiselect("Водитель", df["Водитель"].unique())

    # Применяем фильтры
    if selected_doc:
        df = df[df["Ссылка"].isin(selected_doc)]
    if selected_work:
        df = df[df["ТехнологическиеОперацииВидРабот"].isin(selected_work)]
    if selected_driver:
        df = df[df["Водитель"].isin(selected_driver)]

    # Числовые параметры
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    x_param = st.selectbox("Ось X", numeric_cols)
    y_param = st.selectbox("Ось Y", numeric_cols)

    # Особая логика
    if y_param in [
        "ТехнологическиеОперацииГрузооборот",
        "ТехнологическиеОперацииКоличествоОперацийВсего",
        "ТехнологическиеОперацииКоличествоНоменклатурыВсего",
        "ПоказателиОборудованияПоУчасткамПродолжительность",
    ]:
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
