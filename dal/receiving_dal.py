from .db_connector import get_connection
from mysql.connector import Error

def find_open_purchase_orders(search_term):
    """Finds purchase orders that are open and ready to be received."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT o.order_num, o.order_date, v.vendor_name, o.cust_id as vendor_id FROM orders o JOIN vendors v ON o.cust_id = v.vendor_id WHERE o.order_num LIKE %s AND o.order_num IN (SELECT DISTINCT order_num FROM orders_detail WHERE q_p_s2 = 2) ORDER BY o.order_date DESC LIMIT 100;"
        search_pattern = f"%{search_term}%"
        cursor.execute(query, (search_pattern,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error finding open purchase orders: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_po_line_items(order_num):
    """Fetches the line items for a given purchase order number."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT od.assy_id, od.kdc_id, od.qty, p.description1 FROM orders_detail od JOIN products p ON od.kdc_id = p.kdc_id WHERE od.order_num = %s AND od.q_p_s2 = 2"
        cursor.execute(query, (order_num,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error getting PO line items: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def receive_po_items(order_num, received_items, employee_num):
    """Creates product_trans records for received items."""
    conn = get_connection()
    if not conn: return False
    cursor = None
    try:
        cursor = conn.cursor()
        query = "INSERT INTO product_trans (order_num, kdc_id, assy_id, units_received, q_p_s, employee_num, trans_date) VALUES (%s, %s, %s, %s, %s, %s, CURDATE())"
        items_to_insert = []
        for item in received_items:
            trans_tuple = (order_num, item['kdc_id'], item['assy_id'], item['received_qty'], 2, employee_num)
            items_to_insert.append(trans_tuple)
        cursor.executemany(query, items_to_insert)
        conn.commit()
        print(f"Successfully received items for PO #{order_num}")
        return True
    except Error as e:
        print(f"Error receiving PO items: {e}")
        conn.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
