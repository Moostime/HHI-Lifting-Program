from .db_connector import get_connection
from mysql.connector import Error

def get_distinct_part_numbers():
    """Gets a list of unique assembly part numbers from the lookup table."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT DISTINCT assembly_part_num FROM wire_rope_assembly_lookup ORDER BY assembly_part_num"
        cursor.execute(query)
        return [row['assembly_part_num'] for row in cursor.fetchall()]
    except Error as e:
        print(f"Error fetching distinct part numbers: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_distinct_sizes_for_part_num(part_num):
    """Gets a list of unique sizes for a given part number from the lookup table."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT DISTINCT component_deci_size FROM wire_rope_assembly_lookup WHERE assembly_part_num = %s ORDER BY component_deci_size"
        cursor.execute(query, (part_num,))
        return [row['component_deci_size'] for row in cursor.fetchall()]
    except Error as e:
        print(f"Error fetching distinct sizes: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_bom_by_sku(nu_sku):
    """Gets the Bill of Materials for a specific nu_sku."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT component_kdc_id, description1, per_assy_qty FROM wire_rope_assembly_lookup WHERE nu_sku = %s"
        cursor.execute(query, (nu_sku,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error getting BOM by SKU: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
