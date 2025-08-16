import streamlit as st
from plotly import express as px
from data_processing import Process_data


def print_dataframe():
    df, describe = st.columns(2)

    with df:
        st.markdown(":spiral_note_pad: Click over Top right of dataframe on Fullscreen to open whole dataset.")
        st.markdown(":arrow_down_small: Click on any column name to sort data.")
        st.dataframe(data_obj.get_df(), height=400)

    with describe:
        st.markdown("📇This table describes mean, SD and 5 number summary of data.")
        st.markdown("🔢Only Numeric Columns.")
        st.dataframe(data_obj.describe_data().iloc[1:, :].round(2))


def plot_bar_graph(x_label, y_label, barmode):
    res_data = data_obj.get_bar_data()
    col1 = st.container(border=True)
    fig = px.bar(res_data, x=res_data[x_label], y=res_data[y_label], barmode=barmode)
    mean_val = data_obj.get_mean(y_label)
    if mean_val is not None:
        fig.add_hline(y=mean_val, line_dash="dash", line_color="grey", annotation_text="mean", annotation={"font_size":20})
    col1.plotly_chart(fig)


def plot_scatter_graph(x_label, y_label, color_col):
    res_data = data_obj.get_bar_data()
    col1 = st.container(border=True)
    col1.plotly_chart(px.scatter(res_data, x=res_data[x_label], y=res_data[y_label], color=color_col))


def plot_hist_graph(x_label, color_col):
    res_data = data_obj.get_bar_data()
    col1 = st.container(border=True)
    col1.plotly_chart(px.histogram(res_data, x=res_data[x_label], color=color_col))


def plot_line_graph(x_label, y_label):
    res_data = data_obj.get_bar_data()
    col1 = st.container(border=True)
    fig = px.line(res_data, x=res_data[x_label], y=res_data[y_label])
    mean_val = data_obj.get_mean(y_label)
    if mean_val is not None:
        fig.add_hline(y=mean_val, line_dash="dash", line_color="grey", annotation_text="mean", annotation={"font_size":20})
    col1.plotly_chart(fig)


def plot_pie_chart(val_col, name_col):
    res_data = data_obj.get_df()
    col1 = st.container(border=True)
    fig = px.pie(res_data, values=res_data[val_col], names=res_data[name_col])
    fig.update_traces(textinfo="label+percent")
    col1.plotly_chart(fig)


def plot_box(x_label, y_label, color_col):
    res_data = data_obj.get_bar_data()
    col1 = st.container(border=True)
    col1.plotly_chart(px.box(res_data, x=res_data[x_label], y=res_data[y_label], color=color_col))


st.set_page_config(page_title="Data Visualizer", page_icon=":bar_chart:", layout="wide")
title, documentation = st.columns(2)
st.title(":bar_chart: Data Visualizer")

# if st.sidebar.button("User Guide", use_container_width=True):
#     # webbrowser.open("https://google.com")
file = st.sidebar.file_uploader(label="Open CSV file", type="csv", label_visibility="collapsed")

if file:
    data_obj = Process_data(file)
    btn_df = st.sidebar.button("Show Dataframe")
    if btn_df:
        print_dataframe()
    graphs_charts = ["Histogram", "Bar graph", "Scatter", "Pie Chart", "Line chart", "Box Plot"]
    chosen_graph = st.sidebar.selectbox(label="Choose Task", options=graphs_charts)
    columns = data_obj.get_columns()
    numeric_columns = data_obj.get_numeric_columns()

    if chosen_graph == "Histogram":
        x_label = st.sidebar.selectbox("Select X-axis (Numeric column only):", options=numeric_columns)
        columns.insert(0, None)
        color_col = st.sidebar.selectbox("Color differentiation based on column:", options=columns)
        btn_clicked = st.sidebar.button("Generate Graph")

        if btn_clicked:
            plot_hist_graph(x_label, color_col)

    elif chosen_graph == "Bar graph":
        x_label = st.sidebar.selectbox("Select X-axis (Categorical column Preferred)", options=columns)
        columns.remove(x_label)
        y_label = st.sidebar.selectbox("Select Y-axis (Numeric Column only)", options=numeric_columns)
        barmode = st.sidebar.selectbox("Bar Type:", options=["overlay", "group", "relative"])
        btn_clicked = st.sidebar.button("Generate Graph")

        if btn_clicked:
            plot_bar_graph(x_label, y_label, barmode)

    elif chosen_graph == "Scatter":
        x_label = st.sidebar.selectbox("Select X-axis (Numeric column only)", options=numeric_columns)
        # ensure y comes from numeric columns different from x
        y_options = [c for c in numeric_columns if c != x_label]
        y_label = st.sidebar.selectbox("Select Y-axis (Numeric Column only)", options=y_options)
        color_options = data_obj.get_columns()
        color_options.insert(0, None)
        color_col = st.sidebar.selectbox("Color differentiation based on column:", options=color_options)
        btn_clicked = st.sidebar.button("Generate Graph")

        if btn_clicked:
            plot_scatter_graph(x_label, y_label, color_col)

    elif chosen_graph == "Pie Chart":
        val_col = st.sidebar.selectbox("Select Value Column (Numeric):", options=numeric_columns)
        name_col = st.sidebar.selectbox("Select Name Column (Categorical):", options=columns)
        btn_clicked = st.sidebar.button("Generate Chart")

        if btn_clicked:
            plot_pie_chart(val_col, name_col)

    elif chosen_graph == "Line chart":
        x_label = st.sidebar.selectbox("Select X-axis (Time series/categorical only)", options=columns)
        columns.remove(x_label)
        y_label = st.sidebar.selectbox("Select Y-axis (Numeric Column only)", options=numeric_columns)
        btn_clicked = st.sidebar.button("Generate Chart")

        if btn_clicked:
            plot_line_graph(x_label, y_label)

    elif chosen_graph == "Box Plot":
        x_label = st.sidebar.selectbox("Select X-axis (Categorical column Preferred)", options=columns)
        columns.remove(x_label)
        y_label = st.sidebar.selectbox("Select Y-axis (Numeric Column only)", options=numeric_columns)
        color_options = data_obj.get_columns()
        color_options.insert(0, None)
        color_col = st.sidebar.selectbox("Color differentiation based on column:", options=color_options)
        btn_clicked = st.sidebar.button("Generate Graph")

        if btn_clicked:
            plot_box(x_label, y_label, color_col)