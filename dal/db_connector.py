import mysql.connector
from mysql.connector import pooling, Error

# --- Configuration ---
# Make sure these values are correct for your database.
DB_CONFIG = {
    'host': 'localhost',
    'database': 'hhi',
    'user': 'moos',
    'password': 'DonkeyFruit%69'
}

# --- Create the Connection Pool ---
# This code runs only once when the application starts.
try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="kdc_pool",
        pool_size=2,  # Create a pool of 2 reusable connections
        **DB_CONFIG
    )
    print("Database connection pool created successfully.")
except Error as e:
    print(f"Error creating connection pool: {e}")
    connection_pool = None

def get_connection():
    """Gets a connection from the pool."""
    if connection_pool:
        try:
            return connection_pool.get_connection()
        except Error as e:
            print(f"Error getting connection from pool: {e}")
            return None
    return None






