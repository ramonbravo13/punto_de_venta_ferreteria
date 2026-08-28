import sqlite3
import os
import shutil
from datetime import datetime

class DatabaseManager:
    """
    Gestiona la conexión y operaciones de la base de datos SQLite para Pro-Vision POS.
    Incluye soporte para transacciones y backups automáticos.
    """
    def __init__(self, db_path="provision.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Retorna una conexión con soporte para claves foráneas."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """Crea las tablas necesarias si no existen."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tabla de Productos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sku TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        category TEXT,
                        image_path TEXT,
                        min_stock INTEGER DEFAULT 5,
                        current_stock INTEGER DEFAULT 0,
                        cost_price REAL NOT NULL,
                        selling_price REAL NOT NULL,
                        tax_percentage REAL DEFAULT 0,
                        marca TEXT DEFAULT '',
                        modelo TEXT DEFAULT '',
                        voltaje TEXT DEFAULT ''
                    )
                """)

                # Tabla de Proveedores
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS suppliers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL
                    )
                """)

                # Tabla de Brand Prefixes
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS brand_prefixes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        brand TEXT UNIQUE NOT NULL,
                        prefix TEXT UNIQUE NOT NULL
                    )
                """)

                # Insertar proveedores por defecto si no existen
                cursor.execute("INSERT OR IGNORE INTO suppliers (name) VALUES ('Home Depot'), ('Lowe''s'), ('General')")

                try:
                    cursor.execute("ALTER TABLE sales ADD COLUMN caja_id INTEGER")
                except: pass
                
                try: cursor.execute("ALTER TABLE products ADD COLUMN marca TEXT DEFAULT ''")
                except: pass
                try: cursor.execute("ALTER TABLE products ADD COLUMN modelo TEXT DEFAULT ''")
                except: pass
                try: cursor.execute("ALTER TABLE products ADD COLUMN voltaje TEXT DEFAULT ''")
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
                except: pass
                
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN combo_reference TEXT")
                except: pass
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN combo_name TEXT")
                except: pass
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN distribution_method TEXT")
                except: pass
                
                # Tabla de Compras
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS purchases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        quantity INTEGER NOT NULL,
                        unit_cost REAL NOT NULL,
                        total_cost REAL NOT NULL,
                        supplier_id INTEGER NOT NULL,
                        payment_method TEXT NOT NULL, -- Cash/Credit
                        buyer_tag TEXT,               -- David/Stacey
                        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_return BOOLEAN DEFAULT 0,
                        card_name TEXT,               -- Nombre de la tarjeta si es crédito
                        is_paid BOOLEAN DEFAULT 1,    -- 1=Pagado, 0=Deuda
                        due_date TIMESTAMP,           -- Fecha límite de pago
                        origin_state TEXT,            -- Estado de origen (USA)
                        tax_percentage REAL DEFAULT 0, -- Porcentaje de impuesto
                        FOREIGN KEY (product_id) REFERENCES products(id),
                        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                    )
                """)

                # Migración manual por si la tabla ya existe sin las columnas nuevas
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN card_name TEXT")
                except: pass
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN is_paid BOOLEAN DEFAULT 1")
                except: pass
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN due_date TIMESTAMP")
                except: pass
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN origin_state TEXT")
                except: pass
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN tax_percentage REAL DEFAULT 0")
                except: pass
                try:
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
                except: pass

                # Tabla de Ventas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticket_number TEXT UNIQUE NOT NULL,
                        total_amount REAL NOT NULL,
                        payment_method TEXT NOT NULL,
                        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT,
                        caja_id INTEGER,
                        FOREIGN KEY (caja_id) REFERENCES cajas(id)
                    )
                """)
                # Add caja_id to sales if it doesn't exist
                try:
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
                except: pass
                
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN combo_reference TEXT")
                except: pass
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN combo_name TEXT")
                except: pass
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN distribution_method TEXT")
                except: pass
                # Add total to sales if it doesn't exist (from the diff, it seems total_amount is used, but the diff also adds 'total')
                # Assuming 'total_amount' is the intended 'total' and no new 'total' column is needed if 'total_amount' exists.
                # If 'total' is meant to be a separate column, it should be added here.
                # For now, I'll assume total_amount covers it, and the diff's 'total REAL NOT NULL' was a mistake or redundancy.
                # If the user truly wants a separate 'total' column, they should clarify.
                # Given the diff's `total REAL NOT NULL` and `total_amount REAL NOT NULL`, I'll assume `total_amount` is the primary total.
                # The diff's `add_sale` uses `total` as a parameter, which maps to `total_amount` in the existing table.

                # Tabla de Sesiones de Caja
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cajas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monto_inicial REAL NOT NULL,
                        fecha_apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        fecha_cierre TIMESTAMP,
                        estado TEXT DEFAULT 'abierta',
                        diferencia REAL DEFAULT 0,
                        resumen_json TEXT
                    )
                """)

                # Tabla de Movimientos de Caja
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS movimientos_caja (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        caja_id INTEGER NOT NULL,
                        tipo TEXT NOT NULL, -- 'ingreso' o 'retiro'
                        monto REAL NOT NULL,
                        motivo TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (caja_id) REFERENCES cajas(id)
                    )
                """)

                # Tabla de Detalles de Venta
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sale_details (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sale_id INTEGER NOT NULL,
                        product_id INTEGER NOT NULL,
                        quantity INTEGER NOT NULL,
                        price_at_sale REAL NOT NULL,
                        FOREIGN KEY (sale_id) REFERENCES sales(id),
                        FOREIGN KEY (product_id) REFERENCES products(id)
                    )
                """)

                # Tabla de Tarjetas de Crédito
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS credit_cards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL
                    )
                """)

                # Insertar tarjetas por defecto si no existen
                cursor.execute("INSERT OR IGNORE INTO credit_cards (name) VALUES ('Visa - 1234'), ('MasterCard - 5678'), ('Amex - 9012')")

                # Tabla de Categorías
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL
                    )
                """)

                # Insertar categorías por defecto si no existen
                cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES ('Herramientas'), ('Accesorios'), ('Ferretería'), ('General')")
                
                # Tabla de Personal
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS personnel (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL
                    )
                """)

                # Insertar personal por defecto si no existe
                cursor.execute("INSERT OR IGNORE INTO personnel (name) VALUES ('David'), ('Stacey'), ('Dueño'), ('Encargado')")

                conn.commit()
                print("Base de datos inicializada correctamente.")
        except sqlite3.Error as e:
            print(f"Error al inicializar la base de datos: {e}")

    def backup_db(self):
        """Crea una copia de seguridad de la base de datos en una carpeta 'backups'."""
        if not os.path.exists("backups"):
            os.makedirs("backups")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backups/provision_backup_{timestamp}.db"
        
        try:
            shutil.copy2(self.db_path, backup_name)
            print(f"Backup creado: {backup_name}")
            return backup_name
        except Exception as e:
            print(f"Error al crear backup: {e}")
            return None

    def get_sales_data(self, days=30):
        """Obtiene ventas diarias en el rango de días especificado."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT date(sales.date) as day, SUM(total_amount) 
                    FROM sales 
                    WHERE sales.date >= date('now', ?)
                    GROUP BY day 
                    ORDER BY day
                """, (f'-{days} days',))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener datos de ventas: {e}")
            return []

    def get_investment_data(self):
        """Calcula la inversión total actual (stock * costo)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(current_stock * cost_price) FROM products")
                result = cursor.fetchone()[0]
                return result if result else 0.0
        except sqlite3.Error as e:
            print(f"Error al obtener inversión: {e}")
            return 0.0

    def get_debts_total(self):
        """Obtiene la deuda total de compras no pagadas."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(total_cost) FROM purchases WHERE is_paid = 0")
                result = cursor.fetchone()[0]
                return result if result else 0.0
        except sqlite3.Error as e:
            print(f"Error al obtener deuda total: {e}")
            return 0.0

    def get_debts_by_card(self):
        """Obtiene el desglose de deudas resumido por tarjeta de crédito."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT card_name, SUM(total_cost) 
                    FROM purchases 
                    WHERE payment_method = 'Credit' AND is_paid = 0 
                    GROUP BY card_name
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener deudas por tarjeta: {e}")
            return []

    def get_top_sold_products(self, limit=5):
        """Obtiene los productos más vendidos históricamente."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.name, SUM(sd.quantity) as total_qty
                    FROM sale_details sd
                    JOIN products p ON sd.product_id = p.id
                    GROUP BY p.id
                    ORDER BY total_qty DESC
                    LIMIT ?
                """, (limit,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener top productos: {e}")
            return []

    def get_top_sold_product_week(self):
        """Obtiene el producto más vendido en los últimos 7 días."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.name, SUM(sd.quantity) as total_qty
                    FROM sale_details sd
                    JOIN sales s ON sd.sale_id = s.id
                    JOIN products p ON sd.product_id = p.id
                    WHERE s.date >= date('now', '-7 days')
                    GROUP BY p.id
                    ORDER BY total_qty DESC
                    LIMIT 1
                """)
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error al obtener top semanal: {e}")
            return None

    def get_financial_health_data(self):
        """Inversión (Compras) vs Ventas vs Ganancia."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Total Compras (Inversión)
                cursor.execute("SELECT SUM(total_cost) FROM purchases")
                purchases = cursor.fetchone()[0] or 0.0
                # Total Ventas
                cursor.execute("SELECT SUM(total_amount) FROM sales")
                sales = cursor.fetchone()[0] or 0.0
                return purchases, sales
        except sqlite3.Error as e:
            print(f"Error al obtener salud financiera: {e}")
            return 0.0, 0.0

    def get_profit_data(self, days=7):
        """Calcula ganancia estimada (Venta - Costo) en un periodo."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT SUM((sd.price_at_sale - p.cost_price) * sd.quantity)
                    FROM sale_details sd
                    JOIN products p ON sd.product_id = p.id
                    JOIN sales s ON sd.sale_id = s.id
                    WHERE s.date >= date('now', ?)
                """, (f'-{days} days',))
                result = cursor.fetchone()[0]
                return result if result else 0.0
        except sqlite3.Error as e:
            print(f"Error al calcular ganancia: {e}")
            return 0.0

    def get_monthly_profits(self, months=6):
        """Obtiene historial de ganancias por mes."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT strftime('%Y-%m', s.date) as month, 
                           SUM((sd.price_at_sale - p.cost_price) * sd.quantity) as profit
                    FROM sale_details sd
                    JOIN products p ON sd.product_id = p.id
                    JOIN sales s ON sd.sale_id = s.id
                    WHERE s.date >= date('now', ?)
                    GROUP BY month
                    ORDER BY month ASC
                """, (f'-{months} months',))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener ganancias mensuales: {e}")
            return []

    def get_detailed_debts(self):
        """Obtiene el listado detallado de todas las deudas (pagadas y pendientes) con fecha."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.id, p.date, pr.name, p.total_cost, p.card_name, p.is_paid, p.due_date
                    FROM purchases p
                    JOIN products pr ON p.product_id = pr.id
                    WHERE p.payment_method = 'Credit'
                    ORDER BY p.date DESC
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener deudas detalladas: {e}")
            return []

    def get_upcoming_debts(self):
        """Obtiene deudas que vencen en las próximas 24 horas."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pr.name, p.total_cost, p.due_date 
                    FROM purchases p
                    JOIN products pr ON p.product_id = pr.id
                    WHERE p.is_paid = 0 AND p.due_date IS NOT NULL 
                    AND p.due_date <= date('now', '+1 day')
                    AND p.due_date >= date('now')
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener deudas próximas: {e}")
            return []

    def mark_purchase_as_paid(self, purchase_id):
        """Marca una compra a crédito como pagada."""
        return self.set_purchase_paid_status(purchase_id, 1)

    def set_purchase_paid_status(self, purchase_id, status):
        """Cambia el estado de pago de una compra (1=Pagado, 0=Pendiente)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE purchases SET is_paid = ? WHERE id = ?", (status, purchase_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al actualizar estado de la deuda: {e}")
            return False

    def get_stock_alerts(self):
        """Obtiene productos con stock bajo o agotado."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, current_stock, min_stock FROM products WHERE current_stock <= min_stock")
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener alertas: {e}")
            return []

    def get_all_products(self):
        """Obtiene todos los productos para la tabla de inventario."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.id, p.image_path, p.sku, p.name, 
                           IFNULL((SELECT CASE WHEN combo_reference IS NOT NULL AND combo_reference != '' THEN 'Combo' ELSE 'Individual' END FROM purchases WHERE product_id = p.id AND is_return = 0 ORDER BY date DESC LIMIT 1), 'Individual') as purchase_type, 
                           p.current_stock, p.cost_price, p.selling_price, p.min_stock, p.tax_percentage,
                           IFNULL((SELECT SUM(quantity) FROM purchases WHERE product_id = p.id AND delivery_status = 'Pendiente' AND is_return = 0), 0) as incoming_stock,
                           (SELECT MIN(delivery_date) FROM purchases WHERE product_id = p.id AND delivery_status = 'Pendiente' AND is_return = 0) as next_delivery
                    FROM products p
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener productos: {e}")
            return []

    def add_product(self, sku, name, category, cost, price, min_stock, stock=0, description="", image_path=None, tax_percentage=0, marca="", modelo="", voltaje=""):
        """Inserta un nuevo producto en la base de datos."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO products (sku, name, category, cost_price, selling_price, min_stock, current_stock, description, image_path, tax_percentage, marca, modelo, voltaje)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (sku, name, category, cost, price, min_stock, stock, description, image_path, tax_percentage, marca, modelo, voltaje))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al añadir producto: {e}")
            return False

    def update_product(self, product_id, sku, name, category, cost, price, min_stock, stock, image_path=None, tax_percentage=0, marca="", modelo="", voltaje=""):
        """Actualiza un producto existente en la base de datos."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE products 
                    SET sku=?, name=?, category=?, cost_price=?, selling_price=?, min_stock=?, current_stock=?, image_path=?, tax_percentage=?, marca=?, modelo=?, voltaje=?
                    WHERE id=?
                """, (sku, name, category, cost, price, min_stock, stock, image_path, tax_percentage, marca, modelo, voltaje, product_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al actualizar producto: {e}")
            return False

    def delete_product_completely(self, product_id):
        """Elimina un producto y toda la información relacionada (compras, detalles de venta)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Eliminar detalles de venta relacionados
                cursor.execute("DELETE FROM sale_details WHERE product_id = ?", (product_id,))
                # Eliminar compras relacionadas
                cursor.execute("DELETE FROM purchases WHERE product_id = ?", (product_id,))
                # Eliminar el producto
                cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al eliminar producto completamente: {e}")
            return False

    def get_product_by_sku_or_name(self, query):
        """Busca un producto por SKU (exacto/insensible) o nombre parcial, marca o modelo."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, cost_price, selling_price, sku 
                    FROM products 
                    WHERE UPPER(sku) = UPPER(?) OR name LIKE ? OR marca LIKE ? OR modelo LIKE ?
                """, (query, f"%{query}%", f"%{query}%", f"%{query}%"))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error al buscar producto: {e}")
            return None

    def search_products(self, query, limit=15):
        """Busca múltiples productos que coincidan parcialmente por SKU, nombre, marca o modelo (para autocompletado)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT sku, name, cost_price, tax_percentage, selling_price 
                    FROM products 
                    WHERE sku LIKE ? OR name LIKE ? OR marca LIKE ? OR modelo LIKE ?
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al buscar productos: {e}")
            return []

    def add_purchase(self, product_id, qty, unit_cost, supplier_id, payment_method, buyer_tag, 
                     is_return=0, card_name=None, is_paid=1, due_date=None, 
                     origin_state=None, tax_percentage=0, new_selling_price=None,
                     purchase_type='Física', delivery_date=None, delivery_status='Entregado'):
        """
        Registra una compra, actualiza el stock y opcionalmente el precio de venta del producto.
        El costo total incluye el impuesto aplicado.
        """
        # Calcular costo total con impuesto
        base_cost = qty * unit_cost
        tax_amount = base_cost * (tax_percentage / 100.0)
        total_cost_with_tax = base_cost + tax_amount

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # 1. Insertar compra
                cursor.execute("""
                    INSERT INTO purchases (
                        product_id, quantity, unit_cost, total_cost, supplier_id, 
                        payment_method, buyer_tag, is_return, card_name, is_paid, 
                        due_date, origin_state, tax_percentage, purchase_type, delivery_date, delivery_status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (product_id, qty, unit_cost, total_cost_with_tax, supplier_id, 
                      payment_method, buyer_tag, is_return, card_name, is_paid, 
                      due_date, origin_state, tax_percentage, purchase_type, delivery_date, delivery_status))
                
                # 2. Actualizar stock
                if delivery_status != 'Pendiente':
                    stock_change = -qty if is_return else qty
                    cursor.execute("UPDATE products SET current_stock = current_stock + ? WHERE id = ?", 
                                   (stock_change, product_id))
                
                # 3. Actualizar precio de costo, impuesto y opcionalmente precio de venta
                if not is_return:
                    if new_selling_price is not None:
                        cursor.execute("UPDATE products SET cost_price = ?, tax_percentage = ?, selling_price = ? WHERE id = ?", 
                                       (unit_cost, tax_percentage, new_selling_price, product_id))
                    else:
                        cursor.execute("UPDATE products SET cost_price = ?, tax_percentage = ? WHERE id = ?", 
                                       (unit_cost, tax_percentage, product_id))
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al registrar compra: {e}")
            return False



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

    def add_sale(self, total_amount, payment_method, items, caja_id=None, notes=None, customer_id=None, discount=0.0):
        """
        Registra una venta completa.
        items: Lista de tuplas (product_id, quantity, price)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Generar ticket más simple
                cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='sales'")
                seq_row = cursor.fetchone()
                next_id = (seq_row[0] + 1) if seq_row else 1
                ticket_number = f"TK-{next_id:06d}"
                
                # 2. Insertar venta principal
                cursor.execute("""
                    INSERT INTO sales (ticket_number, total_amount, payment_method, caja_id, notes, customer_id, discount_applied)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (ticket_number, total_amount, payment_method, caja_id, notes, customer_id, discount))
                sale_id = cursor.lastrowid
                
                # 3. Insertar detalles y actualizar stock
                for p_id, qty, price in items:
                    cursor.execute("""
                        INSERT INTO sale_details (sale_id, product_id, quantity, price_at_sale)
                        VALUES (?, ?, ?, ?)
                    """, (sale_id, p_id, qty, price))
                    
                    cursor.execute("""
                        UPDATE products SET current_stock = current_stock - ? WHERE id = ?
                    """, (qty, p_id))
                
                conn.commit()
                return ticket_number
        except sqlite3.Error as e:
            print(f"Error al registrar venta: {e}")
            return None

    # Métodos para Proveedores
    def get_all_suppliers(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM suppliers ORDER BY name")
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener proveedores: {e}")
            return []

    def add_supplier(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO suppliers (name) VALUES (?)", (name,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al añadir proveedor: {e}")
            return False

    def delete_supplier(self, supplier_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al eliminar proveedor: {e}")
            return False

    # Métodos para Tarjetas de Crédito
    def get_all_credit_cards(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM credit_cards ORDER BY name")
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener tarjetas: {e}")
            return []

    def add_credit_card(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO credit_cards (name) VALUES (?)", (name,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al añadir tarjeta: {e}")
            return False

    def delete_credit_card(self, card_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM credit_cards WHERE id = ?", (card_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al eliminar tarjeta: {e}")
            return False

    # Métodos para Categorías
    def get_all_categories(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM categories ORDER BY name")
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener categorías: {e}")
            return []

    def add_category(self, name):
        """Añade una nueva categoría."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al añadir categoría: {e}")
            return False

    def get_all_brand_prefixes(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, brand, prefix FROM brand_prefixes ORDER BY brand")
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener prefijos: {e}")
            return []

    def add_brand_prefix(self, brand, prefix):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO brand_prefixes (brand, prefix) VALUES (?, ?)", (brand.strip().upper(), prefix.strip().upper()))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al añadir prefijo de marca: {e}")
            return False

    def delete_brand_prefix(self, prefix_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM brand_prefixes WHERE id = ?", (prefix_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            return False

    def get_prefix_for_brand(self, brand):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT prefix FROM brand_prefixes WHERE UPPER(brand) = UPPER(?)", (brand.strip(),))
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            return None

    def get_next_sku_sequence(self, prefix):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT sku FROM products WHERE UPPER(sku) LIKE ?", (f"{prefix.upper()}%",))
                results = cursor.fetchall()
                max_seq = 0
                for row in results:
                    sku = row[0]
                    if sku.upper().startswith(prefix.upper()):
                        num_part = sku[len(prefix):]
                        if num_part.isdigit():
                            max_seq = max(max_seq, int(num_part))
                
                next_seq = max_seq + 1
                return f"{prefix.upper()}{next_seq:07d}"
        except sqlite3.Error as e:
            print(f"Error calculando secuencia de SKU: {e}")
            return f"{prefix.upper()}0000001"

    def delete_category(self, category_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al eliminar categoría: {e}")
            return False

    # Métodos para Personal (Responsables)
    def get_all_personnel(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM personnel ORDER BY name")
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener personal: {e}")
            return []

    def add_personnel(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO personnel (name) VALUES (?)", (name,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al añadir personal: {e}")
            return False

    def delete_personnel(self, personnel_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM personnel WHERE id = ?", (personnel_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al eliminar personal: {e}")
            return False

    # --- MÉTODOS DE CAJA ---
    def get_open_caja(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM cajas WHERE estado = 'abierta' LIMIT 1")
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error al obtener caja abierta: {e}")
            return None

    def open_caja(self, monto_inicial):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO cajas (monto_inicial) VALUES (?)", (monto_inicial,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al abrir caja: {e}")
            return False

    def add_caja_movement(self, caja_id, tipo, monto, motivo):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO movimientos_caja (caja_id, tipo, monto, motivo) VALUES (?, ?, ?, ?)",
                               (caja_id, tipo, monto, motivo))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al agregar movimiento: {e}")
            return False

    def close_caja(self, caja_id, diferencia, resumen_json):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE cajas 
                    SET fecha_cierre = CURRENT_TIMESTAMP, estado = 'cerrada', diferencia = ?, resumen_json = ?
                    WHERE id = ?
                """, (diferencia, resumen_json, caja_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al cerrar caja: {e}")
            return False

    def get_caja_totals(self, caja_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Ventas por método de pago
                cursor.execute("SELECT payment_method, SUM(total_amount) FROM sales WHERE caja_id = ? GROUP BY payment_method", (caja_id,))
                sales_summary = dict(cursor.fetchall())
                
                # Movimientos (ingresos/retiros)
                cursor.execute("SELECT tipo, SUM(monto) FROM movimientos_caja WHERE caja_id = ? GROUP BY tipo", (caja_id,))
                movements_summary = dict(cursor.fetchall())
                
                return {
                    'sales': sales_summary,
                    'movements': movements_summary
                }
        except sqlite3.Error as e:
            print(f"Error al obtener totales de caja: {e}")
            return None

    def get_caja_sales(self, caja_id):
        """Obtiene todas las ventas realizadas en una caja específica."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.date, s.ticket_number, IFNULL(c.name, 'Mostrador'), s.discount_applied, s.payment_method, s.total_amount 
                    FROM sales s
                    LEFT JOIN customers c ON s.customer_id = c.id
                    WHERE s.caja_id = ? 
                    ORDER BY s.date DESC
                """, (caja_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener ventas de caja: {e}")
            return []

    def get_sale_details_by_ticket(self, ticket_number):
        """Obtiene los detalles de los productos de un ticket específico."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.sku, p.name, sd.quantity, sd.price_at_sale
                    FROM sale_details sd
                    JOIN sales s ON sd.sale_id = s.id
                    JOIN products p ON sd.product_id = p.id
                    WHERE s.ticket_number = ?
                """, (ticket_number,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener detalles del ticket: {e}")
            return []

    def get_full_ticket_data(self, ticket_number):
        """Retorna todos los datos de un ticket (cabecera y detalles) para impresión."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener cabecera
                cursor.execute("""
                    SELECT s.ticket_number, s.date, s.total_amount, s.payment_method, 
                           s.discount_applied, IFNULL(c.name, 'Mostrador')
                    FROM sales s
                    LEFT JOIN customers c ON s.customer_id = c.id
                    WHERE s.ticket_number = ?
                """, (ticket_number,))
                header = cursor.fetchone()
                
                if not header:
                    return None
                    
                # Obtener detalles
                cursor.execute("""
                    SELECT p.name, sd.quantity, sd.price_at_sale, (sd.quantity * sd.price_at_sale) as importe
                    FROM sale_details sd
                    JOIN sales s ON sd.sale_id = s.id
                    JOIN products p ON sd.product_id = p.id
                    WHERE s.ticket_number = ?
                """, (ticket_number,))
                details = cursor.fetchall()
                
                return {
                    "ticket": header[0],
                    "fecha": header[1],
                    "total": header[2],
                    "metodo_pago": header[3],
                    "descuento": header[4],
                    "cliente": header[5],
                    "items": details
                }
        except sqlite3.Error as e:
            print(f"Error al obtener data completa del ticket: {e}")
            return None

    def get_daily_sales_summary(self, filter_type='all'):
        """Obtiene un resumen de ventas agrupado por día, con filtro opcional."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT 
                        date(date) as day, 
                        COUNT(id) as total_tickets,
                        SUM(CASE WHEN payment_method='Efectivo' THEN total_amount ELSE 0 END) as efectivo,
                        SUM(CASE WHEN payment_method='Tarjeta' THEN total_amount ELSE 0 END) as tarjeta,
                        SUM(total_amount) as total
                    FROM sales 
                """
                
                params = []
                if filter_type == 'week':
                    query += " WHERE date >= date('now', '-7 days')"
                elif filter_type == 'month':
                    query += " WHERE date >= date('now', '-1 month')"
                elif filter_type == 'today':
                    query += " WHERE date(date) = date('now', 'localtime')"
                    
                query += " GROUP BY day ORDER BY day DESC"
                
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener resumen de ventas diario: {e}")
            return []

    def get_caja_history(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM cajas ORDER BY fecha_apertura DESC")
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener historial de caja: {e}")
            return []


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

    db = DatabaseManager()
    db.backup_db()
