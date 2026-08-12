import sys

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. init_db
old_init = '''                try:
                    cursor.execute("ALTER TABLE products ADD COLUMN tax_percentage REAL DEFAULT 0")
                except: pass'''
new_init = '''                try:
                    cursor.execute("ALTER TABLE products ADD COLUMN tax_percentage REAL DEFAULT 0")
                except: pass
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN purchase_type TEXT DEFAULT 'Física'")
                except: pass
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN delivery_date TIMESTAMP")
                except: pass
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN delivery_status TEXT DEFAULT 'Entregado'")
                except: pass'''
content = content.replace(old_init, new_init)

# 2. get_all_products
old_get_all = '''                cursor.execute("SELECT id, image_path, sku, name, category, current_stock, cost_price, selling_price, min_stock, tax_percentage FROM products")'''
new_get_all = '''                cursor.execute("""
                    SELECT p.id, p.image_path, p.sku, p.name, p.category, 
                           p.current_stock, p.cost_price, p.selling_price, p.min_stock, p.tax_percentage,
                           IFNULL((SELECT SUM(quantity) FROM purchases WHERE product_id = p.id AND delivery_status = 'Pendiente' AND is_return = 0), 0) as incoming_stock,
                           (SELECT MIN(delivery_date) FROM purchases WHERE product_id = p.id AND delivery_status = 'Pendiente' AND is_return = 0) as next_delivery
                    FROM products p
                """)'''
content = content.replace(old_get_all, new_get_all)

# 3. add_purchase signature
old_sig = '''    def add_purchase(self, product_id, qty, unit_cost, supplier_id, payment_method, buyer_tag, 
                     is_return=0, card_name=None, is_paid=1, due_date=None, 
                     origin_state=None, tax_percentage=0, new_selling_price=None):'''
new_sig = '''    def add_purchase(self, product_id, qty, unit_cost, supplier_id, payment_method, buyer_tag, 
                     is_return=0, card_name=None, is_paid=1, due_date=None, 
                     origin_state=None, tax_percentage=0, new_selling_price=None,
                     purchase_type='Física', delivery_date=None, delivery_status='Entregado'):'''
content = content.replace(old_sig, new_sig)

# 4. add_purchase insert
old_insert = '''                    INSERT INTO purchases (
                        product_id, quantity, unit_cost, total_cost, supplier_id, 
                        payment_method, buyer_tag, is_return, card_name, is_paid, 
                        due_date, origin_state, tax_percentage
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (product_id, qty, unit_cost, total_cost_with_tax, supplier_id, 
                      payment_method, buyer_tag, is_return, card_name, is_paid, 
                      due_date, origin_state, tax_percentage))'''
new_insert = '''                    INSERT INTO purchases (
                        product_id, quantity, unit_cost, total_cost, supplier_id, 
                        payment_method, buyer_tag, is_return, card_name, is_paid, 
                        due_date, origin_state, tax_percentage, purchase_type, delivery_date, delivery_status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (product_id, qty, unit_cost, total_cost_with_tax, supplier_id, 
                      payment_method, buyer_tag, is_return, card_name, is_paid, 
                      due_date, origin_state, tax_percentage, purchase_type, delivery_date, delivery_status))'''
content = content.replace(old_insert, new_insert)

# 5. add_purchase stock logic
old_stock = '''                # 2. Actualizar stock
                stock_change = -qty if is_return else qty
                cursor.execute("UPDATE products SET current_stock = current_stock + ? WHERE id = ?", 
                               (stock_change, product_id))'''
new_stock = '''                # 2. Actualizar stock
                if delivery_status != 'Pendiente':
                    stock_change = -qty if is_return else qty
                    cursor.execute("UPDATE products SET current_stock = current_stock + ? WHERE id = ?", 
                                   (stock_change, product_id))'''
content = content.replace(old_stock, new_stock)

# 6. Add new methods
new_methods = '''
    def get_pending_orders(self):
        """Obtiene todas las compras en línea que están pendientes de entrega."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.id, pr.name, p.quantity, p.delivery_date, p.total_cost, p.supplier_id
                    FROM purchases p
                    JOIN products pr ON p.product_id = pr.id
                    WHERE p.delivery_status = 'Pendiente' AND p.is_return = 0
                    ORDER BY p.delivery_date ASC
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener órdenes pendientes: {e}")
            return []

    def receive_purchase(self, purchase_id):
        """Marca una orden pendiente como entregada y suma el stock."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # 1. Obtener detalles
                cursor.execute("SELECT product_id, quantity, delivery_status FROM purchases WHERE id = ?", (purchase_id,))
                row = cursor.fetchone()
                if not row or row[2] != 'Pendiente':
                    return False
                
                product_id, quantity, _ = row
                
                # 2. Marcar como entregado
                cursor.execute("UPDATE purchases SET delivery_status = 'Entregado' WHERE id = ?", (purchase_id,))
                
                # 3. Sumar el stock físicamente
                cursor.execute("UPDATE products SET current_stock = current_stock + ? WHERE id = ?", (quantity, product_id))
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al recibir compra: {e}")
            return False

    def add_sale(self,'''
content = content.replace('''    def add_sale(self,''', new_methods)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("database.py updated")
