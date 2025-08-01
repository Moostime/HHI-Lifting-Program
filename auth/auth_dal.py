import mysql.connector
from mysql.connector import Error
from dal.db_connector import get_connection

def login_user(username, password):
    """Authenticates a user by their username and password."""
    conn = get_connection()
    if not conn: return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        # CORRECTED: Removed the "AND active = 'y'" clause
        query = "SELECT EmployeeNum, FirstName, LastName, access_level FROM employees WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        if user:
            print(f"DEBUG: User logged in with permissions: {set(user.get('access_level', '').split(','))}")
        return user
    except Error as e:
        print(f"Error during login: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()