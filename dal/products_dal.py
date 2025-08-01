import mysql.connector
from mysql.connector import Error
from .db_connector import get_connection

def get_product_by_id(kdc_id):
    """Fetches a single product's details by its kdc_id."""
    conn = get_connection()
    if not conn: return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM products WHERE kdc_id = %s"
        cursor.execute(query, (kdc_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error fetching product: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_product_by_part_num(part_num):
    """Fetches a single product's details by its part number (stock_id)."""
    conn = get_connection()
    if not conn: return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM products WHERE stock_id = %s LIMIT 1"
        cursor.execute(query, (part_num,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error fetching product by part number: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def update_product(product_data):
    """Updates key fields of an existing product."""
    conn = get_connection()
    if not conn: return False
    cursor = None
    try:
        cursor = conn.cursor()
        query = "UPDATE products SET description1 = %s, list_price = %s, unit_cost = %s WHERE kdc_id = %s"
        data_tuple = (product_data.get('description1'), product_data.get('list_price'), product_data.get('unit_cost'), product_data.get('kdc_id'))
        cursor.execute(query, data_tuple)
        conn.commit()
        return True
    except Error as e:
        print(f"Error updating product: {e}")
        conn.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
