import os

from dotenv import load_dotenv
from google import genai

load_dotenv()


MODEL_NAME = "gemma-4-26b-a4b-it"


def get_client():
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set.")

    return genai.Client(api_key=api_key)


def generate_sql(question, schema):
    client = get_client()

    prompt = f"""
You are an expert SQLite SQL query generator and data analyst.

Your task is to convert a user's natural-language question into
a correct SQLite SQL query using ONLY the provided database schema.

DATABASE SCHEMA:
{schema}


SQL GENERATION RULES:

1. Use ONLY tables and columns that exist in the provided schema.

2. Never assume that a table exists unless it appears in the schema.

3. Never assume that a column exists unless it appears in the schema.

4. Never invent table names.

5. Never invent column names.

6. Use JOINs only when the provided schema supports the relationship.

7. Infer relationships only from the provided schema.

8. Use valid SQLite syntax.

9. Only generate read-only SELECT queries.

10. Never generate:
INSERT
UPDATE
DELETE
DROP
ALTER
CREATE
REPLACE
TRUNCATE
ATTACH
DETACH

11. If the user asks for a ranking, comparison, highest,
lowest, most, least, top, bottom, maximum, minimum,
or similar analytical result, ALWAYS return both:

- the identifying categorical column
- the numeric metric used for the ranking or comparison

For example, if the user asks:

"Which customer generated the most revenue?"

DO NOT return only:

SELECT customer_name ...

Instead return the customer and revenue:

SELECT
    customer_name,
    SUM(...) AS revenue
...

12. If you use an aggregate expression such as:

SUM(...)
COUNT(...)
AVG(...)
MIN(...)
MAX(...)

and that value is relevant to the user's question,
include that value in the SELECT output.

13. Give calculated numeric columns clear aliases.

Examples:

SUM(...) AS revenue
COUNT(*) AS order_count
AVG(...) AS average_price
SUM(...) AS total_quantity

14. If the user asks "which", "who", or "what" and the
answer depends on a numeric calculation, include the
calculated numeric value in the result.

15. If the user asks for a trend over time, return:

- the date/time column
- the numeric metric

16. If the user asks for a comparison between categories,
return:

- the category
- the numeric metric

17. If the user asks for multiple metrics, include all
relevant metrics in the SELECT output.

18. If the user asks for "top N", include the category and
the metric being ranked, then use ORDER BY and LIMIT N.

19. If the user asks for "bottom N", include the category
and the metric being ranked, then use ORDER BY ASC and LIMIT N.

20. Do not remove a useful numeric metric merely because
the user asks for only the name of the winner.

21. The query result should contain enough information to
allow a data analyst application to visualize meaningful
categorical comparisons, trends, distributions, or numeric
relationships when appropriate.

22. The database schema above is the source of truth.

23. Do NOT use tables, columns, relationships, or business
rules from previous examples unless they actually exist
in the provided schema.

24. Return ONLY the SQL query.

25. Do not use markdown code fences.

26. Do not provide explanations.

USER QUESTION:
{question}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    if not response.text:
        raise ValueError("The model returned an empty response.")

    return response.text.strip()


if __name__ == "__main__":
    from core.schema_discovery import (
        format_schema,
        get_database_schema,
    )

    schema = format_schema(get_database_schema())

    question = input("Ask a question about the database: ")

    sql = generate_sql(
        question,
        schema,
    )

    print("\nGenerated SQL:")
    print(sql)
