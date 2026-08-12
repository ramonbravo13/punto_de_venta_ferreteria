import pytest
import os
import sqlite3
from database import DatabaseManager
from logic import BusinessLogic

# Fixture para configurar una base de datos de prueba limpia
@pytest.fixture
def db():
    test_db = "test_provision.db"
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except PermissionError:
            pass
    
    manager = DatabaseManager(test_db)
    yield manager
    
    # Intentar limpiar, pero no fallar si Windows bloquea el archivo
    import gc
    gc.collect() # Forzar liberación de objetos que puedan tener handles abiertos
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except PermissionError:
            print(f"\n[Nota] No se pudo eliminar {test_db}, el archivo será sobrescrito en la próxima prueba.")

def test_add_product(db):
    """Prueba que un producto se agregue correctamente."""
    success = db.add_product(
        sku="TEST-001",
        name="Producto de Prueba",
        category="General",
        cost=10.0,
        price=15.0,
        min_stock=5,
        stock=10
    )
    assert success is True
    
    product = db.get_product_by_sku_or_name("TEST-001")
    assert product is not None
    assert product[1] == "Producto de Prueba"
    assert product[3] == 15.0

def test_add_purchase_updates_stock(db):
    """Prueba que registrar una compra aumente el stock."""
    # 1. Agregar producto base
    db.add_product("SKU-PURCH", "Item Compra", "General", 5.0, 10.0, 2, stock=5)
    prod = db.get_product_by_sku_or_name("SKU-PURCH")
    pid = prod[0]
    
    # 2. Registrar compra de 5 unidades
    # params: product_id, qty, unit_cost, supplier_id, payment_method, buyer_tag
    db.add_purchase(pid, 5, 5.0, 1, "Cash", "Admin")
    
    # 3. Verificar stock (5 inicial + 5 nuevos = 10)
    products = db.get_all_products()
    # product structure in get_all_products: id, image_path, sku, name, category, current_stock, ...
    target = next(p for p in products if p[2] == "SKU-PURCH")
    assert target[5] == 10

def test_add_sale_updates_stock(db):
    """Prueba que realizar una venta disminuya el stock."""
    db.add_product("SKU-SALE", "Item Venta", "General", 5.0, 10.0, 2, stock=20)
    prod = db.get_product_by_sku_or_name("SKU-SALE")
    pid = prod[0]
    
    # Registrar venta de 3 unidades
    # items list: (product_id, quantity, price)
    items = [(pid, 3, 10.0)]
    db.add_sale(30.0, "Efectivo", items)
    
    # Verificar stock (20 - 3 = 17)
    products = db.get_all_products()
    target = next(p for p in products if p[2] == "SKU-SALE")
    assert target[5] == 17

def test_logic_calculate_change():
    """Prueba el cálculo de cambio en el POS."""
    assert BusinessLogic.calculate_change(150.50, 200.00) == 49.50
    assert BusinessLogic.calculate_change(100, 50) == 0  # No alcanza

def test_logic_stock_status():
    """Prueba los colores del semáforo de stock."""
    assert BusinessLogic.get_stock_status(10, 5) == "Green"
    assert BusinessLogic.get_stock_status(3, 5) == "Amber"
    assert BusinessLogic.get_stock_status(0, 5) == "Red"
    assert BusinessLogic.get_stock_status(-1, 5) == "Red"

def test_add_purchase_full_features(db):
    """Prueba las nuevas características del módulo de compras."""
    db.add_product("SKU-NEW-PURCH", "Item Completo", "General", 10.0, 20.0, 2, stock=0)
    prod = db.get_product_by_sku_or_name("SKU-NEW-PURCH")
    pid = prod[0]
    
    # Comprar 10 unidades a $15 c/u, con 10% de impuesto
    # Costo base = 150. Impuesto = 15. Total = 165.
    db.add_purchase(
        product_id=pid,
        qty=10,
        unit_cost=15.0,
        supplier_id=1,
        payment_method="Cash",
        buyer_tag="Admin",
        origin_state="TX",
        tax_percentage=10.0,
        new_selling_price=30.0
    )
    
    # 1. Verificar registro en BD y costo total
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT total_cost, origin_state, tax_percentage FROM purchases WHERE product_id = ?", (pid,))
        purchase = cursor.fetchone()
        
    assert purchase is not None
    assert purchase[0] == 165.0  # El costo total debe incluir el impuesto
    assert purchase[1] == "TX"  # Estado de origen
    assert purchase[2] == 10.0  # Porcentaje de impuesto
    
    # 2. Verificar impacto en la tabla de productos (precio de venta, costo, impuesto, stock)
    products = db.get_all_products()
    # pos en get_all_products: 5=stock, 6=costo, 7=venta, 9=impuesto
    target = next(p for p in products if p[2] == "SKU-NEW-PURCH")
    assert target[5] == 10       # Stock sumó 10
    assert target[6] == 15.0     # Costo actualizado
    assert target[7] == 30.0     # Precio de venta actualizado
    assert target[9] == 10.0     # Impuesto actualizado

