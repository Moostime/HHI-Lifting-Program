from .db_connector import get_connection
from mysql.connector import Error

def get_sales_by_customer(start_date, end_date):
    """Calculates total sales for each customer within a given date range."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT c.customer_name, COUNT(DISTINCT o.order_num) AS order_count, SUM(od.ext_price) AS total_sales FROM orders o JOIN orders_detail od ON o.order_num = od.order_num JOIN customers2 c ON o.cust_id = c.cust_id WHERE od.q_p_s2 = 3 AND o.order_date BETWEEN %s AND %s GROUP BY c.customer_name ORDER BY total_sales DESC;"
        cursor.execute(query, (start_date, end_date))
        return cursor.fetchall()
    except Error as e:
        print(f"Error generating sales report: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
