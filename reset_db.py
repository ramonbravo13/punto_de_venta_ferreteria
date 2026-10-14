import sqlite3

def clean_database():
    conn = sqlite3.connect('provision.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = OFF;")
    
    tables_to_clear = [
        'sale_details',
        'sales',
        'inventory_batches',
        'purchase_order_details',
        'purchase_orders',
        'purchases',
        'products',
        'movimientos_caja',
        'cajas',
        'expenses',
        'accounts_payable',
        'customers'
    ]
    
    for table in tables_to_clear:
        print(f"Borrando {table}...")
        try:
            cursor.execute(f"DELETE FROM {table};")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
        except sqlite3.Error as e:
            print(f"Error al borrar {table}: {e}")
        
    conn.commit()
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.close()
    print("Base de datos limpiada correctamente. Configuraciones (Categorías, Proveedores, Personal, Tarjetas, Marcas) conservadas.")

if __name__ == "__main__":
    clean_database()
