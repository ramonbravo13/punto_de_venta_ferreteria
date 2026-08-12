import sqlite3
import os

def check_setup():
    db_path = "provision.db"
    print(f"--- Sistema de Verificación Pro-Vision ---\n")
    
    # 1. Verificar archivo de base de datos
    if os.path.exists(db_path):
        print(f"[OK] Archivo de base de datos '{db_path}' encontrado.")
    else:
        print(f"[FAIL] No se encontró '{db_path}'. Ejecute main.py primero.")
        return

    # 2. Verificar tablas
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        
        required_tables = ['products', 'suppliers', 'purchases', 'sales', 'sale_details']
        for table in required_tables:
            if table in tables:
                print(f"[OK] Tabla '{table}' existe.")
            else:
                print(f"[FAIL] Tabla '{table}' falta.")
        
        # 3. Verificar proveedores iniciales
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        count = cursor.fetchone()[0]
        if count >= 3:
            print(f"[OK] Se encontraron {count} proveedores iniciales.")
        else:
            print(f"[WARNING] Solo hay {count} proveedores (Se esperan 3: Home Depot, Lowe's, General).")
            
        conn.close()
    except Exception as e:
        print(f"[ERROR] Error al acceder a la base de datos: {e}")

if __name__ == "__main__":
    check_setup()
