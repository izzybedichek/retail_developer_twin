import sqlite3

# ref https://sqldocs.org/sqlite-create-database/, https://docs.python.org/3/library/sqlite3.html
connection = sqlite3.connect('inventory.db')

# needed to execute queries
cur = connection.cursor()

# using https://www.w3resource.com/projects/sql/sql-projects-on-inventory-management-system.php
# database structure
cur.execute("CREATE TABLE Products(product_id INT PRIMARY KEY,"
            "product_name VARCHAR(255) NOT NULL,"
            "price DECIMAL(10, 2) NOT NULL,"
            "category VARCHAR(100));")

cur.execute("CREATE TABLE Suppliers ("
            "supplier_id INT PRIMARY KEY,"
            "supplier_name VARCHAR(255) NOT NULL,"
            "contact_email VARCHAR(255),"
            "phone_number VARCHAR(15));")

cur.execute("CREATE TABLE Inventory ("
            "inventory_id INT PRIMARY KEY,"
            "product_id INT,"
            "quantity INT DEFAULT 0,"
            "supplier_id INT,"
            "last_updated DATE DEFAULT (CURRENT_DATE),"
            "FOREIGN KEY (product_id) REFERENCES Products(product_id),"
            "FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id));")


cur.execute("CREATE TABLE Transactions ("
            "transaction_id INT PRIMARY KEY,"
            "product_id INT,"
            "transaction_type TEXT CHECK(transaction_type IN ('sale', 'purchase')) NOT NULL,"
            "transaction_date DATE DEFAULT (CURRENT_DATE),"
            "quantity INT NOT NULL,"
            "FOREIGN KEY (product_id) REFERENCES Products(product_id));")

connection.commit()
connection.close()
