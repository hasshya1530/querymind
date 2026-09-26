import io
import tempfile
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from core.query_executor import execute_safe_query
from core.result_explainer import explain_results
from core.schema_discovery import format_schema, get_database_schema
from core.sql_generator import generate_sql
from database.connection import get_connection, load_csv, load_excel
from utils.helpers import results_to_dataframe

# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="QueryMind",
    page_icon="⌕",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "query_results" not in st.session_state:
    st.session_state.query_results = None

if "generated_sql" not in st.session_state:
    st.session_state.generated_sql = None

if "question" not in st.session_state:
    st.session_state.question = None

if "database_path" not in st.session_state:
    st.session_state.database_path = None

if "data_source" not in st.session_state:
    st.session_state.data_source = "Demo Database"

if "explanation" not in st.session_state:
    st.session_state.explanation = None

if "query_error" not in st.session_state:
    st.session_state.query_error = None


# --------------------------------------------------
# Uploaded data handling
# --------------------------------------------------


def get_uploaded_database(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()

    temp_directory = tempfile.mkdtemp()

    database_path = Path(temp_directory) / "uploaded.db"

    if suffix == ".csv":
        csv_path = Path(temp_directory) / uploaded_file.name

        with open(csv_path, "wb") as file:
            file.write(uploaded_file.getbuffer())

        table_name = Path(uploaded_file.name).stem.strip().replace(" ", "_")

        load_csv(
            csv_path,
            table_name,
            database_path,
        )

    if suffix in {".xlsx", ".xls"}:
        excel_path = Path(temp_directory) / uploaded_file.name

        with open(excel_path, "wb") as file:
            file.write(uploaded_file.getbuffer())

        load_excel(
            excel_path,
            database_path,
        )

    if suffix in {
        ".db",
        ".sqlite",
        ".sqlite3",
    }:
        database_path.write_bytes(uploaded_file.getbuffer())

    if suffix not in {
        ".csv",
        ".xlsx",
        ".xls",
        ".db",
        ".sqlite",
        ".sqlite3",
    }:
        raise ValueError(
            "Unsupported file type. Please upload CSV, Excel, or SQLite database files."
        )

    return database_path


# --------------------------------------------------
# Schema discovery for uploaded databases
# --------------------------------------------------


def get_schema_for_database(database_path):
    connection = get_connection(database_path)

    try:
        cursor = connection.cursor()

        tables = cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        schema = {}

        for (table_name,) in tables:
            columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()

            schema[table_name] = [
                {
                    "name": column[1],
                    "type": column[2],
                    "primary_key": bool(column[5]),
                }
                for column in columns
            ]

        return schema

    finally:
        connection.close()


# --------------------------------------------------
# Chart utilities
# --------------------------------------------------

CHART_TYPES = [
    "Bar",
    "Line",
    "Pie",
    "Scatter",
    "Grouped Bar",
]


def get_numeric_columns(dataframe):
    return dataframe.select_dtypes(include="number").columns.tolist()


def get_categorical_columns(dataframe):
    numeric_columns = get_numeric_columns(dataframe)

    return [column for column in dataframe.columns if column not in numeric_columns]


def get_date_columns(dataframe):
    date_columns = []

    for column in dataframe.columns:
        if pd.api.types.is_datetime64_any_dtype(dataframe[column]):
            date_columns.append(column)
            continue

        if not pd.api.types.is_object_dtype(dataframe[column]):
            continue

        converted = pd.to_datetime(
            dataframe[column],
            errors="coerce",
        )

        if not dataframe[column].empty and converted.notna().mean() >= 0.8:
            date_columns.append(column)

    return date_columns


# --------------------------------------------------
# Bar chart
# --------------------------------------------------


def create_bar_chart(dataframe):
    numeric_columns = get_numeric_columns(dataframe)

    categorical_columns = get_categorical_columns(dataframe)

    if not numeric_columns:
        return None

    y_column = numeric_columns[0]

    if categorical_columns:
        x_column = categorical_columns[0]

    else:
        x_column = dataframe.columns[0]

    figure, axis = plt.subplots(figsize=(10, 5))

    axis.bar(
        dataframe[x_column].astype(str),
        dataframe[y_column],
    )

    axis.set_title(f"{y_column} by {x_column}")

    axis.set_xlabel(x_column)
    axis.set_ylabel(y_column)

    axis.tick_params(
        axis="x",
        rotation=45,
    )

    figure.tight_layout()

    return figure


# --------------------------------------------------
# Line chart
# --------------------------------------------------


def create_line_chart(dataframe):
    numeric_columns = get_numeric_columns(dataframe)

    date_columns = get_date_columns(dataframe)

    if not numeric_columns:
        return None

    y_column = numeric_columns[0]

    if date_columns:
        x_column = date_columns[0]

        plot_data = dataframe.copy()

        plot_data[x_column] = pd.to_datetime(
            plot_data[x_column],
            errors="coerce",
        )

        plot_data = plot_data.dropna(
            subset=[
                x_column,
                y_column,
            ]
        )

        plot_data = plot_data.sort_values(by=x_column)

        x_values = plot_data[x_column]

    else:
        categorical_columns = get_categorical_columns(dataframe)

        if categorical_columns:
            x_column = categorical_columns[0]
            x_values = dataframe[x_column].astype(str)

        else:
            x_column = "Row"
            x_values = range(
                1,
                len(dataframe) + 1,
            )

        plot_data = dataframe

    figure, axis = plt.subplots(figsize=(10, 5))

    axis.plot(
        x_values,
        plot_data[y_column],
        marker="o",
    )

    axis.set_title(f"{y_column} over {x_column}")

    axis.set_xlabel(x_column)
    axis.set_ylabel(y_column)

    axis.tick_params(
        axis="x",
        rotation=45,
    )

    figure.tight_layout()

    return figure


# --------------------------------------------------
# Pie chart
# --------------------------------------------------


def create_pie_chart(dataframe):
    numeric_columns = get_numeric_columns(dataframe)

    categorical_columns = get_categorical_columns(dataframe)

    if not numeric_columns:
        return None

    value_column = numeric_columns[0]

    if categorical_columns:
        label_column = categorical_columns[0]

        labels = dataframe[label_column].astype(str)

        values = dataframe[value_column]

    else:
        labels = [f"Row {index + 1}" for index in range(len(dataframe))]

        values = dataframe[value_column]

    figure, axis = plt.subplots(figsize=(8, 6))

    axis.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
    )

    axis.set_title(f"{value_column} distribution")

    figure.tight_layout()

    return figure


