from database.connection import execute_query

from core.sql_validator import split_sql_statements, validate_sql


def execute_safe_query(sql, db_path=None):
    is_valid, message = validate_sql(sql)

    if not is_valid:
        raise ValueError(message)

    statements = split_sql_statements(sql)

    results = []

    for statement in statements:
        columns, rows = execute_query(
            statement,
            db_path,
        )

        results.append(
            {
                "sql": statement,
                "columns": columns,
                "rows": rows,
            }
        )

    return results


if __name__ == "__main__":
    sql = """
    SELECT * FROM products;
    SELECT * FROM customers;
    """

    results = execute_safe_query(sql)

    for index, result in enumerate(results, start=1):
        print(f"\nQuery {index}:")
        print(result["sql"])

        print("\nColumns:")
        print(result["columns"])

        print("\nResults:")
        for row in result["rows"]:
            print(row)
