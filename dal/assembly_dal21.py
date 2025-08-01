import mysql.connector
from mysql.connector import Error
from .db_connector import get_connection

def get_wirerope_diameters():
    """Gets a list of all unique wire rope diameters from the builder table."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT DISTINCT Dia FROM wire_rope_builder ORDER BY CAST(REPLACE(Dia, '-', '.') AS DECIMAL(10,5))"
        cursor.execute(query)
        return [row['Dia'] for row in cursor.fetchall()]
    except Error as e:
        print(f"Error fetching wire rope diameters: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_assembly_part_numbers():
    """Gets a list of all unique assembly part numbers from the assembler table."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT DISTINCT part_num FROM assembler ORDER BY part_num"
        cursor.execute(query)
        return [row['part_num'] for row in cursor.fetchall()]
    except Error as e:
        print(f"Error fetching assembly part numbers: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_assembly_recipe(part_num):
    """Gets the component recipe for a given assembly part_num."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT column_name, qty, category_id, legs FROM assembler WHERE part_num = %s"
        cursor.execute(query, (part_num,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error getting assembly recipe: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_assy_name_from_builder(diameter, column_name):
    """Gets the assy_name from the wire_rope_builder table for a given dia and column."""
    conn = get_connection()
    if not conn: return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = f"SELECT `{column_name}` FROM wire_rope_builder WHERE Dia = %s"
        cursor.execute(query, (diameter,))
        result = cursor.fetchone()
        return result[column_name] if result else None
    except Error as e:
        print(f"Error getting assy_name from builder: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_products_by_assy_name(assy_name):
    """Gets a list of all products that match a given assy_name, with defaults first."""
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT kdc_id, description1, default_assy FROM products WHERE assy_name = %s ORDER BY default_assy DESC, description1 ASC"
        cursor.execute(query, (assy_name,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error getting products by assy_name: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_working_loads(diameter):
    """Gets the SINGLE LEG WLL by looking up the EIPS and sw_factor for a given diameter."""
    conn = get_connection()
    if not conn: return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        design_factor = 5.0
        choker_factor = 0.75
        basket_factor = 2.0
        
        query = "SELECT eips, sw_factor FROM working_loads WHERE dia = %s"
        cursor.execute(query, (diameter,))
        result = cursor.fetchone()
        
        if not result or result.get('eips') is None or result.get('sw_factor') is None:
            return {'vertical': 0, 'choker': 0, 'basket': 0}
            
        breaking_strength_tons = float(result['eips'])
        swage_factor = float(result['sw_factor'])
        
        base_wll_tons = (breaking_strength_tons * swage_factor) / design_factor
        
        calculated_loads = {
            'vertical': base_wll_tons,
            'choker': base_wll_tons * choker_factor,
            'basket': base_wll_tons * basket_factor
        }
        return calculated_loads
        
    except Error as e:
        print(f"Error getting working loads: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_sling_angle_factors(legs):
    """Gets the WLL multipliers for multi-leg slings from the new table."""
    conn = get_connection()
    if not conn: return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM sling_angle_factors WHERE legs = %s"
        cursor.execute(query, (legs,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error getting sling angle factors: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
