import pandas as pd


def results_to_dataframe(result):
    columns = result["columns"]
    rows = result["rows"]

    if not rows:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        rows,
        columns=columns,
    )


def is_date_column(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return True

    if not pd.api.types.is_object_dtype(series):
        return False

    if series.empty:
        return False

    converted = pd.to_datetime(
        series,
        errors="coerce",
    )

    return converted.notna().mean() >= 0.8


def get_column_types(dataframe):
    numeric_columns = dataframe.select_dtypes(include="number").columns.tolist()

    categorical_columns = [
        column for column in dataframe.columns if column not in numeric_columns
    ]

    date_columns = [
        column for column in categorical_columns if is_date_column(dataframe[column])
    ]

    categorical_columns = [
        column for column in categorical_columns if column not in date_columns
    ]

    return (
        numeric_columns,
        categorical_columns,
        date_columns,
    )


def get_chart_type(dataframe):
    if dataframe.empty:
        return None

    if len(dataframe.columns) < 2:
        return None

    (
        numeric_columns,
        categorical_columns,
        date_columns,
    ) = get_column_types(dataframe)

    # Date + numeric = line chart.
    if date_columns and numeric_columns:
        return "line"

    # Two numeric columns = scatter plot.
    if len(numeric_columns) == 2 and not categorical_columns:
        return "scatter"

    # Category + multiple numeric columns =
    # grouped bar chart.
    if categorical_columns and len(numeric_columns) >= 2:
        return "grouped_bar"

    # Category + one numeric column.
    if categorical_columns and len(numeric_columns) == 1:
        if len(dataframe) <= 6:
            return "pie"

        return "bar"

    return None


def get_chart_columns(dataframe):
    chart_type = get_chart_type(dataframe)

    if not chart_type:
        return (
            None,
            None,
            None,
        )

    (
        numeric_columns,
        categorical_columns,
        date_columns,
    ) = get_column_types(dataframe)

    if chart_type == "line":
        return (
            chart_type,
            date_columns[0],
            numeric_columns[0],
        )

    if chart_type == "scatter":
        return (
            chart_type,
            numeric_columns[0],
            numeric_columns[1],
        )

    if chart_type == "grouped_bar":
        return (
            chart_type,
            categorical_columns[0],
            numeric_columns,
        )

    if chart_type == "bar":
        return (
            chart_type,
            categorical_columns[0],
            numeric_columns[0],
        )

    if chart_type == "pie":
        return (
            chart_type,
            categorical_columns[0],
            numeric_columns[0],
        )

    return (
        None,
        None,
        None,
    )
