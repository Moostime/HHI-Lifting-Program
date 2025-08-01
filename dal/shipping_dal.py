from .db_connector import get_connection
from mysql.connector import Error

def find_open_sales_orders(search_term):
    """Finds sales orders that are open and ready to be shipped."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT o.order_num, o.order_date, o.po_num, c.customer_name FROM orders o JOIN customers2 c ON o.cust_id = c.cust_id WHERE (o.order_num LIKE %s OR o.po_num LIKE %s) AND o.order_num IN (SELECT DISTINCT order_num FROM orders_detail WHERE q_p_s2 = 3) ORDER BY o.order_date DESC LIMIT 100;"
        search_pattern = f"%{search_term}%"
        cursor.execute(query, (search_pattern, search_pattern))
        return cursor.fetchall()
    except Error as e:
        print(f"Error finding open sales orders: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_so_line_items(order_num):
    """Fetches the line items for a given sales order number."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT od.assy_id, od.kdc_id, od.qty, p.description1 FROM orders_detail od JOIN products p ON od.kdc_id = p.kdc_id WHERE od.order_num = %s AND od.q_p_s2 = 3"
        cursor.execute(query, (order_num,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error getting SO line items: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def ship_so_items(order_num, shipped_items, employee_num):
    """Creates product_trans records for shipped items."""
    conn = get_connection()
    if not conn: return False
    cursor = None
    try:
        cursor = conn.cursor()
        query = "INSERT INTO product_trans (order_num, kdc_id, assy_id, units_shipped, q_p_s, employee_num, trans_date) VALUES (%s, %s, %s, %s, %s, %s, CURDATE())"
        items_to_insert = []
        for item in shipped_items:
            trans_tuple = (order_num, item['kdc_id'], item['assy_id'], item['shipped_qty'], 3, employee_num)
            items_to_insert.append(trans_tuple)
        cursor.executemany(query, items_to_insert)
        conn.commit()
        print(f"Successfully shipped items for SO #{order_num}")
        return True
    except Error as e:
        print(f"Error shipping SO items: {e}")
        conn.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