# --------------------------------------------------
# Scatter chart
# --------------------------------------------------


def create_scatter_chart(dataframe):
    numeric_columns = get_numeric_columns(dataframe)

    if len(numeric_columns) >= 2:
        x_column = numeric_columns[0]
        y_column = numeric_columns[1]

        x_values = dataframe[x_column]

    elif len(numeric_columns) == 1:
        x_column = "Row"
        y_column = numeric_columns[0]

        x_values = range(
            1,
            len(dataframe) + 1,
        )

    else:
        return None

    figure, axis = plt.subplots(figsize=(10, 5))

    axis.scatter(
        x_values,
        dataframe[y_column],
    )

    axis.set_title(f"{y_column} vs {x_column}")

    axis.set_xlabel(x_column)
    axis.set_ylabel(y_column)

    figure.tight_layout()

    return figure


# --------------------------------------------------
# Grouped bar chart
# --------------------------------------------------


def create_grouped_bar_chart(dataframe):
    numeric_columns = get_numeric_columns(dataframe)

    if not numeric_columns:
        return None

    categorical_columns = get_categorical_columns(dataframe)

    if categorical_columns:
        x_column = categorical_columns[0]

        labels = dataframe[x_column].astype(str)

    else:
        x_column = "Row"

        labels = [str(index + 1) for index in range(len(dataframe))]

    figure, axis = plt.subplots(figsize=(11, 5))

    positions = list(range(len(dataframe)))

    number_of_metrics = len(numeric_columns)

    width = 0.8 / number_of_metrics

    for index, column in enumerate(numeric_columns):
        offset = (index - (number_of_metrics - 1) / 2) * width

        bar_positions = [position + offset for position in positions]

        axis.bar(
            bar_positions,
            dataframe[column],
            width=width,
            label=column,
        )

    axis.set_title(f"Metrics by {x_column}")

    axis.set_xlabel(x_column)
    axis.set_ylabel("Value")

    axis.set_xticks(positions)

    axis.set_xticklabels(
        labels,
        rotation=45,
        ha="right",
    )

    axis.legend()

    figure.tight_layout()

    return figure


# --------------------------------------------------
# Chart dispatcher
# --------------------------------------------------


