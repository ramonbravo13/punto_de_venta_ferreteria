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
                        purchase_type TEXT DEFAULT 'Física', -- Física, En Línea
                        delivery_date TIMESTAMP,
                        delivery_status TEXT DEFAULT 'Entregado',
                        shipping_cost REAL DEFAULT 0.0,
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
                try:
                    cursor.execute("ALTER TABLE purchases ADD COLUMN shipping_cost REAL DEFAULT 0.0")
                except: pass

                # --- NUEVAS TABLAS FASE B ---
                # Tabla de Órdenes de Compra
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS purchase_orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_number TEXT UNIQUE,
                        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        supplier_id INTEGER NOT NULL,
                        purchase_type TEXT DEFAULT 'Tienda', -- Tienda, Online, Marketplace
                        marketplace_name TEXT,
                        seller_name TEXT,
                        tracking_number TEXT,
                        shipping_provider TEXT,
                        status TEXT DEFAULT 'Borrador', -- Borrador, Ordenada, Confirmada, Enviada, En_Transito, Recibida, Validada, Cancelada
                        subtotal REAL DEFAULT 0,
                        tax REAL DEFAULT 0,
                        shipping REAL DEFAULT 0,
                        total REAL DEFAULT 0,
                        estimated_delivery_date TIMESTAMP,
                        actual_delivery_date TIMESTAMP,
                        notes TEXT,
                        payment_method TEXT DEFAULT 'Efectivo',
                        card_id INTEGER,
                        origin_state TEXT,
                        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                    )
                """)

                # Tabla de Detalles de Orden de Compra
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS purchase_order_details (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id INTEGER NOT NULL,
                        product_id INTEGER NOT NULL,
                        ordered_quantity INTEGER NOT NULL,
                        received_quantity INTEGER DEFAULT 0,
                        original_unit_cost REAL NOT NULL,
                        allocated_tax REAL DEFAULT 0,
                        allocated_shipping REAL DEFAULT 0,
                        actual_unit_cost REAL NOT NULL,
                        combo_reference TEXT,
                        combo_name TEXT,
                        FOREIGN KEY (order_id) REFERENCES purchase_orders(id),
                        FOREIGN KEY (product_id) REFERENCES products(id)
                    )
                """)

                # Tabla de Lotes/Entradas de Inventario
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS inventory_batches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        order_detail_id INTEGER,
                        quantity INTEGER NOT NULL,
                        remaining_quantity INTEGER NOT NULL,
                        actual_unit_cost REAL NOT NULL,
                        received_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        condition TEXT DEFAULT 'Buenas Condiciones',
                        FOREIGN KEY (product_id) REFERENCES products(id),
                        FOREIGN KEY (order_detail_id) REFERENCES purchase_order_details(id)
                    )
                """)
                # -----------------------------


                # Migraciones para users Ventas
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
                        unit_cost_at_sale REAL DEFAULT 0,
                        FOREIGN KEY (sale_id) REFERENCES sales(id),
                        FOREIGN KEY (product_id) REFERENCES products(id)
                    )
                """)

                # Tabla de Tarjetas de Crédito
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS credit_cards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        cut_day INTEGER,
                        payment_day INTEGER,
                        bank TEXT,
                        last_digits TEXT,
                        credit_limit REAL DEFAULT 0,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                
                try: cursor.execute("ALTER TABLE credit_cards ADD COLUMN cut_day INTEGER")
                except sqlite3.OperationalError: pass
                try: cursor.execute("ALTER TABLE credit_cards ADD COLUMN payment_day INTEGER")
                except sqlite3.OperationalError: pass
                try: cursor.execute("ALTER TABLE credit_cards ADD COLUMN bank TEXT")
                except sqlite3.OperationalError: pass
                try: cursor.execute("ALTER TABLE credit_cards ADD COLUMN last_digits TEXT")
                except sqlite3.OperationalError: pass
                try: cursor.execute("ALTER TABLE credit_cards ADD COLUMN credit_limit REAL DEFAULT 0")
                except sqlite3.OperationalError: pass
                try: cursor.execute("ALTER TABLE credit_cards ADD COLUMN is_active BOOLEAN DEFAULT 1")
                except sqlite3.OperationalError: pass
                
                try: cursor.execute("ALTER TABLE purchase_orders ADD COLUMN payment_method TEXT DEFAULT 'Efectivo'")
                except sqlite3.OperationalError: pass
                try: cursor.execute("ALTER TABLE purchase_orders ADD COLUMN card_id INTEGER")
                except sqlite3.OperationalError: pass
                try: cursor.execute("ALTER TABLE purchase_orders ADD COLUMN origin_state TEXT")
                except sqlite3.OperationalError: pass
                
                try: cursor.execute("ALTER TABLE accounts_payable ADD COLUMN card_id INTEGER")
                except sqlite3.OperationalError: pass

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

                # Tabla de Gastos (Expenses)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        category TEXT NOT NULL,
                        description TEXT,
                        amount REAL NOT NULL,
                        tax_included BOOLEAN DEFAULT 0,
                        payment_method TEXT NOT NULL,
                        is_paid BOOLEAN DEFAULT 1
                    )
                """)

                # Tabla de Cuentas por Pagar (Accounts Payable)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS accounts_payable (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        provider_name TEXT NOT NULL,
                        description TEXT,
                        total_amount REAL NOT NULL,
                        amount_paid REAL DEFAULT 0,
                        due_date TIMESTAMP,
                        status TEXT DEFAULT 'Pendiente',
                        payment_method TEXT DEFAULT 'Efectivo',
                        card_id INTEGER,
                        shipping_cost REAL DEFAULT 0,
                        purchase_type TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Migrate existing databases
                try: cursor.execute("ALTER TABLE accounts_payable ADD COLUMN payment_method TEXT DEFAULT 'Efectivo'")
                except sqlite3.OperationalError: pass
                try: cursor.execute("ALTER TABLE accounts_payable ADD COLUMN card_name TEXT")
                except sqlite3.OperationalError: pass
                try: cursor.execute("ALTER TABLE accounts_payable ADD COLUMN shipping_cost REAL DEFAULT 0")
                except sqlite3.OperationalError: pass
                try: cursor.execute("ALTER TABLE accounts_payable ADD COLUMN purchase_type TEXT")
                except sqlite3.OperationalError: pass
                try: cursor.execute("ALTER TABLE accounts_payable ADD COLUMN payment_date TIMESTAMP")
                except sqlite3.OperationalError: pass

                conn.commit()
                print("Base de datos inicializada correctamente.")
        except sqlite3.Error as e:
            print(f"Error al inicializar la base de datos: {e}")

    def factory_reset(self):
        """Elimina todos los datos operativos pero conserva la configuración base."""
        tables_to_clear = [
            'sale_details', 'sales', 'inventory_batches', 'purchase_order_details',
            'purchase_orders', 'purchases', 'products', 'movimientos_caja',
            'cajas', 'expenses', 'accounts_payable', 'customers'
        ]
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = OFF;")
                for table in tables_to_clear:
                    try:
                        cursor.execute(f"DELETE FROM {table}")
                        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                    except sqlite3.OperationalError:
                        pass # Ignore if table doesn't exist
                conn.commit()
                cursor.execute("PRAGMA foreign_keys = ON;")
            return True, None
        except sqlite3.Error as e:
            return False, str(e)

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
                cursor.execute("SELECT SUM(remaining_quantity * actual_unit_cost) FROM inventory_batches WHERE remaining_quantity > 0")
                result = cursor.fetchone()[0]
                if result and result > 0:
                    return result
                cursor.execute("SELECT SUM(current_stock * cost_price) FROM products WHERE current_stock > 0")
                fallback = cursor.fetchone()[0]
                return fallback if fallback else 0.0
        except sqlite3.Error as e:
            print(f"Error al obtener inversión: {e}")
            return 0.0

    def get_investment_owed_data(self):
        """Devuelve cuánto del dinero invertido se debe (Cuentas por pagar pendientes)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(total_amount - amount_paid) FROM accounts_payable WHERE status = 'Pendiente'")
                result = cursor.fetchone()[0]
                return result if result else 0.0
        except sqlite3.Error as e:
            print(f"Error al calcular deuda de inversión: {e}")
            return 0.0

    def get_debts_total(self):
        """Obtiene la deuda total de compras no pagadas."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT (
                        IFNULL((SELECT SUM(total_cost) FROM purchases WHERE is_paid = 0), 0) + 
                        IFNULL((SELECT SUM(total_amount - amount_paid) FROM accounts_payable WHERE status = 'Pendiente'), 0)
                    )
                """)
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
                    SELECT card, SUM(debt) 
                    FROM (
                        SELECT IFNULL(card_name, payment_method) as card, total_cost as debt 
                        FROM purchases 
                        WHERE (payment_method = 'Credit' OR payment_method LIKE 'Tarjeta%') AND is_paid = 0 
                        
                        UNION ALL
                        
                        SELECT payment_method as card, (total_amount - amount_paid) as debt 
                        FROM accounts_payable 
                        WHERE payment_method != 'Efectivo' AND status = 'Pendiente'
                    )
                    GROUP BY card
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
                cursor.execute("""
                    SELECT (
                        IFNULL((SELECT SUM(total_cost) FROM purchases), 0) + 
                        IFNULL((SELECT SUM(total) FROM purchase_orders), 0)
                    )
                """)
                purchases = cursor.fetchone()[0] or 0.0
                # Total Ventas
                cursor.execute("SELECT SUM(total_amount) FROM sales")
                sales = cursor.fetchone()[0] or 0.0
                return purchases, sales
        except sqlite3.Error as e:
            print(f"Error al obtener salud financiera: {e}")
            return 0.0, 0.0

    def get_profit_data(self, period="month"):
        """Calcula ganancia estimada (Venta - Costo c/Imp) en un periodo."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if period == "today":
                    date_filter = "date(s.date) = date('now', 'localtime')"
                elif period == "week":
                    date_filter = "s.date >= date('now', '-7 days', 'localtime')"
                else:
                    date_filter = "s.date >= date('now', '-30 days', 'localtime')"
                    
                query = f"""
                    SELECT SUM(
                        (sd.price_at_sale - sd.unit_cost_at_sale) * sd.quantity
                    )
                    FROM sale_details sd
                    JOIN products p ON sd.product_id = p.id
                    JOIN sales s ON sd.sale_id = s.id
                    WHERE {date_filter}
                """
                cursor.execute(query)
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
                           SUM((sd.price_at_sale - COALESCE(sd.unit_cost_at_sale, p.cost_price)) * sd.quantity) as profit
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
        """Obtiene el listado detallado de todas las deudas (pagadas y pendientes) combinando cuentas por pagar y compras a crédito."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        'ap_' || a.id as unique_id,
                        a.created_at as debt_date,
                        COALESCE(a.description, a.provider_name) as concept,
                        a.total_amount as amount,
                        COALESCE(c.name, a.card_name, a.payment_method) as card_or_method,
                        CASE WHEN a.status = 'Pagado' THEN 1 ELSE 0 END as is_paid,
                        a.due_date as due_date,
                        'ap' as source_type,
                        a.id as raw_id
                    FROM accounts_payable a
                    LEFT JOIN credit_cards c ON a.card_id = c.id
                    
                    UNION ALL
                    
                    SELECT 
                        'p_' || p.id as unique_id,
                        p.date as debt_date,
                        pr.name as concept,
                        p.total_cost as amount,
                        p.card_name as card_or_method,
                        p.is_paid as is_paid,
                        p.due_date as due_date,
                        'p' as source_type,
                        p.id as raw_id
                    FROM purchases p
                    JOIN products pr ON p.product_id = pr.id
                    WHERE (p.payment_method = 'Credit' OR p.payment_method LIKE 'Tarjeta%' OR p.is_paid = 0)
                    
                    ORDER BY debt_date DESC
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
                           IFNULL((SELECT MAX(c) FROM (SELECT (total_cost * 1.0 / quantity) as c FROM purchases WHERE product_id = p.id AND quantity > 0 UNION SELECT actual_unit_cost as c FROM purchase_order_details WHERE product_id = p.id)), p.cost_price * (1 + p.tax_percentage / 100.0)) as max_cost,
                           (
                               IFNULL((SELECT SUM(quantity) FROM purchases WHERE product_id = p.id AND delivery_status = 'Pendiente' AND is_return = 0), 0) +
                               IFNULL((SELECT SUM(pod.ordered_quantity - pod.received_quantity) FROM purchase_order_details pod JOIN purchase_orders po ON pod.order_id = po.id WHERE pod.product_id = p.id AND po.status LIKE 'Pendiente%'), 0)
                           ) as incoming_stock,
                           (
                               SELECT MIN(d) FROM (
                                   SELECT delivery_date as d FROM purchases WHERE product_id = p.id AND delivery_status = 'Pendiente' AND is_return = 0
                                   UNION
                                   SELECT po.estimated_delivery_date as d FROM purchase_order_details pod JOIN purchase_orders po ON pod.order_id = po.id WHERE pod.product_id = p.id AND po.status LIKE 'Pendiente%'
                               )
                           ) as next_delivery,
                           p.marca, p.modelo, p.voltaje,
                           IFNULL((SELECT SUM(quantity) FROM purchases WHERE product_id = p.id AND is_return = 0 AND (combo_reference IS NOT NULL AND combo_reference != '')), 0) as combo_qty,
                           IFNULL((SELECT SUM(quantity) FROM purchases WHERE product_id = p.id AND is_return = 0 AND (combo_reference IS NULL OR combo_reference = '')), 0) as indiv_qty
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
                cursor.execute("DELETE FROM inventory_batches WHERE product_id = ?", (product_id,))
                cursor.execute("DELETE FROM purchase_order_details WHERE product_id = ?", (product_id,))
                cursor.execute("DELETE FROM purchases WHERE product_id = ?", (product_id,))
                cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al eliminar producto completamente: {e}")
            return False

    def delete_product(self, product_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al eliminar producto: {e}")
            return False

    def get_product_batches(self, product_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, remaining_quantity, actual_unit_cost, received_date
                    FROM inventory_batches
                    WHERE product_id = ? AND remaining_quantity > 0
                    ORDER BY received_date ASC
                """, (product_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener lotes del producto {product_id}: {e}")
            return []

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

    def get_product_for_pos(self, query):
        """Busca un producto y devuelve stock actual y costo máximo histórico (para POS)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, cost_price, selling_price, sku, current_stock,
                           IFNULL((SELECT MAX(c) FROM (
                               SELECT (total_cost * 1.0 / quantity) as c FROM purchases WHERE product_id = products.id AND quantity > 0
                               UNION 
                               SELECT actual_unit_cost as c FROM purchase_order_details WHERE product_id = products.id
                           )), cost_price) as max_cost
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
                    SELECT sku, name, cost_price, tax_percentage, selling_price, marca, modelo 
                    FROM products 
                    WHERE sku LIKE ? OR name LIKE ? OR marca LIKE ? OR modelo LIKE ?
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al buscar productos: {e}")
            return []

    def create_purchase_order(self, order_number, supplier_id, purchase_type,
                              marketplace_name=None, seller_name=None, tracking_number=None,
                              shipping_provider=None, status='Borrador',
                              subtotal=0, tax=0, shipping=0, total=0,
                              estimated_delivery_date=None, notes=None, payment_method='Efectivo', card_id=None,
                              origin_state=None):
        """Crea una nueva orden de compra."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO purchase_orders (
                        order_number, supplier_id, purchase_type, marketplace_name,
                        seller_name, tracking_number, shipping_provider, status,
                        subtotal, tax, shipping, total, estimated_delivery_date, notes,
                        payment_method, card_id, origin_state
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (order_number, supplier_id, purchase_type, marketplace_name,
                      seller_name, tracking_number, shipping_provider, status,
                      subtotal, tax, shipping, total, estimated_delivery_date, notes, payment_method, card_id, origin_state))
                order_id = cursor.lastrowid
                
                # FASE I: Generar registro financiero unificado INMEDIATAMENTE al crear orden
                cursor.execute("SELECT name FROM suppliers WHERE id = ?", (supplier_id,))
                supp_row = cursor.fetchone()
                supplier_name = supp_row[0] if supp_row else f"Proveedor {supplier_id}"
                
                track_desc = f" (Tracking: {tracking_number})" if tracking_number else ""
                desc = f"Orden de Compra {order_id}{track_desc}"
                
                from datetime import datetime
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                if payment_method == "A crédito":
                    cursor.execute("""
                        INSERT INTO accounts_payable (provider_name, description, total_amount, status, purchase_type, payment_method, card_id, created_at)
                        VALUES (?, ?, ?, 'Pendiente', ?, ?, ?, ?)
                    """, (supplier_name, desc, total, purchase_type, payment_method, card_id, now_str))
                elif payment_method == "Tarjeta":
                    cursor.execute("""
                        INSERT INTO accounts_payable (provider_name, description, total_amount, amount_paid, status, purchase_type, payment_method, card_id, created_at, payment_date)
                        VALUES (?, ?, ?, ?, 'Pagado', ?, ?, ?, ?, ?)
                    """, (supplier_name, desc, total, total, purchase_type, payment_method, card_id, now_str, now_str))
                else:
                    cursor.execute("""
                        INSERT INTO expenses (category, description, amount, payment_method, tax_included, is_paid, date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, ("Compra de Inventario", f"Compra a {supplier_name} - {desc}", total, payment_method, 0, 1, now_str))
                
                conn.commit()
                return order_id
        except sqlite3.Error as e:
            print(f"Error al crear orden de compra: {e}")
            return None

    def add_purchase_order_details(self, order_id, items, total_tax=0, total_shipping=0):
        """
        Agrega detalles a una orden de compra, distribuyendo impuestos y envío (FASE E).
        items: [{'product_id': id, 'quantity': q, 'unit_cost': c, 'combo_ref': ref, 'combo_name': name}]
        """
        try:
            # Calcular subtotal total para distribución ponderada
            subtotal = sum(item['quantity'] * item['unit_cost'] for item in items)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for item in items:
                    p_id = item['product_id']
                    qty = item['quantity']
                    u_cost = item['unit_cost']
                    total_p_cost = qty * u_cost
                    
                    weight = (total_p_cost / subtotal) if subtotal > 0 else (1.0 / len(items))
                    
                    allocated_tax = total_tax * weight
                    allocated_shipping = total_shipping * weight
                    
                    actual_unit_cost = (total_p_cost + allocated_tax + allocated_shipping) / qty if qty > 0 else u_cost
                    
                    cursor.execute("""
                        INSERT INTO purchase_order_details (
                            order_id, product_id, ordered_quantity, original_unit_cost,
                            allocated_tax, allocated_shipping, actual_unit_cost,
                            combo_reference, combo_name
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (order_id, p_id, qty, u_cost, allocated_tax, allocated_shipping,
                          actual_unit_cost, item.get('combo_ref'), item.get('combo_name')))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al agregar detalles de orden: {e}")
            return False

    def update_purchase_order_status(self, order_id, new_status, received_items=None, payment_method='Efectivo', is_paid=False):
        """
        Actualiza el estado (FASE F). Si new_status == 'Recibida', genera inventory_batches (FASE G)
        y actualiza finanzas sin modificar precio de venta ni costo histórico (FASE H).
        received_items: [{'detail_id': id, 'received_qty': q, 'condition': c, 'product_id': p_id, 'actual_unit_cost': c}]
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if new_status == 'Recibida' and received_items:
                    cursor.execute("SELECT status FROM purchase_orders WHERE id = ?", (order_id,))
                    current_status = cursor.fetchone()[0]
                    
                    if current_status != 'Recibida':
                        for item in received_items:
                            detail_id = item['detail_id']
                            rec_qty = item['received_qty']
                            condition = item.get('condition', 'Buenas Condiciones')
                            p_id = item['product_id']
                            act_cost = item['actual_unit_cost']
                            
                            # Update received quantity in details
                            cursor.execute("""
                                UPDATE purchase_order_details 
                                SET received_quantity = ? 
                                WHERE id = ?
                            """, (rec_qty, detail_id))
                            
                            # Create batch (FASE G)
                            if rec_qty > 0:
                                cursor.execute("""
                                    INSERT INTO inventory_batches (
                                        product_id, order_detail_id, quantity, remaining_quantity,
                                        actual_unit_cost, condition
                                    ) VALUES (?, ?, ?, ?, ?, ?)
                                """, (p_id, detail_id, rec_qty, rec_qty, act_cost, condition))
                                
                                # Update total stock in products (we preserve existing architecture)
                                cursor.execute("UPDATE products SET current_stock = current_stock + ? WHERE id = ?", 
                                            (rec_qty, p_id))
                                
                                # NO actualizamos selling_price ni sobrescribimos cost_price de forma obligatoria aquí.
                        # Eliminar generacion de finanzas de FASE I, ya se hizo al momento de la compra
                        
                        # Registrar fecha de recepción
                        cursor.execute("UPDATE purchase_orders SET actual_delivery_date = CURRENT_TIMESTAMP WHERE id = ?", (order_id,))

                cursor.execute("UPDATE purchase_orders SET status = ? WHERE id = ?", (new_status, order_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al actualizar estado de la orden: {e}")
            return False

    def get_purchase_orders(self, status=None, limit=50):
        """Obtiene las órdenes de compra, opcionalmente filtradas por estado."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT po.id, po.order_number, po.date, s.name, po.purchase_type, 
                           po.status, po.total, po.tracking_number, po.origin_state
                    FROM purchase_orders po
                    JOIN suppliers s ON po.supplier_id = s.id
                """
                params = []
                if status:
                    query += " WHERE po.status = ?"
                    params.append(status)
                query += " ORDER BY po.date DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener órdenes de compra: {e}")
            return []

    def get_purchase_order_by_id(self, order_id):
        """Obtiene una orden de compra por su ID interno."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT po.id, po.order_number, po.date, s.name, po.purchase_type, 
                           po.status, po.total, po.tracking_number, po.origin_state
                    FROM purchase_orders po
                    JOIN suppliers s ON po.supplier_id = s.id
                    WHERE po.id = ?
                """, (order_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error al obtener orden de compra: {e}")
            return None

    def get_purchase_order_details(self, order_id):
        """Obtiene los detalles (artículos) de una orden de compra."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pod.id, pod.product_id, p.name, p.sku, pod.ordered_quantity, 
                           pod.received_quantity, pod.original_unit_cost, pod.actual_unit_cost,
                           pod.combo_reference, pod.combo_name
                    FROM purchase_order_details pod
                    JOIN products p ON pod.product_id = p.id
                    WHERE pod.order_id = ?
                """, (order_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener detalles de la orden: {e}")
            return []

    def delete_purchase_order(self, order_id):
        """Elimina una orden de compra y sus detalles. Útil para rollbacks."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM purchase_order_details WHERE order_id = ?", (order_id,))
                cursor.execute("DELETE FROM purchase_orders WHERE id = ?", (order_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al eliminar orden de compra: {e}")
            return False

    def add_purchase(self, product_id, qty, unit_cost, supplier_id, payment_method, buyer_tag, 
                     origin_state=None, tax_percentage=0, new_selling_price=None,
                     purchase_type='Física', delivery_date=None, delivery_status='Entregado',
                     shipping_cost=0.0):
        """
        Registra una compra, actualiza el stock y opcionalmente el precio de venta del producto.
        El costo total incluye el impuesto aplicado.
        """
        # Calcular costo total con impuesto. El costo de envío no afecta el costo unitario para la venta.
        base_cost = qty * unit_cost
        tax_amount = base_cost * (tax_percentage / 100.0)
        total_cost_with_tax = base_cost + tax_amount
        total_debt_or_expense = total_cost_with_tax + shipping_cost
        # Costo unitario real sin envío
        actual_unit_cost = (total_cost_with_tax / qty) if qty > 0 else unit_cost

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # 1. Insertar compra
                cursor.execute("""
                    INSERT INTO purchases (
                        product_id, quantity, unit_cost, total_cost, supplier_id, 
                        payment_method, buyer_tag, is_return, card_name, is_paid, 
                        due_date, origin_state, tax_percentage, purchase_type, delivery_date, delivery_status, shipping_cost
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (product_id, qty, actual_unit_cost, total_cost_with_tax, supplier_id, 
                      payment_method, buyer_tag, is_return, card_name, is_paid, 
                      due_date, origin_state, tax_percentage, purchase_type, delivery_date, delivery_status, shipping_cost))
                
                # 2. Actualizar stock
                if delivery_status != 'Pendiente':
                    stock_change = -qty if is_return else qty
                    cursor.execute("UPDATE products SET current_stock = current_stock + ? WHERE id = ?", 
                                   (stock_change, product_id))
                
                # 3. Actualizar impuesto y opcionalmente precio de venta (FASE H: NO sobrescribir costo)
                if not is_return:
                    if new_selling_price is not None:
                        # Se cambia por acción explícita
                        cursor.execute("UPDATE products SET tax_percentage = ?, selling_price = ? WHERE id = ?", 
                                       (tax_percentage, new_selling_price, product_id))
                    else:
                        cursor.execute("UPDATE products SET tax_percentage = ? WHERE id = ?", 
                                       (tax_percentage, product_id))

                    # 4. Integrar con Finanzas (Gastos / Cuentas por Pagar)
                    cursor.execute("SELECT name FROM suppliers WHERE id = ?", (supplier_id,))
                    supp_row = cursor.fetchone()
                    supplier_name = supp_row[0] if supp_row else f"Proveedor {supplier_id}"

                    desc_extra = f" - Tarjeta: {card_name}" if card_name else ""
                    if is_paid:
                        cursor.execute("""
                            INSERT INTO expenses (category, description, amount, payment_method, tax_included, is_paid)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, ("Compra de Inventario", f"Compra a {supplier_name}{desc_extra}", total_debt_or_expense, payment_method, int(tax_percentage > 0), 1))
                    else:
                        cursor.execute("""
                            INSERT INTO accounts_payable (provider_name, description, total_amount, due_date, status, payment_method, card_name, shipping_cost, purchase_type)
                            VALUES (?, ?, ?, ?, 'Pendiente', ?, ?, ?, ?)
                        """, (supplier_name, "Compra de Inventario", total_debt_or_expense, due_date, payment_method, card_name, shipping_cost, purchase_type))
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al registrar compra: {e}")
            return False



    def add_combo_purchase(self, combo_name, total_cost, distribution_method, items, 
                           supplier_id, payment_method, buyer_tag, origin_state, 
                           purchase_type, delivery_date, delivery_status, shipping_cost=0.0):
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
                    # Allocate shipping cost proportionally for the total, but keep unit cost unchanged
                    weight = (total_p_cost / total_cost) if total_cost > 0 else (1.0 / len(items))
                    allocated_shipping = shipping_cost * weight
                    actual_u_cost = u_cost
                    actual_total_p_cost = total_p_cost + allocated_shipping

                    cursor.execute("""
                        INSERT INTO purchases (
                            product_id, quantity, unit_cost, total_cost, supplier_id, 
                            payment_method, buyer_tag, is_return, origin_state,
                            purchase_type, delivery_date, delivery_status,
                            combo_reference, combo_name, distribution_method, shipping_cost
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (p_id, qty, actual_u_cost, actual_total_p_cost, supplier_id, payment_method, 
                          buyer_tag, 0, origin_state, purchase_type, delivery_date, 
                          delivery_status, combo_ref, combo_name, distribution_method, allocated_shipping))
                    
                    # Stock
                    if delivery_status != 'Pendiente':
                        cursor.execute("UPDATE products SET current_stock = current_stock + ? WHERE id = ?", (qty, p_id))
                    
                    # Update cost and price
                    if n_price is not None and str(n_price).strip() != "":
                        try:
                            price_val = float(n_price)
                            cursor.execute("UPDATE products SET cost_price = ?, selling_price = ? WHERE id = ?", (actual_u_cost, price_val, p_id))
                        except ValueError:
                            cursor.execute("UPDATE products SET cost_price = ? WHERE id = ?", (actual_u_cost, p_id))
                    else:
                        cursor.execute("UPDATE products SET cost_price = ? WHERE id = ?", (actual_u_cost, p_id))
                        
                # Integrar con Finanzas (Gastos / Cuentas por Pagar)
                cursor.execute("SELECT name FROM suppliers WHERE id = ?", (supplier_id,))
                supp_row = cursor.fetchone()
                supplier_name = supp_row[0] if supp_row else f"Proveedor {supplier_id}"
                
                is_credit = ("crédito" in str(payment_method).lower() or "credito" in str(payment_method).lower()) and "tarjeta" not in str(payment_method).lower()

                if not is_credit:
                    cursor.execute("""
                        INSERT INTO expenses (category, description, amount, payment_method, tax_included, is_paid)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ("Compra de Inventario (Combo)", f"Combo '{combo_name}' a {supplier_name}", total_cost + shipping_cost, payment_method, 0, 1))
                else:
                    cursor.execute("""
                        INSERT INTO accounts_payable (provider_name, description, total_amount, due_date, status, payment_method, shipping_cost, purchase_type)
                        VALUES (?, ?, ?, ?, 'Pendiente', ?, ?, ?)
                    """, (supplier_name, f"Combo '{combo_name}'", total_cost + shipping_cost, delivery_date, payment_method, shipping_cost, purchase_type))

                conn.commit()
                return combo_ref
        except sqlite3.Error as e:
            print(f"Error al registrar compra combo: {e}")
            return None

    def get_pending_orders(self):
        """Obtiene detalles de los productos pendientes de recibir desde órdenes 'En Línea'."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        IFNULL(pod.combo_name, pr.name) as product_name,
                        (pod.ordered_quantity - pod.received_quantity) as pending_qty,
                        s.name as supplier,
                        po.date as order_date,
                        pod.actual_unit_cost as cost,
                        po.order_number,
                        po.tracking_number,
                        po.estimated_delivery_date
                    FROM purchase_order_details pod
                    JOIN purchase_orders po ON pod.order_id = po.id
                    JOIN products pr ON pod.product_id = pr.id
                    JOIN suppliers s ON po.supplier_id = s.id
                    WHERE po.status = 'Pendiente de recibir' AND po.purchase_type = 'En Línea'
                    ORDER BY po.date ASC
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener productos pendientes: {e}")
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
                
                # 3. Insertar detalles y actualizar stock (Lógica FIFO)
                for p_id, qty, price in items:
                    # Conseguir el costo base por defecto del producto
                    cursor.execute("SELECT cost_price, tax_percentage FROM products WHERE id = ?", (p_id,))
                    p_row = cursor.fetchone()
                    default_cost = p_row[0] * (1 + p_row[1] / 100.0) if p_row else 0.0
                    
                    # FIFO Lógica
                    qty_needed = qty
                    total_cost = 0.0
                    
                    cursor.execute("SELECT id, remaining_quantity, actual_unit_cost FROM inventory_batches WHERE product_id = ? AND remaining_quantity > 0 ORDER BY received_date ASC", (p_id,))
                    batches = cursor.fetchall()
                    
                    for b_id, b_qty, b_cost in batches:
                        if qty_needed <= 0:
                            break
                            
                        if b_qty >= qty_needed:
                            # Este lote cubre la necesidad actual
                            cursor.execute("UPDATE inventory_batches SET remaining_quantity = remaining_quantity - ? WHERE id = ?", (qty_needed, b_id))
                            total_cost += (qty_needed * b_cost)
                            qty_needed = 0
                        else:
                            # Este lote se consume por completo
                            cursor.execute("UPDATE inventory_batches SET remaining_quantity = 0 WHERE id = ?", (b_id,))
                            total_cost += (b_qty * b_cost)
                            qty_needed -= b_qty
                            
                    # Si todavía falta (porque no había lotes), usamos el default_cost
                    if qty_needed > 0:
                        total_cost += (qty_needed * default_cost)
                        
                    unit_cost_at_sale = (total_cost / qty) if qty > 0 else default_cost

                    cursor.execute("""
                        INSERT INTO sale_details (sale_id, product_id, quantity, price_at_sale, unit_cost_at_sale)
                        VALUES (?, ?, ?, ?, ?)
                    """, (sale_id, p_id, qty, price, unit_cost_at_sale))
                    
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
                cursor.execute("SELECT id, name, cut_day, payment_day, bank, last_digits, credit_limit, is_active FROM credit_cards ORDER BY name")
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener tarjetas: {e}")
            return []

    def add_credit_card(self, name, cut_day=None, payment_day=None, bank="", last_digits="", credit_limit=0.0, is_active=1):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO credit_cards (name, cut_day, payment_day, bank, last_digits, credit_limit, is_active) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, cut_day, payment_day, bank, last_digits, credit_limit, is_active))
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

    def get_credit_card_summaries(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        c.id,
                        c.name,
                        c.bank,
                        c.last_digits,
                        c.credit_limit,
                        c.cut_day,
                        c.payment_day,
                        IFNULL(SUM(a.total_amount), 0) as total_gastado,
                        IFNULL(SUM(a.total_amount - a.amount_paid), 0) as total_pendiente,
                        IFNULL(SUM(a.amount_paid), 0) as total_pagado,
                        COUNT(a.id) as num_purchases
                    FROM credit_cards c
                    LEFT JOIN accounts_payable a 
                        ON c.id = a.card_id
                    WHERE c.is_active = 1
                    GROUP BY c.id
                    ORDER BY c.name
                """)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener resumen de tarjetas: {e}")
            return []

    def get_card_purchases(self, card_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        created_at as fecha,
                        provider_name as proveedor,
                        description as concepto,
                        total_amount as importe,
                        status as estado,
                        payment_date as fecha_pago
                    FROM accounts_payable
                    WHERE card_id = ?
                    ORDER BY created_at DESC
                """, (card_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener compras de tarjeta: {e}")
            return []

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
                    SELECT 
                        s.date, 
                        s.ticket_number, 
                        IFNULL(c.name, 'Mostrador'), 
                        s.discount_applied, 
                        s.payment_method, 
                        s.total_amount,
                        IFNULL((
                            SELECT SUM(sd.quantity * p.cost_price * (1 + p.tax_percentage / 100.0))
                            FROM sale_details sd
                            JOIN products p ON sd.product_id = p.id
                            WHERE sd.sale_id = s.id
                        ), 0) as total_cost_with_tax
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

    def get_purchase_history(self, product_id, purchase_mode=None):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT date, quantity, unit_cost, total_cost, supplier_name, buyer_tag, 
                           purchase_type, delivery_status, combo_reference, combo_name, order_id
                    FROM (
                        SELECT p.date, p.quantity, p.unit_cost, p.total_cost, s.name as supplier_name, p.buyer_tag, 
                               p.purchase_type, p.delivery_status, p.combo_reference, p.combo_name, p.product_id, NULL as order_id
                        FROM purchases p
                        LEFT JOIN suppliers s ON p.supplier_id = s.id
                        WHERE p.is_return = 0
                        
                        UNION ALL
                        
                        SELECT po.date as date, pod.ordered_quantity as quantity, pod.actual_unit_cost as unit_cost, 
                               (pod.ordered_quantity * pod.actual_unit_cost) as total_cost, s.name as supplier_name, 
                               '-' as buyer_tag, po.purchase_type, po.status as delivery_status, pod.combo_reference, pod.combo_name, pod.product_id, po.id as order_id
                        FROM purchase_order_details pod
                        JOIN purchase_orders po ON pod.order_id = po.id
                        LEFT JOIN suppliers s ON po.supplier_id = s.id
                    )
                    WHERE product_id = ?
                """
                params = [product_id]
                
                if purchase_mode == 'combo':
                    query += " AND (combo_reference IS NOT NULL AND combo_reference != '')"
                elif purchase_mode == 'individual':
                    query += " AND (combo_reference IS NULL OR combo_reference = '')"
                    
                query += " ORDER BY date DESC"
                
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener historial de compras: {e}")
            return []

    # ==========================================
    # GASTOS Y CUENTAS POR PAGAR (FINANZAS)
    # ==========================================
    def add_expense(self, category, description, amount, payment_method, tax_included=False, is_paid=True):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO expenses (category, description, amount, payment_method, tax_included, is_paid)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (category, description, amount, payment_method, tax_included, is_paid))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al registrar gasto: {e}")
            return None

    def get_unified_expenses_by_period(self, start_date, end_date):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        'EXP-' || e.id as id,
                        e.date as fecha,
                        e.category as proveedor_categoria,
                        e.description as concepto_ref,
                        e.amount as importe,
                        0 as impuestos,
                        e.payment_method as tarjeta_metodo,
                        '' as digitos,
                        CASE WHEN e.is_paid = 1 THEN 'Pagado' ELSE 'Pendiente' END as estado,
                        e.date as fecha_pago
                    FROM expenses e
                    WHERE date(e.date) BETWEEN date(?) AND date(?)
                    UNION ALL
                    SELECT 
                        'AP-' || ap.id as id,
                        ap.created_at as fecha,
                        ap.provider_name as proveedor_categoria,
                        ap.description as concepto_ref,
                        ap.total_amount as importe,
                        0 as impuestos,
                        COALESCE(c.name, ap.payment_method) as tarjeta_metodo,
                        COALESCE(c.last_digits, '') as digitos,
                        ap.status as estado,
                        ap.payment_date as fecha_pago
                    FROM accounts_payable ap
                    LEFT JOIN credit_cards c ON ap.card_id = c.id
                    WHERE date(ap.created_at) BETWEEN date(?) AND date(?)
                    ORDER BY fecha DESC
                """, (start_date, end_date, start_date, end_date))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener gastos: {e}")
            return []

    def get_total_expenses(self, start_date, end_date):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT SUM(amount) FROM expenses
                    WHERE date(date) BETWEEN date(?) AND date(?) AND is_paid = 1
                """, (start_date, end_date))
                res = cursor.fetchone()
                return res[0] if res[0] else 0.0
        except sqlite3.Error as e:
            print(f"Error al obtener total de gastos: {e}")
            return 0.0

    def get_accounts_payable(self, status=None):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT a.id, a.provider_name, a.description, a.total_amount, a.amount_paid, 
                           a.due_date, a.status, a.payment_method, c.name as card_name, a.shipping_cost, a.purchase_type 
                    FROM accounts_payable a
                    LEFT JOIN credit_cards c ON a.card_id = c.id
                """
                if status:
                    query += " WHERE a.status = ?"
                    cursor.execute(query, (status,))
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener cuentas por pagar: {e}")
            return []

    def add_account_payable(self, provider_name, description, total_amount, due_date, payment_method="Efectivo", card_id=None, shipping_cost=0.0, purchase_type=None):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO accounts_payable (provider_name, description, total_amount, due_date, status, payment_method, card_id, shipping_cost, purchase_type)
                    VALUES (?, ?, ?, ?, 'Pendiente', ?, ?, ?, ?)
                """, (provider_name, description, total_amount, due_date, payment_method, card_id, shipping_cost, purchase_type))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar cuenta por pagar: {e}")
            return None

    def add_payment_to_account(self, account_id, payment_amount):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT total_amount, amount_paid FROM accounts_payable WHERE id = ?", (account_id,))
                res = cursor.fetchone()
                if res:
                    total, paid = res
                    new_paid = paid + payment_amount
                    status = 'Pagado' if new_paid >= total else 'Pendiente'
                    
                    if status == 'Pagado':
                        from datetime import datetime
                        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute("""
                            UPDATE accounts_payable
                            SET amount_paid = ?, status = ?, payment_date = ?
                            WHERE id = ?
                        """, (new_paid, status, now_str, account_id))
                    else:
                        cursor.execute("""
                            UPDATE accounts_payable
                            SET amount_paid = ?, status = ?
                            WHERE id = ?
                        """, (new_paid, status, account_id))
                    conn.commit()
                    return True
                return False
        except sqlite3.Error as e:
            print(f"Error al abonar a cuenta por pagar: {e}")
            return False

    def get_inventory_valuation(self):
        """Obtiene el desglose de lotes activos para calcular el valor total del inventario."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.sku, p.name, b.id, b.remaining_quantity, b.actual_unit_cost, 
                           (b.remaining_quantity * b.actual_unit_cost) as total_value, 
                           b.received_date, b.condition
                    FROM inventory_batches b
                    JOIN products p ON b.product_id = p.id
                    WHERE b.remaining_quantity > 0
                    ORDER BY p.name, b.received_date ASC
                ''')
                return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener valorización de inventario: {e}")
            return []

if __name__ == "__main__":

    db = DatabaseManager()
    db.backup_db()
