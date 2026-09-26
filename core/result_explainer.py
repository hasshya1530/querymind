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


def explain_results(question, results):
    if not results:
        return "No results were found for this question."

    client = get_client()

    result_sections = []

    for index, result in enumerate(results, start=1):
        columns = result["columns"]
        rows = result["rows"]

        if rows:
            result_text = "\n".join(str(dict(zip(columns, row))) for row in rows)
        else:
            result_text = "No rows returned."

        result_sections.append(f"Query {index}:\n{result_text}")

    all_results = "\n\n".join(result_sections)

    prompt = f"""
You are a data analyst explaining database query results to a user.

USER QUESTION:
{question}

QUERY RESULTS:
{all_results}

Instructions:
- Answer the user's question directly.
- Use only the information present in the query results.
- Do not invent facts or numbers.
- If multiple query results are provided, consider all of them.
- Keep the explanation concise and easy to understand.
- Mention important numbers when relevant.
- Do not discuss SQL or database implementation.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    if not response.text:
        raise ValueError("The model returned an empty response.")

    return response.text.strip()


if __name__ == "__main__":
    question = "Show me the products and customers."

    results = [
        {
            "sql": "SELECT * FROM products",
            "columns": ["product_id", "name", "price"],
            "rows": [
                (1, "Laptop Pro", 1200.0),
                (2, "Wireless Headphones", 150.0),
            ],
        },
        {
            "sql": "SELECT * FROM customers",
            "columns": ["customer_id", "name", "city"],
            "rows": [
                (1, "Aarav Sharma", "Mumbai"),
                (2, "Diya Patel", "Pune"),
            ],
        },
    ]

    explanation = explain_results(
        question,
        results,
    )

    print("\nExplanation:")
    print(explanation)