def create_chart(
    dataframe,
    chart_type,
):
    if chart_type == "Bar":
        return create_bar_chart(dataframe)

    if chart_type == "Line":
        return create_line_chart(dataframe)

    if chart_type == "Pie":
        return create_pie_chart(dataframe)

    if chart_type == "Scatter":
        return create_scatter_chart(dataframe)

    if chart_type == "Grouped Bar":
        return create_grouped_bar_chart(dataframe)

    return None


# --------------------------------------------------
# Convert figure to PNG
# --------------------------------------------------


def figure_to_png(figure):
    image_buffer = io.BytesIO()

    figure.savefig(
        image_buffer,
        format="png",
        dpi=150,
        bbox_inches="tight",
    )

    image_buffer.seek(0)

    return image_buffer.getvalue()


# --------------------------------------------------
# Create ZIP containing all five charts
# --------------------------------------------------


def create_all_charts_zip(dataframe):
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as zip_file:
        for chart_type in CHART_TYPES:
            figure = create_chart(
                dataframe,
                chart_type,
            )

            if figure is None:
                continue

            image_bytes = figure_to_png(figure)

            filename = chart_type.lower().replace(" ", "_") + ".png"

            zip_file.writestr(
                filename,
                image_bytes,
            )

            plt.close(figure)

    zip_buffer.seek(0)

    return zip_buffer.getvalue()


# --------------------------------------------------
# Visualization
# --------------------------------------------------


def show_visualization(dataframe, result_index):
    st.markdown("### Visualization")

    chart_type = st.radio(
        "Chart type",
        CHART_TYPES,
        horizontal=True,
        key=f"chart_type_{result_index}",
        label_visibility="collapsed",
    )

    figure = create_chart(
        dataframe,
        chart_type,
    )

    if figure is None:
        st.info(f"{chart_type} cannot be generated from this result.")
        return

    image_bytes = figure_to_png(figure)

    st.pyplot(
        figure,
        use_container_width=True,
    )

    plt.close(figure)

    st.download_button(
        "Download Current Chart",
        data=image_bytes,
        file_name=(
            "querymind_"
            + chart_type.lower().replace(
                " ",
                "_",
            )
            + ".png"
        ),
        mime="image/png",
        use_container_width=True,
        key=(f"download_current_{result_index}"),
    )

    st.markdown("#### Save all 5 charts")

    all_charts_zip = create_all_charts_zip(dataframe)

    st.download_button(
        "Download All 5 Charts",
        data=all_charts_zip,
        file_name="querymind_all_5_charts.zip",
        mime="application/zip",
        use_container_width=True,
        key=(f"download_all_{result_index}"),
    )


# --------------------------------------------------
# Main application
# --------------------------------------------------