def test_online_purchase_workflow(db):
    """Prueba que una compra en línea no sume stock al inventario inmediatamente, 
    y que sí lo sume al usar receive_purchase."""
    
    db.add_product("SKU-ONLINE", "Item Online", "General", 5.0, 10.0, 2, stock=0)
    prod = db.get_product_by_sku_or_name("SKU-ONLINE")
    pid = prod[0]
    
    # 1. Registrar compra En Línea (estado = Pendiente)
    db.add_purchase(
        product_id=pid, qty=5, unit_cost=5.0, supplier_id=1, payment_method="Cash", buyer_tag="User",
        purchase_type="En Línea", delivery_date="2030-01-01", delivery_status="Pendiente"
    )
    
    # 2. Verificar que el stock físico siga siendo 0
    prod_updated = db.get_product_by_sku_or_name("SKU-ONLINE")
    # Para validar el stock, podemos revisar en get_all_products
    all_products = db.get_all_products()
    target = next(p for p in all_products if p[2] == "SKU-ONLINE")
    assert target[5] == 0           # current_stock no cambió
    assert target[10] == 5          # incoming_stock es 5
    
    # 3. Verificar en pending orders
    pending = db.get_pending_orders()
    assert len(pending) >= 1
    purch_id = pending[0][0]
    
    # 4. Recibir el pedido
    success = db.receive_purchase(purch_id)
    assert success is True
    
    # 5. Volver a revisar stock y pedidos pendientes
    all_products_after = db.get_all_products()
    target_after = next(p for p in all_products_after if p[2] == "SKU-ONLINE")
    assert target_after[5] == 5     # current_stock sumó 5!
    assert target_after[10] == 0    # incoming_stock es 0
    
    pending_after = db.get_pending_orders()
    assert not any(p[0] == purch_id for p in pending_after)

def test_client_management(db):
    """Prueba la creación de un cliente y asignación a una venta."""
    # 1. Crear cliente
    success = db.add_customer("Carlos VIP", "555-0000", "carlos@vip.com", "Av. Siempre Viva 123")
    assert success is True
    
    customers = db.get_all_customers()
    assert len(customers) >= 1
    carlos_id = next(c[0] for c in customers if c[1] == "Carlos VIP")
    
    # 2. Asignar venta a cliente
    db.add_product("SKU-VIP1", "Producto VIP", "VIP", 50.0, 100.0, 5, stock=10)
    vip_prod = db.get_product_by_sku_or_name("SKU-VIP1")
    
    # Venta de 2 productos VIP ($200), con descuento de $20
    db.add_sale(
        total_amount=180.0,
        payment_method="Tarjeta",
        items=[(vip_prod[0], 2, 100.0)],
        caja_id=None,
        customer_id=carlos_id,
        discount=20.0
    )
    
    # 3. Comprobar historial del cliente
    history = db.get_customer_history(carlos_id)
    assert len(history) == 1
    assert history[0][2] == 180.0  # total_amount
    assert history[0][3] == 20.0   # discount_applied

