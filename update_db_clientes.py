import sys

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. init_db adding customers table and sales migration
old_init = '''                try:
                    cursor.execute("ALTER TABLE sales ADD COLUMN caja_id INTEGER")
                except: pass'''
new_init = '''                try:
                    cursor.execute("ALTER TABLE sales ADD COLUMN caja_id INTEGER")
                except: pass
                
                # Tabla de Clientes
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS customers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        phone TEXT,
                        email TEXT,
                        address TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                try:
                    cursor.execute("ALTER TABLE sales ADD COLUMN customer_id INTEGER")
                except: pass
                try:
                    cursor.execute("ALTER TABLE sales ADD COLUMN discount_applied REAL DEFAULT 0")
                except: pass'''
content = content.replace(old_init, new_init)

# 2. add_sale logic update
old_add_sale = '''    def add_sale(self, total_amount, payment_method, items, caja_id=None, notes=None):
        """
        Registra una venta completa.
        items: Lista de tuplas (product_id, quantity, price)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Generar ticket
                import datetime
                ticket_number = f"TICK-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # 2. Insertar venta principal
                cursor.execute("""
                    INSERT INTO sales (ticket_number, total_amount, payment_method, caja_id, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (ticket_number, total_amount, payment_method, caja_id, notes))'''

new_add_sale = '''    def add_sale(self, total_amount, payment_method, items, caja_id=None, notes=None, customer_id=None, discount=0.0):
        """
        Registra una venta completa.
        items: Lista de tuplas (product_id, quantity, price)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Generar ticket
                import datetime
                ticket_number = f"TICK-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # 2. Insertar venta principal
                cursor.execute("""
                    INSERT INTO sales (ticket_number, total_amount, payment_method, caja_id, notes, customer_id, discount_applied)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (ticket_number, total_amount, payment_method, caja_id, notes, customer_id, discount))'''
content = content.replace(old_add_sale, new_add_sale)

# 3. Customer DB Methods
customer_methods = '''
    # --- METODOS DE CLIENTES ---
    def get_all_customers(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.id, c.name, c.phone, c.email,
                           COUNT(s.id) as total_visits,
                           IFNULL(SUM(s.total_amount), 0) as total_spent,
                           IFNULL(SUM(s.discount_applied), 0) as total_discounts
                    FROM customers c
                    LEFT JOIN sales s ON c.id = s.customer_id
                    GROUP BY c.id
                    ORDER BY c.name
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener clientes: {e}")
            return []

    def add_customer(self, name, phone="", email="", address=""):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO customers (name, phone, email, address) VALUES (?, ?, ?, ?)",
                               (name, phone, email, address))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al añadir cliente: {e}")
            return False

    def update_customer(self, c_id, name, phone, email, address):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE customers 
                    SET name=?, phone=?, email=?, address=?
                    WHERE id=?
                """, (name, phone, email, address, c_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al actualizar cliente: {e}")
            return False

    def delete_customer(self, c_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Opcionalmente, desligar ventas del cliente en lugar de borrar para que no haya FK errors
                cursor.execute("UPDATE sales SET customer_id = NULL WHERE customer_id = ?", (c_id,))
                cursor.execute("DELETE FROM customers WHERE id = ?", (c_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al eliminar cliente: {e}")
            return False

    def get_top_customers_by_spent(self, limit=10):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.name, SUM(s.total_amount) as total
                    FROM customers c JOIN sales s ON c.id = s.customer_id
                    GROUP BY c.id ORDER BY total DESC LIMIT ?
                """, (limit,))
                return cursor.fetchall()
        except sqlite3.Error: return []

    def get_top_customers_by_frequency(self, limit=10):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.name, COUNT(s.id) as freq
                    FROM customers c JOIN sales s ON c.id = s.customer_id
                    GROUP BY c.id ORDER BY freq DESC LIMIT ?
                """, (limit,))
                return cursor.fetchall()
        except sqlite3.Error: return []

    def get_top_customers_by_promotions(self, limit=10):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.name, SUM(s.discount_applied) as discounts
                    FROM customers c JOIN sales s ON c.id = s.customer_id
                    WHERE s.discount_applied > 0
                    GROUP BY c.id ORDER BY discounts DESC LIMIT ?
                """, (limit,))
                return cursor.fetchall()
        except sqlite3.Error: return []

    def get_customer_history(self, customer_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT date, ticket_number, total_amount, discount_applied
                    FROM sales WHERE customer_id = ? ORDER BY date DESC
                """, (customer_id,))
                return cursor.fetchall()
        except sqlite3.Error: return []

if __name__ == "__main__":
'''
content = content.replace('''if __name__ == "__main__":''', customer_methods)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("database.py updated for clients")
