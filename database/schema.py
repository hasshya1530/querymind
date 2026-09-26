import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "querymind.db"


def create_database():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.executescript(
        """
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            country TEXT NOT NULL
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id)
        );

        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (order_id)
                REFERENCES orders(order_id),
            FOREIGN KEY (product_id)
                REFERENCES products(product_id)
        );

        INSERT INTO customers VALUES
            (1, 'Aarav Sharma', 'Mumbai', 'India'),
            (2, 'Diya Patel', 'Pune', 'India'),
            (3, 'Rohan Mehta', 'Bangalore', 'India'),
            (4, 'Ananya Singh', 'Delhi', 'India'),
            (5, 'Kabir Shah', 'Hyderabad', 'India');

        INSERT INTO products VALUES
            (1, 'Laptop Pro', 'Electronics', 1200.00),
            (2, 'Wireless Headphones', 'Electronics', 150.00),
            (3, 'Mechanical Keyboard', 'Accessories', 100.00),
            (4, '4K Monitor', 'Electronics', 500.00),
            (5, 'USB-C Hub', 'Accessories', 60.00);

        INSERT INTO orders VALUES
            (1, 1, '2025-01-15'),
            (2, 1, '2025-02-10'),
            (3, 2, '2025-02-18'),
            (4, 2, '2025-03-05'),
            (5, 3, '2025-03-20'),
            (6, 3, '2025-04-12'),
            (7, 4, '2025-05-08'),
            (8, 4, '2025-06-15'),
            (9, 5, '2025-07-22'),
            (10, 5, '2025-08-01');

        INSERT INTO order_items VALUES
            (1, 1, 1, 1),
            (2, 2, 2, 2),
            (3, 3, 4, 1),
            (4, 4, 5, 3),
            (5, 5, 1, 2),
            (6, 6, 3, 2),
            (7, 7, 2, 3),
            (8, 8, 4, 1),
            (9, 9, 1, 1),
            (10, 10, 5, 4);
        """
    )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_database()
    print(f"Database created successfully at: {DB_PATH}")
