import re

FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "REPLACE",
    "TRUNCATE",
    "ATTACH",
    "DETACH",
}


def split_sql_statements(sql):
    statements = []

    for statement in sql.split(";"):
        statement = statement.strip()

        if statement:
            statements.append(statement)

    return statements


def validate_sql(sql):
    if not sql or not sql.strip():
        return False, "The generated SQL query is empty."

    statements = split_sql_statements(sql)

    for statement in statements:
        if not re.match(r"^SELECT\b", statement, re.IGNORECASE):
            return False, "Only SELECT queries are allowed."

        for keyword in FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{keyword}\b", statement, re.IGNORECASE):
                return False, f"SQL keyword '{keyword}' is not allowed."

    return True, "SQL queries are valid."
