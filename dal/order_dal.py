import mysql.connector
from mysql.connector import Error
from .db_connector import get_connection
import datetime

def search_products(search_term):
    conn = get_connection()
    if not conn: return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT kdc_id, stock_id, figure_num, description1, list_price FROM products WHERE (description1 LIKE %s OR stock_id LIKE %s OR figure_num LIKE %s OR pam_id LIKE %s) AND consignment <> 7 LIMIT 200;"
        search_pattern = f"%{search_term}%"
        cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
        return cursor.fetchall()
    except Error as e:
        print(f"Error searching products: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def create_sales_order(customer_id, employee_num, order_items, po_num, po_by, shipto_id, ship_date, ship_via, freight_charge):
    """Creates a new sales order, correctly grouping assembly components."""
    conn = get_connection()
    if not conn: return None
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(CAST(order_num AS UNSIGNED)) + 1 FROM orders")
        new_order_num = cursor.fetchone()[0]
        if not new_order_num: new_order_num = 350000

        order_header_query = "INSERT INTO orders (order_num, real_order_num, cust_id, shipto_id, employee_num, order_date, ship_date, po_num, po_by, ship_via, freight_charge) VALUES (%s, %s, %s, %s, %s, CURDATE(), %s, %s, %s, %s, %s)"
        cursor.execute(order_header_query, (str(new_order_num), new_order_num, customer_id, shipto_id, employee_num, ship_date, po_num, po_by, ship_via, freight_charge))

        assy_id_counter = 0
        current_assy_id = 0
        for item in order_items:
            if item.get('is_main_assembly') or not item.get('comment', '').startswith('Component for'):
                assy_id_counter += 1
            
            current_assy_id = assy_id_counter

            now = datetime.datetime.now()
            comment_id = f"S{now.strftime('%y%j%H%M%S')}-{employee_num}-{current_assy_id}"
            if item.get('comment'):
                cursor.execute("INSERT INTO comments (comment_num, comment_content) VALUES (%s, %s)", (comment_id, item['comment']))

            qty, price = item.get('qty', 1), item.get('unit_price', 0)
            ext_price = qty * price
            testwo_flag = 1 if item.get('test_load') else 0

            order_detail_query = "INSERT INTO orders_detail (order_num, real_order_num, assy_id, kdc_id, qty, unit_price, ext_price, comment_id, q_p_s2, testwo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            detail_tuple = (str(new_order_num), new_order_num, current_assy_id, item['kdc_id'], qty, price, ext_price, comment_id, 3, testwo_flag)
            cursor.execute(order_detail_query, detail_tuple)

            if testwo_flag == 1:
                test_tuple = (str(new_order_num), current_assy_id, item.get('rated_load', ''), item.get('test_load'), 3)
                cursor.execute("INSERT INTO testing_wo (order_num3, assy_id3, rated_load, test_load, q_p_s3) VALUES (%s, %s, %s, %s, %s)", test_tuple)

            product_trans_query = "INSERT INTO product_trans (order_num, kdc_id, assy_id, units_sold, q_p_s, employee_num, trans_date) VALUES (%s, %s, %s, %s, %s, %s, CURDATE())"
            trans_tuple = (str(new_order_num), item['kdc_id'], current_assy_id, qty, 3, employee_num)
            cursor.execute(product_trans_query, trans_tuple)

        conn.commit()
        print(f"Successfully created Sales Order: {new_order_num}")
        return new_order_num
    except Error as e:
        print(f"Error creating sales order: {e}")
        conn.rollback()
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def create_purchase_order(vendor_id, employee_num, order_items):
    # ... (This function is complete and correct)
    pass

def search_all_sales_orders(search_term):
    # ... (This function is complete and correct)
    pass

def get_order_header(order_num):
    # ... (This function is complete and correct)
    pass

def get_order_line_items(order_num):
    # ... (This function is complete and correct)
    pass
