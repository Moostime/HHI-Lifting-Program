import customtkinter as ctk
from dal.order_dal import search_all_sales_orders
from views.sales_order_view import SalesOrderWindow

class OrderSearchWindow(ctk.CTkToplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Search Sales Orders")
        self.geometry("800x600")
        
        self.master_app = master

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Search Frame ---
        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.search_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search by Order #, PO #, or Customer Name...")
        self.search_entry.grid(row=0, column=0, padx=(10,5), pady=10, sticky="ew")
        self.search_button = ctk.CTkButton(self.search_frame, text="Search", command=self.display_search_results)
        self.search_button.grid(row=0, column=1, padx=(5,10), pady=10)

        # --- Results Frame ---
        self.results_frame = ctk.CTkScrollableFrame(self, label_text="Search Results")
        self.results_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        
        self.grab_set()

    def display_search_results(self):
        search_term = self.search_entry.get()
        if not search_term: return

        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        orders = search_all_sales_orders(search_term)
        
        if not orders:
            ctk.CTkLabel(self.results_frame, text="No orders found.").pack(padx=10, pady=10)
            return
            
        for order in orders:
            order_text = f"Order #{order['order_num']} - {order['customer_name']} - PO: {order['po_num']} - Date: {order['order_date']}"
            button = ctk.CTkButton(self.results_frame, text=order_text,
                                  command=lambda o=order['order_num']: self.open_order(o))
            button.pack(pady=4, padx=10, fill="x")

    def open_order(self, order_num):
        order_win = SalesOrderWindow(self.master_app, order_to_load=order_num)
        order_win.grab_set()