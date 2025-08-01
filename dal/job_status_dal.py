from .db_connector import get_connection
from mysql.connector import Error

def get_wip_orders():
    """Fetches all orders currently in Work in Progress (WIP)."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT js.order_num, c.customer_name, p.description1, js.wip AS wip_date, js.tested AS tested_date, js.tagged AS tagged_date FROM job_status js JOIN orders o ON js.order_num = o.order_num JOIN customers2 c ON o.cust_id = c.cust_id JOIN orders_detail od ON js.order_num = od.order_num AND js.assy_id = od.assy_id JOIN products p ON od.kdc_id = p.kdc_id WHERE js.wip IS NOT NULL AND js.shipped IS NULL ORDER BY js.wip ASC;"
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching WIP orders: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
