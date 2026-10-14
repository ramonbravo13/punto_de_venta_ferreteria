import os
import sqlite3
from database import DatabaseManager

def run_audit():
    if os.path.exists('test_audit.db'):
        os.remove('test_audit.db')
        
    db = DatabaseManager('test_audit.db')
    
    print("--- INICIANDO AUDITORIA INTEGRAL ---")
    
    # 1. Registrar producto individual y 2. Registrar combo
    db.add_product("SKU-IND", "Producto Individual", "Cat", 100, 150, 5, 0)
    db.add_product("SKU-COM1", "Combo Parte 1", "Cat", 50, 80, 5, 0)
    db.add_product("SKU-COM2", "Combo Parte 2", "Cat", 50, 80, 5, 0)
    
    p_ind = db.get_product_by_sku_or_name("SKU-IND")
    p_c1 = db.get_product_by_sku_or_name("SKU-COM1")
    p_c2 = db.get_product_by_sku_or_name("SKU-COM2")
    
    id_ind = p_ind[0]
    id_c1 = p_c1[0]
    id_c2 = p_c2[0]
    
    print(f"[OK] Productos creados: IND({id_ind}), COM1({id_c1}), COM2({id_c2})")
    
    # 3. Realizar compra física
    print("\n--- COMPRA FISICA (Individual) ---")
    order_id_1 = db.create_purchase_order(
        order_number="PO-FISICA", supplier_id=1, purchase_type="Física", tracking_number="",
        status="Pendiente de recibir", subtotal=1000, tax=0, shipping=0, total=1000,
        estimated_delivery_date=None
    )
    items_fisica = [{'product_id': id_ind, 'quantity': 10, 'unit_cost': 100}]
    db.add_purchase_order_details(order_id_1, items_fisica, 0, 0)
    
    received_items_fisica = [{'detail_id': 1, 'received_qty': 10, 'product_id': id_ind, 'actual_unit_cost': 100, 'condition': 'Ok'}]
    db.update_purchase_order_status(order_id_1, "Recibida", received_items_fisica, payment_method="Efectivo", is_paid=True)
    
    # 4. Verificar inventario
    prod_check = db.get_product_for_pos("SKU-IND")
    assert prod_check[5] == 10, f"Stock fisico fallo. Esperado 10, actual {prod_check[5]}"
    print(f"[OK] Inventario fsico sum correctamente a {prod_check[5]}.")
    
    # 5. Consultar historial de compra
    hist = db.get_purchase_history(id_ind, 'individual')
    assert len(hist) == 1, "Historial fisico vacio"
    print("[OK] Historial consultado correctamente (Aparece la compra).")
    
    # 6. Realizar compra en lnea
    print("\n--- COMPRA EN LINEA (Combo) ---")
    order_id_2 = db.create_purchase_order(
        order_number="PO-ONLINE", supplier_id=1, purchase_type="En Línea", tracking_number="TRK123",
        status="Pendiente de recibir", subtotal=200, tax=0, shipping=0, total=200,
        estimated_delivery_date=None, payment_method="A crédito", card_id=1
    )
    items_online = [
        {'product_id': id_c1, 'quantity': 2, 'unit_cost': 50, 'combo_ref': 'REF-1', 'combo_name': 'Promo'},
        {'product_id': id_c2, 'quantity': 2, 'unit_cost': 50, 'combo_ref': 'REF-1', 'combo_name': 'Promo'}
    ]
    db.add_purchase_order_details(order_id_2, items_online, 0, 0)
    
    # 6.5. Verificar Finanzas INMEDIATAMENTE al crear orden
    debts_early = db.get_debts_total()
    assert debts_early == 200, f"Deuda no fue generada al crear la orden. Esperado 200, actual {debts_early}"
    print("[OK] Finanzas reconoci la deuda de $200 INMEDIATAMENTE al crear la orden en lnea.")

    
    # 7. Verificar que quede pendiente de recibir
    po2 = [po for po in db.get_purchase_orders() if po[0] == order_id_2][0]
    assert po2[5] == "Pendiente de recibir", "Estado de orden en linea no es Pendiente de recibir"
    print("[OK] Orden en lnea est Pendiente de recibir.")
    
    # 8. Verificar que aparezca en Recibir orden
    rec_orders = db.get_purchase_orders(status="Pendiente de recibir")
    assert any(o[0] == order_id_2 for o in rec_orders), "La orden no aparece para recibir"
    print("[OK] Orden lista para ser recibida en el mdulo Recibir Orden.")
    
    # 9. Verificar que NO aumente el stock
    pc1_check = db.get_product_for_pos("SKU-COM1")
    assert pc1_check[5] == 0, f"Stock subio prematuramente. Stock={pc1_check[5]}"
    print("[OK] Stock de compra en lnea NO subi (es 0 como esperado).")
    
    # 10. Verificar "Pedidos pendientes" (incoming_stock)
    all_p = db.get_all_products()
    pc1_all = [p for p in all_p if p[0] == id_c1][0]
    assert pc1_all[11] == 2, f"Incoming stock fall. Esperado 2, actual {pc1_all[11]}"
    print("[OK] El sistema reconoce 2 unidades como 'Pedidos pendientes'.")
    
    # 11. Recibir la orden
    print("\n--- RECIBIENDO ORDEN ---")
    received_items_online = [
        {'detail_id': 2, 'received_qty': 2, 'product_id': id_c1, 'actual_unit_cost': 50, 'condition': 'Ok'},
        {'detail_id': 3, 'received_qty': 2, 'product_id': id_c2, 'actual_unit_cost': 50, 'condition': 'Ok'}
    ]
    db.update_purchase_order_status(order_id_2, "Recibida", received_items_online, payment_method="Credit", is_paid=False)
    
    # 12. Verificar actualizacin de stock
    pc1_check2 = db.get_product_for_pos("SKU-COM1")
    assert pc1_check2[5] == 2, "Stock NO subi al recibir la orden"
    
    pc1_all2 = [p for p in db.get_all_products() if p[0] == id_c1][0]
    assert pc1_all2[11] == 0, "Incoming stock NO baj a 0 despus de recibir"
    print("[OK] Stock sum a 2 y Pendientes baj a 0.")
    
    # 13. Verificar Finanzas nuevamente
    debts = db.get_debts_total()
    assert debts == 200, f"Deuda en finanzas cambi incorrectamente. Esperado 200 (compra a credito), actual {debts}"
    print("[OK] Finanzas mantuvo correctamente la deuda de $200 tras recibir la orden.")
    
    # 14. Verificar historial
    hist_c1 = db.get_purchase_history(id_c1, 'combo')
    assert len(hist_c1) == 1, "Historial de combo fall"
    print("[OK] Historial del producto en combo verificado con xito.")
    
    # 15. POS Sale check
    print("\n--- PRUEBA DE VENTA POS ---")
    # Intentar vender 3 del IND (que tiene 10)
    sale_items = [(id_ind, 3, 150)]
    # Abrir caja primero para evitar error de Foreign Key
    db.open_caja(100.0)
    db.add_sale(total_amount=450, payment_method="Efectivo", items=sale_items, caja_id=1, discount=0.0)
    p_ind2 = db.get_product_for_pos("SKU-IND")
    assert p_ind2[5] == 7, "Stock de venta no se descont correctamente"
    print("[OK] Venta descont correctamente el stock (de 10 a 7).")
    
    print("\n>>> AUDITORIA COMPLETADA SIN ERRORES <<<")
    
    db.conn.close()

if __name__ == "__main__":
    run_audit()