def test_client_analytics(db):
    """Comprueba que las métricas (frecuencia, gasto, promociones) se calculan correctamente."""
    db.add_customer("Ana Top", "111", "", "")
    db.add_customer("Luis B", "222", "", "")
    
    customers = db.get_all_customers()
    ana_id = next(c[0] for c in customers if c[1] == "Ana Top")
    luis_id = next(c[0] for c in customers if c[1] == "Luis B")
    
    db.add_product("SKU-VIP1", "Producto VIP", "VIP", 50.0, 100.0, 5, stock=10)
    p = db.get_product_by_sku_or_name("SKU-VIP1")
    
    # Ana compra 3 veces, 100$ cada vez, 0 desc
    for _ in range(3):
        db.add_sale(100.0, "Efectivo", [(p[0], 1, 100.0)], customer_id=ana_id)
        
    # Luis compra 1 vez, 500$, con descuento de 50$
    db.add_sale(450.0, "Efectivo", [(p[0], 1, 500.0)], customer_id=luis_id, discount=50.0)
    
    # Validar Frecuencia
    top_freq = db.get_top_customers_by_frequency(10)
    # Ana tiene 3 visitas, Carlos 1, Luis 1
    assert top_freq[0][0] == "Ana Top"
    assert top_freq[0][1] == 3
    
    # Validar Gasto
    top_spent = db.get_top_customers_by_spent(10)
    # Luis gastó 450, Ana 300, Carlos 180
    assert top_spent[0][0] == "Luis B"
    assert top_spent[0][1] == 450.0
    
    # Validar Promociones/Descuentos
    top_promo = db.get_top_customers_by_promotions(10)
    # Luis tiene 50, Carlos 20, Ana 0
    assert top_promo[0][0] == "Luis B"
    assert top_promo[0][1] == 50.0

def test_combo_purchase_equitable(db):
    # Setup
    db.add_product("C-A1", "Item A", "ComboCat", 0.0, 10.0, 5, stock=0)
    db.add_product("C-A2", "Item B", "ComboCat", 0.0, 10.0, 5, stock=0)
    p1 = db.get_product_by_sku_or_name("C-A1")
    p2 = db.get_product_by_sku_or_name("C-A2")
    
    # Comprar Combo: 2 de A, 3 de B. Total= 5 uds. Costo = 100
    items = [
        {'product_id': p1[0], 'quantity': 2, 'unit_cost': 20.0}, # unit cost passed from UI
        {'product_id': p2[0], 'quantity': 3, 'unit_cost': 20.0}
    ]
    
    ref = db.add_combo_purchase("Promo Test", 100.0, "Equitativa", items, 1, "Efectivo", "David", "TX", "Física", None, "Entregado")
    assert ref is not None
    
    # Comprobar Stock y Costos actualizados
    p1_updated = db.get_product_by_sku_or_name("C-A1")
    p2_updated = db.get_product_by_sku_or_name("C-A2")
    
    all_p = db.get_all_products()
    p1_full = next(x for x in all_p if x[2] == "C-A1")
    p2_full = next(x for x in all_p if x[2] == "C-A2")
    
    assert p1_full[5] == 2 # Stock de A subió 2
    assert p2_full[5] == 3 # Stock de B subió 3
    assert p1_full[6] == 20.0 # Costo Unitario es 20.0 (100 / 5)
    assert p2_full[6] == 20.0

def test_combo_purchase_manual(db):
    db.add_product("C-M1", "Item M1", "ComboCat", 0.0, 10.0, 5, stock=0)
    db.add_product("C-M2", "Item M2", "ComboCat", 0.0, 10.0, 5, stock=0)
    p1 = db.get_product_by_sku_or_name("C-M1")
    p2 = db.get_product_by_sku_or_name("C-M2")
    
    # Combo de $1000. M1 tiene 70% peso. M2 tiene 30% peso.
    # Uds: 2 de M1, 3 de M2.
    # Costo por ud M1 = (1000 * 0.70) / 2 = 350.0
    # Costo por ud M2 = (1000 * 0.30) / 3 = 100.0
    items = [
        {'product_id': p1[0], 'quantity': 2, 'unit_cost': 350.0},
        {'product_id': p2[0], 'quantity': 3, 'unit_cost': 100.0}
    ]
    ref = db.add_combo_purchase("Promo Manual", 1000.0, "Manual (%)", items, 1, "Efectivo", "David", "TX", "Física", None, "Entregado")
    assert ref is not None
    
    all_p = db.get_all_products()
    p1_full = next(x for x in all_p if x[2] == "C-M1")
    p2_full = next(x for x in all_p if x[2] == "C-M2")
    
    assert p1_full[6] == 350.0 # Costo exacto
    assert p2_full[6] == 100.0


