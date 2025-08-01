from .db_connector import get_connection
from mysql.connector import Error

def get_ranked_component_options(category_id, keyword):
    """Fetches all products for a category/keyword, ranked by total units sold."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT p.kdc_id, p.description1, SUM(IFNULL(pt.units_sold, 0)) AS total_sold FROM products p LEFT JOIN product_trans pt ON p.kdc_id = pt.kdc_id WHERE p.category_id = %s AND p.description1 LIKE %s GROUP BY p.kdc_id, p.description1 ORDER BY total_sold DESC, p.description1 ASC;"
        search_pattern = f"%{keyword}%"
        cursor.execute(query, (category_id, search_pattern))
        return cursor.fetchall()
    except Error as e:
        print(f"Error searching components: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
