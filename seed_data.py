import sqlite3
import random
from datetime import datetime, timedelta

def seed_data():
    conn = sqlite3.connect("provision.db")
    cursor = conn.cursor()

    # 1. Limpiar datos previos
    cursor.execute("DELETE FROM sale_details")
    cursor.execute("DELETE FROM sales")
    cursor.execute("DELETE FROM purchases")
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM suppliers")
    cursor.execute("DELETE FROM credit_cards")
    cursor.execute("DELETE FROM categories")

    # 2. Insertar Catálogos Base
    suppliers = [("Home Depot",), ("Lowe's",), ("General",)]
    cursor.executemany("INSERT INTO suppliers (name) VALUES (?)", suppliers)
    
    cards = [("Visa - 1234",), ("MasterCard - 5678",), ("Amex - 9012",)]
    cursor.executemany("INSERT INTO credit_cards (name) VALUES (?)", cards)
    
    categories = [("Herramientas",), ("Accesorios",), ("Ferretería",), ("Iluminación",)]
    cursor.executemany("INSERT INTO categories (name) VALUES (?)", categories)
    
    conn.commit()
    
    # Obtener IDs
    cursor.execute("SELECT id FROM suppliers")
    supplier_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT name FROM credit_cards")
    card_names = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT name FROM categories")
    category_names = [row[0] for row in cursor.fetchall()]

    # 3. Insertar Productos de Prueba
    products_list = [
        ("SKU001", "Martillo Pro", "Herramientas", 10.5, 15.99, 10, 2),
        ("SKU002", "Taladro Inalámbrico", "Herramientas", 45.0, 89.99, 5, 12),
        ("SKU003", "Cinta Métrica 5m", "Accesorios", 2.0, 5.50, 20, 1),
        ("SKU004", "Sierra Eléctrica", "Herramientas", 60.0, 120.0, 3, 5),
        ("SKU005", "Destornillador Phillips", "Herramientas", 1.5, 4.0, 15, 30),
    ]

    cursor.executemany("""
        INSERT INTO products (sku, name, category, cost_price, selling_price, min_stock, current_stock)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, products_list)
    
    conn.commit()
    
    # Obtener datos de productos
    cursor.execute("SELECT id, cost_price, selling_price FROM products")
    product_data = cursor.fetchall()

    # 4. Insertar Ventas de Prueba (últimos 30 días)
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(1, 101): # 100 ventas
        sale_date = start_date + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        total_amount = 0
        sale_id = i
        ticket_number = f"TICK-{1000 + i}"
        
        cursor.execute("INSERT INTO sales (id, ticket_number, total_amount, payment_method, date) VALUES (?, ?, ?, ?, ?)",
                       (sale_id, ticket_number, 0, random.choice(["Cash", "Credit"]), sale_date))
        
        num_items = random.randint(1, 3)
        for _ in range(num_items):
            p_id, cost, price = random.choice(product_data)
            qty = random.randint(1, 2)
            subtotal = qty * price
            total_amount += subtotal
            
            cursor.execute("INSERT INTO sale_details (sale_id, product_id, quantity, price_at_sale) VALUES (?, ?, ?, ?)",
                           (sale_id, p_id, qty, price))
        
        cursor.execute("UPDATE sales SET total_amount = ? WHERE id = ?", (total_amount, sale_id))

    # 5. Insertar Compras de Prueba
    for i in range(1, 15): # 15 compras
        p_id, cost, price = random.choice(product_data)
        qty = random.randint(5, 10)
        method = random.choice(["Cash", "Credit"])
        card = random.choice(card_names) if method == "Credit" else None
        is_paid = random.choice([0, 1]) if method == "Credit" else 1 
        
        cursor.execute("""
            INSERT INTO purchases (product_id, quantity, unit_cost, total_cost, supplier_id, payment_method, buyer_tag, date, card_name, is_paid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (p_id, qty, cost, qty * cost, random.choice(supplier_ids), method, random.choice(["David", "Stacey", "Dueño"]), datetime.now() - timedelta(days=random.randint(0, 20)), card, is_paid))

    conn.commit()
    conn.close()
    print("Datos de prueba cargados con éxito.")

if __name__ == "__main__":
    seed_data()