def main():

    st.title("QueryMind")

    st.markdown("### Ask questions. Query data. Discover insights.")

    st.caption("Natural Language → SQL → Results → Visualization")

    st.divider()

    # --------------------------------------------------
    # Data source
    # --------------------------------------------------

    st.markdown("## Choose your data")

    data_source = st.radio(
        "Data source",
        [
            "Demo Database",
            "Upload Your Data",
        ],
        horizontal=True,
        key="data_source_selector",
        label_visibility="collapsed",
    )

    # --------------------------------------------------
    # Demo database
    # --------------------------------------------------

    if data_source == "Demo Database":
        database_path = None

        if st.session_state.data_source != "Demo Database":
            st.session_state.query_results = None
            st.session_state.generated_sql = None
            st.session_state.question = None
            st.session_state.explanation = None

        st.session_state.data_source = "Demo Database"

        database_schema = get_database_schema()

    # --------------------------------------------------
    # Uploaded database
    # --------------------------------------------------

    if data_source == "Upload Your Data":
        uploaded_file = st.file_uploader(
            "Upload CSV, Excel, or SQLite database",
            type=[
                "csv",
                "xlsx",
                "xls",
                "db",
                "sqlite",
                "sqlite3",
            ],
        )

        if uploaded_file is None:
            if st.session_state.query_results is not None:
                database_path = st.session_state.database_path

                if database_path is not None:
                    database_schema = get_schema_for_database(database_path)

                else:
                    st.info("Upload a file to start.")
                    return

            else:
                st.info("Upload a CSV, Excel, or SQLite database to start.")
                return

        else:
            uploaded_file_key = f"{uploaded_file.name}_{uploaded_file.size}"

            if st.session_state.get("uploaded_file_key") != uploaded_file_key:
                try:
                    database_path = get_uploaded_database(uploaded_file)

                except ValueError as error:
                    st.error(str(error))
                    return

                st.session_state.database_path = database_path

                st.session_state.uploaded_file_key = uploaded_file_key

                st.session_state.query_results = None
                st.session_state.generated_sql = None
                st.session_state.question = None
                st.session_state.explanation = None

            database_path = st.session_state.database_path

            database_schema = get_schema_for_database(database_path)

            st.success(f"{uploaded_file.name} loaded successfully.")

    # --------------------------------------------------
    # Schema
    # --------------------------------------------------

    if not database_schema:
        st.warning("No tables were found.")
        return

    schema = format_schema(database_schema)

    # --------------------------------------------------
    # Sidebar
    # --------------------------------------------------

    with st.sidebar:
        st.markdown("## QueryMind")

        st.caption("AI-powered data analyst")

        st.divider()

        st.markdown("### How it works")

        st.markdown(
            """
            **01 · Connect**

            Connect your data.

            **02 · Ask**

            Ask a question in plain English.

            **03 · Generate**

            Gemma converts the question into SQL.

            **04 · Validate**

            QueryMind validates the SQL.

            **05 · Analyze**

            View results and visualizations.
            """
        )

        st.divider()

        st.markdown("### Connected data")

        st.success("Database ready")

        st.caption(f"{len(database_schema)} tables available")

        for table_name in database_schema:
            st.write(f"• `{table_name}`")

    # --------------------------------------------------
    # Question input
    # --------------------------------------------------

    st.markdown("## What would you like to know?")

    question = st.text_area(
        "Ask QueryMind",
        placeholder=(
            "Example: Show each product with "
            "its price, total quantity sold, "
            "and total revenue."
        ),
        height=120,
        key="question_input",
    )

    st.caption(
        "QueryMind converts your question into SQL and runs it against your data."
    )

    run_query = st.button(
        "Run Query →",
        type="primary",
        use_container_width=True,
    )

    # --------------------------------------------------
    # ONLY run AI + SQL when button is clicked
    # --------------------------------------------------

    if run_query:
        if not question.strip():
            st.warning("Please enter a question.")
            return

        st.session_state.query_results = None
        st.session_state.generated_sql = None
        st.session_state.explanation = None
        st.session_state.query_error = None

        try:
            with st.spinner("Understanding your question..."):
                sql = generate_sql(
                    question,
                    schema,
                )

            with st.spinner("Querying your data..."):
                results = execute_safe_query(
                    sql,
                    database_path,
                )

            with st.spinner("Generating insights..."):
                explanation = explain_results(
                    question,
                    results,
                )

            # Store everything.
            st.session_state.question = question

            st.session_state.generated_sql = sql

            st.session_state.query_results = results

            st.session_state.explanation = explanation

        except ValueError as error:
            st.session_state.query_error = str(error)

    # --------------------------------------------------
    # Show stored query error
    # --------------------------------------------------

    if st.session_state.query_error:
        st.error(st.session_state.query_error)

        return

    # --------------------------------------------------
    # Nothing executed yet
    # --------------------------------------------------

    if st.session_state.query_results is None:
        st.info("💡 Ask a question about your data to get started.")

        return

    # --------------------------------------------------
    # Generated SQL
    # --------------------------------------------------

    st.divider()

    st.markdown("## Generated SQL")

    st.code(
        st.session_state.generated_sql,
        language="sql",
    )

    # --------------------------------------------------
    # Results
    # --------------------------------------------------

    st.markdown("## Results")

    results = st.session_state.query_results

    has_results = False

    for index, result in enumerate(results):
        rows = result["rows"]

        st.markdown(f"### Query {index + 1}")

        if rows:
            has_results = True

            dataframe = results_to_dataframe(result)

            st.dataframe(
                dataframe,
                use_container_width=True,
                hide_index=True,
            )

            st.caption(f"{len(rows)} result{'s' if len(rows) != 1 else ''} returned")

            show_visualization(
                dataframe,
                index,
            )

        else:
            st.info("No matching records were found.")

    # --------------------------------------------------
    # AI Insight
    # --------------------------------------------------

    if has_results:
        st.markdown("## AI Insight")

        st.success(st.session_state.explanation)


if __name__ == "__main__":
    main()
