# QueryMind — Natural Language SQL Analyst

> **Ask questions. Query data. Discover insights.**

QueryMind is an AI-powered natural language SQL analyst that lets users interact with structured data using plain English.

Instead of manually writing SQL queries, users can ask questions about their data and QueryMind uses **Google Gemma 4** to generate SQL, validates the generated query, executes it against SQLite, explains the results, and provides multiple visualization options.

**Live Demo:** https://querymind-ai-analyst.streamlit.app/

**GitHub:** https://github.com/hasshya1530/querymind

---

## Overview

QueryMind follows a simple natural-language data analysis workflow:

```text
Natural Language Question
          ↓
    Schema Discovery
          ↓
      Google Gemma 4
          ↓
     SQL Generation
          ↓
     SQL Validation
          ↓
    SQLite Execution
          ↓
      Query Results
          ↓
    AI Explanation
          ↓
     Visualization
          ↓
       Export
```

The goal is to make database analysis accessible without requiring users to write SQL manually.

---

## Features

### Natural Language to SQL

Ask questions about your data using everyday language.

Example:

```text
Which customer generated the most revenue?
```

QueryMind converts the question into a SQL query using the available database schema.

### Automatic Schema Discovery

QueryMind inspects the connected SQLite database and discovers:

- Tables
- Columns
- Column types
- Primary keys

The discovered schema is provided to Gemma so SQL generation is based on the actual database structure.

### SQL Validation

Generated SQL is validated before it reaches the database.

QueryMind only allows read-oriented queries and blocks operations such as:

```text
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
```

This provides a validation layer between the LLM-generated SQL and the database.

### SQLite Query Execution

Validated SQL queries are executed against SQLite.

The application supports:

- SELECT queries
- Aggregations
- Filtering
- Sorting
- GROUP BY
- JOINs
- Ranking
- Calculations

### AI Result Explanation

After the query is executed, QueryMind uses Gemma 4 to explain the returned results in simple language.

---

## Data Visualization

QueryMind gives users control over how query results are visualized.

Available chart types:

```text
Bar
Line
Pie
Scatter
Grouped Bar
```

The user can switch between chart types after the query has been executed.

### No repeated query execution

Changing the chart type does **not** generate a new SQL query or call the LLM again.

The charts are generated from the existing query result stored in the Streamlit session.

```text
Run Query
    ↓
Gemma generates SQL
    ↓
SQL executes
    ↓
Result is stored
    ↓
Bar | Line | Pie | Scatter | Grouped Bar
              ↓
       Change visualization
```

This keeps database querying and visualization separate.

---

## Chart Export

QueryMind provides two export options.

### Download Current Chart

Download the currently selected visualization as a PNG image.

### Download All 5 Charts

Download all five chart variants together as a ZIP file:

```text
querymind_all_5_charts.zip

├── bar.png
├── line.png
├── pie.png
├── scatter.png
└── grouped_bar.png
```

---

## Supported Data Sources

QueryMind includes a demo SQLite database and supports uploading external datasets.

### Demo Database

The included demo database contains:

```text
customers
products
orders
order_items
```

The relational structure allows QueryMind to demonstrate multi-table queries and JOIN operations.

### Supported Upload Formats

```text
.csv
.xlsx
.xls
.db
.sqlite
.sqlite3
```

Uploaded structured data can be queried using the same natural-language interface.

---

## Example Questions

### Customer Analysis

```text
Show each customer with their total revenue.
```

```text
Which customer generated the most revenue?
```

```text
Show each customer with their total revenue and total quantity purchased.
```

```text
Show the customers ranked by total revenue.
```

### Product Analysis

```text
Show each product with its price and total quantity sold.
```

```text
Show each product with its price and total revenue.
```

```text
Which product generated the most revenue?
```

```text
Show the top 5 products by total revenue.
```

### Order Analysis

```text
Show total revenue for each order date.
```

```text
Show the total number of orders for each order date.
```

```text
Show the total quantity of products sold for each order date.
```

### Category Analysis

```text
Show each product category and its total revenue.
```

```text
Show the number of products in each category.
```

---

## SQL Generation

QueryMind provides Gemma 4 with the database schema and the user's question.

The SQL generation process is instructed to:

- Use only tables present in the provided schema
- Use only columns present in the provided schema
- Avoid inventing tables
- Avoid inventing columns
- Use JOINs only when supported by the schema
- Generate valid SQLite syntax
- Generate read-only SELECT queries
- Include relevant aggregate metrics
- Include meaningful fields for analytical results
- Return SQL without unnecessary explanation

For analytical questions, QueryMind also attempts to retain the metric used for the calculation.

For example:

```text
name          revenue
---------------------
Rohan Mehta   2600
```

This makes the result more useful for analysis and visualization.

---

## SQL Safety Layer

LLM-generated SQL should not be executed blindly.

QueryMind separates SQL generation from SQL execution:

```text
User Question
      ↓
LLM SQL Generation
      ↓
SQL Validator
      ↓
Valid SELECT?
   ↙       ↘
 No         Yes
 ↓           ↓
Reject    Execute
```

The validator checks that generated statements are read-only and rejects prohibited SQL operations.

---

## Project Architecture

