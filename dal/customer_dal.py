import mysql.connector
from mysql.connector import Error
from .db_connector import get_connection

def search_customers(search_term):
    """Searches for customers by name or ID."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM customers2 WHERE customer_name LIKE %s OR cust_id LIKE %s ORDER BY customer_name LIMIT 100"
        search_pattern = f"%{search_term}%"
        cursor.execute(query, (search_pattern, search_pattern))
        return cursor.fetchall()
    except Error as e:
        print(f"Error searching customers: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_shipping_addresses(cust_id):
    """Fetches all shipping addresses for a given customer ID."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT s.* FROM shipto s JOIN ship_cust_ref r ON s.id_shipto = r.ship_id WHERE r.cust_id = %s"
        cursor.execute(query, (cust_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching shipping addresses: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def create_customer(customer_data):
    """Inserts a new customer into the customers2 table."""
    conn = get_connection()
    if not conn: return None
    cursor = None
    try:
        cursor = conn.cursor()
        query = "INSERT INTO customers2 (customer_name, address1, city, state, zip, cust_id, comment_id, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        data_tuple = (customer_data.get('customer_name'), customer_data.get('address1'), customer_data.get('city'), customer_data.get('state'), customer_data.get('zip'), customer_data.get('cust_id'), '', 999)
        cursor.execute(query, data_tuple)
        conn.commit()
        return customer_data.get('cust_id')
    except Error as e:
        print(f"Error creating customer: {e}")
        conn.rollback()
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def update_customer(customer_data):
    """Updates an existing customer's record."""
    conn = get_connection()
    if not conn: return False
    cursor = None
    try:
        cursor = conn.cursor()
        query = "UPDATE customers2 SET customer_name = %s, address1 = %s, city = %s, state = %s, zip = %s, updated_by = %s WHERE cust_id = %s"
        data_tuple = (customer_data.get('customer_name'), customer_data.get('address1'), customer_data.get('city'), customer_data.get('state'), customer_data.get('zip'), 999, customer_data.get('cust_id'))
        cursor.execute(query, data_tuple)
        conn.commit()
        return True
    except Error as e:
        print(f"Error updating customer: {e}")
        conn.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
