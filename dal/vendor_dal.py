from .db_connector import get_connection
from mysql.connector import Error

def search_vendors(search_term):
    """Searches for vendors by name or ID."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT vendor_id, vendor_name, city, state FROM vendors WHERE vendor_name LIKE %s OR vendor_id LIKE %s ORDER BY vendor_name LIMIT 100;"
        search_pattern = f"%{search_term}%"
        cursor.execute(query, (search_pattern, search_pattern))
        return cursor.fetchall()
    except Error as e:
        print(f"Error searching vendors: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
