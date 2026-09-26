from database.connection import get_connection


def get_database_schema():
    connection = get_connection()
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

    connection.close()

    return schema


def format_schema(schema):
    lines = []

    for table_name, columns in schema.items():
        lines.append(f"Table: {table_name}")

        for column in columns:
            primary_key = " PRIMARY KEY" if column["primary_key"] else ""
            lines.append(f"  - {column['name']} ({column['type']}){primary_key}")

        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    schema = get_database_schema()
    print(format_schema(schema))
