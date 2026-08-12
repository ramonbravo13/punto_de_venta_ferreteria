import sys

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Migrations for combos
old_init = '''                try:
                    cursor.execute("ALTER TABLE sales ADD COLUMN discount_applied REAL DEFAULT 0")
                except: pass'''
new_init = '''                try:
                    cursor.execute("ALTER TABLE sales ADD COLUMN discount_applied REAL DEFAULT 0")
                except: pass
                
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN combo_reference TEXT")
                except: pass
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN combo_name TEXT")
                except: pass
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN distribution_method TEXT")
                except: pass'''
content = content.replace(old_init, new_init)


# 2. Add add_combo_purchase
new_method = '''
    def add_combo_purchase(self, combo_name, total_cost, distribution_method, items, 
                           supplier_id, payment_method, buyer_tag, origin_state, 
                           purchase_type, delivery_date, delivery_status):
        """
        Registra una compra tipo combo. items es una lista de diccionarios:
        [{'product_id': id, 'quantity': q, 'unit_cost': c, 'new_selling_price': sp}]
        """
        import uuid
        combo_ref = str(uuid.uuid4())
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for item in items:
                    p_id = item['product_id']
                    qty = item['quantity']
                    u_cost = item['unit_cost']
                    total_p_cost = qty * u_cost
                    n_price = item.get('new_selling_price')
                    
                    cursor.execute("""
                        INSERT INTO purchases (
                            product_id, quantity, unit_cost, total_cost, supplier_id, 
                            payment_method, buyer_tag, is_return, origin_state,
                            purchase_type, delivery_date, delivery_status,
                            combo_reference, combo_name, distribution_method
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (p_id, qty, u_cost, total_p_cost, supplier_id, payment_method, 
                          buyer_tag, 0, origin_state, purchase_type, delivery_date, 
                          delivery_status, combo_ref, combo_name, distribution_method))
                    
                    # Stock
                    if delivery_status != 'Pendiente':
                        cursor.execute("UPDATE products SET current_stock = current_stock + ? WHERE id = ?", (qty, p_id))
                    
                    # Update cost and price
                    if n_price is not None and str(n_price).strip() != "":
                        try:
                            price_val = float(n_price)
                            cursor.execute("UPDATE products SET cost_price = ?, selling_price = ? WHERE id = ?", (u_cost, price_val, p_id))
                        except ValueError:
                            cursor.execute("UPDATE products SET cost_price = ? WHERE id = ?", (u_cost, p_id))
                    else:
                        cursor.execute("UPDATE products SET cost_price = ? WHERE id = ?", (u_cost, p_id))
                        
                conn.commit()
                return combo_ref
        except sqlite3.Error as e:
            print(f"Error al registrar compra combo: {e}")
            return None

    def get_pending_orders(self):'''

content = content.replace("    def get_pending_orders(self):", new_method)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("database.py updated for combos")