```text
querymind/
│
├── app.py
│
├── database/
│   ├── __init__.py
│   ├── connection.py
│   ├── schema.py
│   └── querymind.db
│
├── core/
│   ├── __init__.py
│   ├── schema_discovery.py
│   ├── sql_generator.py
│   ├── sql_validator.py
│   ├── query_executor.py
│   └── result_explainer.py
│
├── utils/
│   ├── __init__.py
│   └── helpers.py
│
├── .env
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Core Components

### `app.py`

The main Streamlit application responsible for:

- User interface
- Data source selection
- File uploads
- Question input
- Query execution
- Results display
- Visualization controls
- Chart downloads
- AI insights

### `database/connection.py`

Handles:

- SQLite connections
- SQL execution
- CSV loading
- Excel loading

### `database/schema.py`

Creates and initializes the QueryMind demo database.

### `core/schema_discovery.py`

Discovers:

- Table names
- Column names
- Column types
- Primary-key information

### `core/sql_generator.py`

Uses Google Gemma 4 to convert natural-language questions into SQLite SQL queries.

### `core/sql_validator.py`

Validates generated SQL before execution and ensures only permitted read-only SQL statements are accepted.

### `core/query_executor.py`

Executes validated SQL queries and converts database responses into structured results.

### `core/result_explainer.py`

Uses Gemma 4 to generate concise natural-language explanations based on query results.

### `utils/helpers.py`

Contains reusable helper functions for processing query results.

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Application development |
| Streamlit | Web application |
| Google Gemma 4 | SQL generation and result explanation |
| Google GenAI SDK | LLM API integration |
| SQLite | Database |
| Pandas | Data processing |
| Matplotlib | Data visualization |
| uv | Dependency and environment management |
| python-dotenv | Environment configuration |

---

## Getting Started

### Prerequisites

You will need:

- Python 3.12
- `uv`
- A Google Gemini API key

### 1. Clone the repository

```bash
git clone https://github.com/hasshya1530/querymind.git
cd querymind
```

### 2. Install dependencies

QueryMind uses `uv` for dependency management.

```bash
uv sync
```

### 3. Configure the API key

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

A template is provided in:

```text
.env.example
```

**Never commit your actual API key to GitHub.**

### 4. Create the demo database

```bash
uv run python database/schema.py
```

### 5. Start the application

```bash
uv run streamlit run app.py
```

---

## Environment Variables

QueryMind requires:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

The application loads this value using `python-dotenv`.

Your real `.env` file should remain local and should never be committed to the repository.

---

## Complete Query Workflow

When the user clicks **Run Query**, QueryMind follows this workflow:

```text
1. User asks a question
        ↓
2. QueryMind discovers the schema
        ↓
3. Gemma generates SQL
        ↓
4. SQL is validated
        ↓
5. SQL is executed against SQLite
        ↓
6. Results are displayed
        ↓
7. Gemma explains the results
        ↓
8. User explores visualizations
        ↓
9. Charts can be exported
```

---

## Session-Based Visualization

QueryMind separates query execution from visualization.

When a query is run, the following information is stored in the Streamlit session:

```text
Question
Generated SQL
Query Results
AI Explanation
```

This means switching between visualization types does not require another LLM request or database execution.

```text
User runs query
      ↓
Gemma called
      ↓
SQL executed
      ↓
Results stored
      ↓
Bar
 ↓
Line
 ↓
Pie
 ↓
Scatter
 ↓
Grouped Bar
```

The same result is reused throughout the visualization workflow.

---

## Demo Database Schema

The included database contains four main tables.

### Customers

```text
customer_id
name
city
country
```

### Products

```text
product_id
name
category
price
```

### Orders

```text
order_id
customer_id
order_date
```

### Order Items

```text
order_item_id
order_id
product_id
quantity
```

These relationships allow queries involving customers, orders, products, quantities, and revenue calculations.

---

## Project Goals

QueryMind was built to explore the practical use of LLMs as an interface for structured data.

Traditional database analysis often requires users to understand:

- SQL syntax
- Table relationships
- JOIN operations
- Aggregations
- Filtering
- GROUP BY
- Ordering

QueryMind provides a natural-language interface instead.

The user can ask:

```text
Which customer generated the most revenue?
```

and the application handles the translation into SQL.

The project combines:

```text
LLM
+
Database
+
SQL
+
Data Analysis
+
Visualization
```

into one application.

---

## Future Improvements

Potential future improvements include:

- PostgreSQL support
- MySQL support
- Additional database connectors
- More advanced SQL parsing
- Query history
- Saved queries
- Saved dashboards
- Additional chart types
- Automatic visualization recommendations
- Conversational follow-up questions
- Multi-database support
- Database connection management
- Authentication
- Query performance analysis
- More advanced SQL safety validation

---

## Learning Reference

QueryMind was developed as part of my hands-on learning while following the Udemy course:

**Building Gen AI App 12+ Hands-on Projects with Gemini Pro**

by **Krish Naik**.

This project was inspired by the course's **Text-to-SQL LLM application**.

Original course repository:

https://github.com/krishnaik06/Build-Gen-AI-With-Google-Gemini

The original project served as a learning reference.

QueryMind is an independent implementation with its own project structure and additional functionality, including:

- Database schema discovery
- Dedicated database layer
- SQL validation
- Read-only query enforcement
- JOIN-capable demo database
- CSV and Excel ingestion
- SQLite database upload
- AI result explanation
- Multiple visualization options
- Session-based visualization switching
- PNG chart export
- Batch chart export

---

## Deployment

QueryMind is deployed using Streamlit Community Cloud.

**Live Application:**

https://querymind-ai-analyst.streamlit.app/

---

## Author

### Hasshya Krishnamoorthy

AI/ML Engineer focused on:

- Generative AI
- LLM Applications
- Machine Learning
- Data Engineering
- AI/ML Systems

**GitHub:**  
https://github.com/hasshya1530

**Portfolio:**  
https://hasshya1530.github.io/portfolio_website/

---

## License

This project is primarily intended as a learning and portfolio project.

See the repository for the applicable license and usage terms.
