import customtkinter as ctk
from dal.customer_dal import search_customers, get_shipping_addresses
from dal.order_dal import search_products, create_sales_order, get_order_header, get_order_line_items
from views.order_item_dialog import OrderItemDialog
from pdf.pdf_generator import create_work_order_pdf
# Note: The assembly builder is no longer opened from here, it's part of the main view
import os
import subprocess
import sys
import datetime


class SalesOrderWindow(ctk.CTkToplevel):
    def __init__(self, master, order_to_load=None, initial_items=None, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Sales Order")
        self.geometry("1200x800")
        
        self.current_order_items = initial_items if initial_items else []
        self.selected_customer = None
        self.selected_shipping_address = None
        self.shipping_addresses = []
        self.selected_item_index = ctk.StringVar()

        # --- Main Grid Layout & Frames ---
        self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=1); self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.customer_frame = ctk.CTkFrame(self); self.customer_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")
        self.customer_frame.grid_rowconfigure(3, weight=1)
        self.product_frame = ctk.CTkFrame(self); self.product_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")
        self.product_frame.grid_rowconfigure(3, weight=1)
        self.order_frame = ctk.CTkFrame(self); self.order_frame.grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky="nsew")
        self.order_frame.grid_rowconfigure(1, weight=1)

        # --- Customer & Order Info Widgets ---
        self.customer_label = ctk.CTkLabel(self.customer_frame, text="1. Select Customer", font=ctk.CTkFont(size=16, weight="bold")); self.customer_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.customer_search_entry = ctk.CTkEntry(self.customer_frame, placeholder_text="Search customers..."); self.customer_search_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.customer_search_button = ctk.CTkButton(self.customer_frame, text="Search", command=self.display_customer_search_results); self.customer_search_button.grid(row=1, column=1, padx=10, pady=5)
        self.selected_customer_label = ctk.CTkLabel(self.customer_frame, text="No Customer Selected", text_color="yellow"); self.selected_customer_label.grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        self.customer_results_frame = ctk.CTkScrollableFrame(self.customer_frame, label_text="Results"); self.customer_results_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        self.header_frame = ctk.CTkFrame(self.customer_frame); self.header_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)
        self.po_label = ctk.CTkLabel(self.header_frame, text="PO Number:"); self.po_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.po_entry = ctk.CTkEntry(self.header_frame); self.po_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.poby_label = ctk.CTkLabel(self.header_frame, text="Ordered By:"); self.poby_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.poby_entry = ctk.CTkEntry(self.header_frame); self.poby_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.ship_date_label = ctk.CTkLabel(self.header_frame, text="Ship Date (YYYY-MM-DD):"); self.ship_date_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.ship_date_entry = ctk.CTkEntry(self.header_frame); self.ship_date_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.ship_date_entry.insert(0, (datetime.date.today() + datetime.timedelta(days=10)).strftime('%Y-%m-%d'))
        
        self.shipping_addr_label = ctk.CTkLabel(self.customer_frame, text="Ship-To Address:"); self.shipping_addr_label.grid(row=5, column=0, padx=10, pady=(10,0), sticky="w")
        self.shipping_addr_combo = ctk.CTkComboBox(self.customer_frame, values=["Select a customer first"], state="disabled", command=self.display_selected_address); self.shipping_addr_combo.grid(row=5, column=1, padx=10, pady=(10,0), sticky="ew")
        self.address_display_frame = ctk.CTkFrame(self.customer_frame, fg_color="transparent"); self.address_display_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.selected_address_label = ctk.CTkLabel(self.address_display_frame, text="", justify="left", anchor="w"); self.selected_address_label.pack(anchor="w")

        self.shipping_frame = ctk.CTkFrame(self.customer_frame); self.shipping_frame.grid(row=7, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.shipping_frame.grid_columnconfigure((0,1), weight=1)
        self.ship_method_frame = ctk.CTkFrame(self.shipping_frame); self.ship_method_frame.grid(row=0, column=0, padx=(0,5), sticky="nsew")
        ctk.CTkLabel(self.ship_method_frame, text="Ship Method").pack(anchor="w", padx=10)
        self.ship_method_var = ctk.StringVar(value="Will Call")
        ctk.CTkRadioButton(self.ship_method_frame, text="Will Call", variable=self.ship_method_var, value="Will Call").pack(anchor="w", padx=10)
        ctk.CTkRadioButton(self.ship_method_frame, text="Motor Freight", variable=self.ship_method_var, value="Motor Freight").pack(anchor="w", padx=10)
        ctk.CTkRadioButton(self.ship_method_frame, text="UPS", variable=self.ship_method_var, value="UPS").pack(anchor="w", padx=10)
        self.freight_frame = ctk.CTkFrame(self.shipping_frame); self.freight_frame.grid(row=0, column=1, padx=(5,0), sticky="nsew")
        ctk.CTkLabel(self.freight_frame, text="Freight Charge").pack(anchor="w", padx=10)
        self.freight_charge_var = ctk.StringVar(value="Collect")
        ctk.CTkRadioButton(self.freight_frame, text="Collect", variable=self.freight_charge_var, value="Collect").pack(anchor="w", padx=10)
        ctk.CTkRadioButton(self.freight_frame, text="PP/ADD", variable=self.freight_charge_var, value="PP/ADD").pack(anchor="w", padx=10)
        ctk.CTkRadioButton(self.freight_frame, text="Allowed", variable=self.freight_charge_var, value="Allowed").pack(anchor="w", padx=10)

        # --- Product Search Widgets ---
        self.product_label = ctk.CTkLabel(self.product_frame, text="2. Add Products", font=ctk.CTkFont(size=16, weight="bold")); self.product_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.product_search_entry = ctk.CTkEntry(self.product_frame, placeholder_text="Search products..."); self.product_search_entry.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.product_search_button = ctk.CTkButton(self.product_frame, text="Search", command=self.display_product_search_results); self.product_search_button.grid(row=2, column=1, padx=10, pady=5)
        self.product_results_frame = ctk.CTkScrollableFrame(self.product_frame, label_text="Results"); self.product_results_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # --- Current Order Widgets ---
        self.order_label = ctk.CTkLabel(self.order_frame, text="3. Current Order", font=ctk.CTkFont(size=16, weight="bold")); self.order_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.order_items_frame = ctk.CTkScrollableFrame(self.order_frame, label_text="Line Items"); self.order_items_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.button_frame = ctk.CTkFrame(self.order_frame); self.button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.edit_item_button = ctk.CTkButton(self.button_frame, text="Edit Item", command=self.edit_order_item); self.edit_item_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.delete_item_button = ctk.CTkButton(self.button_frame, text="Delete Item", command=self.delete_order_item, fg_color="red"); self.delete_item_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.print_wo_button = ctk.CTkButton(self.button_frame, text="Print Work Order", command=self.print_work_order); self.print_wo_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.save_button = ctk.CTkButton(self.order_frame, text="Save Order", command=self.save_order); self.save_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        if order_to_load:
            self.load_existing_order(order_to_load)
        
        if self.current_order_items:
            self.refresh_order_display()

    def load_existing_order(self, order_num):
        header = get_order_header(order_num)
        items = get_order_line_items(order_num)
        if not header:
            print(f"Error: Could not find order header for {order_num}")
            return

        self.title(f"Viewing Order #{order_num}")
        self.po_entry.insert(0, header.get('po_num', ''))
        self.poby_entry.insert(0, header.get('po_by', ''))
        if header.get('ship_date'):
            self.ship_date_entry.insert(0, header.get('ship_date').strftime('%Y-%m-%d'))
        
        cust_id = header.get('cust_id')
        customers = search_customers(str(cust_id))
        if customers:
            self.select_customer(customers[0])
            ship_id_to_find = header.get('shipto_id')
            for i, addr in enumerate(self.shipping_addresses):
                if addr['id_shipto'] == ship_id_to_find:
                    choice = f"{addr['customer_name']} - {addr['address1']}"
                    self.shipping_addr_combo.set(choice)
                    self.display_selected_address(choice)
                    break
        
        self.current_order_items = []
        for item in items:
            try:
                unit_price = float(item.get('unit_price', 0))
                list_price = float(item.get('list_price', 0))
                qty = int(item.get('qty', 0))
            except (ValueError, TypeError):
                unit_price, list_price, qty = 0.0, 0.0, 0
            
            line_item = {
                'stock_id': item['stock_id'], 'description1': item['description1'],
                'kdc_id': item['kdc_id'], 'list_price': list_price, 'qty': qty, 
                'unit_price': unit_price, 'comment': item.get('comment_content', ''), 
                'rated_load': item.get('rated_load', ''), 'test_load': item.get('test_load', '')
            }
            self.current_order_items.append(line_item)
        
        self.refresh_order_display()
        self.save_button.configure(state="disabled", text="Saving Existing Order Not Implemented")

    def display_customer_search_results(self, event=None):
        search_term = self.customer_search_entry.get()
        if not search_term: return
        for widget in self.customer_results_frame.winfo_children(): widget.destroy()
        customers = search_customers(search_term)
        for customer in customers:
            button = ctk.CTkButton(self.customer_results_frame, text=f"{customer['cust_id']} - {customer['customer_name']}",
                                  command=lambda cust=customer: self.select_customer(cust))
            button.pack(pady=4, padx=10, fill="x")

    def select_customer(self, customer_data):
        self.selected_customer = customer_data
        self.selected_customer_label.configure(text=f"Selected: {self.selected_customer['customer_name']}", text_color="lightgreen")
        self.load_shipping_addresses(self.selected_customer['cust_id'])

    def load_shipping_addresses(self, cust_id):
        self.shipping_addresses = get_shipping_addresses(cust_id)
        if self.shipping_addresses:
            address_names = [f"{addr['customer_name']} - {addr['address1']}" for addr in self.shipping_addresses]
            self.shipping_addr_combo.configure(values=address_names, state="normal")
            self.shipping_addr_combo.set(address_names[0])
            self.display_selected_address(address_names[0])
        else:
            self.shipping_addr_combo.configure(values=["No shipping addresses found"], state="disabled")
            self.shipping_addr_combo.set("No shipping addresses found")
            self.selected_address_label.configure(text="")

    def display_selected_address(self, selected_choice):
        for addr in self.shipping_addresses:
            choice_text = f"{addr['customer_name']} - {addr['address1']}"
            if choice_text == selected_choice:
                self.selected_shipping_address = addr
                display_text = f"{addr['customer_name']}\n{addr['address1']}\n"
                if addr.get('address2'): display_text += f"{addr.get('address2')}\n"
                display_text += f"{addr['city']}, {addr['state']} {addr['zip']}"
                self.selected_address_label.configure(text=display_text)
                break
    
    def display_product_search_results(self, event=None):
        search_term = self.product_search_entry.get()
        if not search_term: return
        for widget in self.product_results_frame.winfo_children(): widget.destroy()
        products = search_products(search_term)
        for product in products:
            item_frame = ctk.CTkFrame(self.product_results_frame)
            item_frame.pack(fill="x", padx=5, pady=5)
            label_text = f"{product['stock_id']} - {product['description1']}"
            item_label = ctk.CTkLabel(item_frame, text=label_text, anchor="w")
            item_label.pack(side="left", padx=5, pady=5, fill="x", expand=True)
            item_label.bind("<Double-1>", lambda event, p=product: self.add_item_to_order(p))
            add_button = ctk.CTkButton(item_frame, text="Add", width=50, command=lambda p=product: self.add_item_to_order(p))
            add_button.pack(side="right", padx=5, pady=5)

    def add_item_to_order(self, product_data):
        dialog = OrderItemDialog(self, product_data)
        details = dialog.get_input()
        if details:
            line_item = product_data.copy()
            line_item['qty'] = details['qty']; line_item['unit_price'] = details['unit_price']
            line_item['comment'] = details['comment']; line_item['rated_load'] = details['rated_load']
            line_item['test_load'] = details['test_load']
            self.current_order_items.append(line_item)
            self.refresh_order_display()

    def refresh_order_display(self):
        for widget in self.order_items_frame.winfo_children(): widget.destroy()
        if self.current_order_items: self.selected_item_index.set("0")
        for i, item in enumerate(self.current_order_items):
            ext_price = item['qty'] * item['unit_price']
            desc_text = f"{item['qty']} x {item['description1']} @ ${item['unit_price']:.2f} = ${ext_price:.2f}"
            if item.get('comment'): desc_text += f"\n  Comment: {item['comment']}"
            if item.get('test_load'): desc_text += "\n  (Testing Required)"
            rb = ctk.CTkRadioButton(self.order_items_frame, text=desc_text, variable=self.selected_item_index, value=str(i))
            rb.pack(fill="x", padx=10, pady=5, anchor="w")

    def edit_order_item(self):
        try:
            index = int(self.selected_item_index.get())
            item_to_edit = self.current_order_items[index]
            dialog = OrderItemDialog(self, item_to_edit, existing_details=item_to_edit)
            details = dialog.get_input()
            if details:
                self.current_order_items[index]['qty'] = details['qty']; self.current_order_items[index]['unit_price'] = details['unit_price']
                self.current_order_items[index]['comment'] = details['comment']; self.current_order_items[index]['rated_load'] = details['rated_load']
                self.current_order_items[index]['test_load'] = details['test_load']
                self.refresh_order_display()
        except (ValueError, IndexError): print("No item selected or list is empty.")

    def delete_order_item(self):
        try:
            index = int(self.selected_item_index.get())
            self.current_order_items.pop(index)
            self.refresh_order_display()
        except (ValueError, IndexError): print("No item selected or list is empty.")
            
    def save_order(self):
        if not self.selected_customer or not self.selected_shipping_address:
            print("ERROR: A customer and shipping address must be selected."); return
        if not self.current_order_items:
            print("ERROR: No items in the order."); return
        employee_num = self.master.current_user['EmployeeNum']
        po_num, po_by, ship_date = self.po_entry.get(), self.poby_entry.get(), self.ship_date_entry.get()
        shipto_id = self.selected_shipping_address['id_shipto']
        ship_via, freight_charge = self.ship_method_var.get(), self.freight_charge_var.get()
        new_order_num = create_sales_order(self.selected_customer['cust_id'], employee_num, self.current_order_items,
                                           po_num, po_by, shipto_id, ship_date, ship_via, freight_charge)
        if new_order_num:
            print(f"Order {new_order_num} saved successfully!"); self.destroy()
        else: print("Failed to save the order.")

    def print_work_order(self):
        if not self.selected_customer: print("Please select a customer first."); return
        if not self.current_order_items: print("Please add items to the order first."); return
        filename = create_work_order_pdf(self.selected_customer, self.current_order_items)
        print(f"Work order saved to {filename}")
        try:
            if sys.platform == "win32": os.startfile(filename)
            elif sys.platform == "darwin": subprocess.call(["open", filename])
            else: subprocess.call(["xdg-open", filename])
        except Exception as e: print(f"Could not open file automatically: {e}")
