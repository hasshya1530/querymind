import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "querymind.db"


def get_connection(db_path=None):
    path = db_path or DB_PATH
    return sqlite3.connect(path)


def execute_query(sql, db_path=None):
    connection = get_connection(db_path)

    try:
        cursor = connection.cursor()
        cursor.execute(sql)

        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        return columns, rows

    finally:
        connection.close()


def load_csv(file_path, table_name, db_path):
    dataframe = pd.read_csv(file_path)

    connection = get_connection(db_path)

    try:
        dataframe.to_sql(
            table_name,
            connection,
            if_exists="replace",
            index=False,
        )
    finally:
        connection.close()


def load_excel(file_path, db_path):
    sheets = pd.read_excel(
        file_path,
        sheet_name=None,
    )

    connection = get_connection(db_path)

    try:
        for sheet_name, dataframe in sheets.items():
            table_name = sheet_name.strip().replace(" ", "_")

            dataframe.to_sql(
                table_name,
                connection,
                if_exists="replace",
                index=False,
            )
    finally:
        connection.close()
