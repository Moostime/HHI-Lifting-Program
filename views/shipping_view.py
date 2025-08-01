import customtkinter as ctk
from dal.shipping_dal import find_open_sales_orders, get_so_line_items, ship_so_items

class ShippingWindow(ctk.CTkToplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Ship Sales Order")
        self.geometry("1000x600")
        
        self.selected_so = None
        self.line_item_widgets = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # --- 1. SO Search Frame (Left) ---
        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.search_frame.grid_rowconfigure(2, weight=1)
        self.so_search_label = ctk.CTkLabel(self.search_frame, text="1. Find Sales Order", font=ctk.CTkFont(size=16, weight="bold"))
        self.so_search_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.so_search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search by SO# or PO#...")
        self.so_search_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.so_search_button = ctk.CTkButton(self.search_frame, text="Search", command=self.display_so_search_results)
        self.so_search_button.grid(row=1, column=1, padx=10, pady=5)
        self.so_results_frame = ctk.CTkScrollableFrame(self.search_frame, label_text="Open Sales Orders")
        self.so_results_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # --- 2. SO Details Frame (Right) ---
        self.details_frame = ctk.CTkFrame(self)
        self.details_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.details_frame.grid_rowconfigure(1, weight=1)
        self.details_label = ctk.CTkLabel(self.details_frame, text="2. Ship Items", font=ctk.CTkFont(size=16, weight="bold"))
        self.details_label.grid(row=0, column=0, padx=10, pady=10)
        self.line_items_frame = ctk.CTkScrollableFrame(self.details_frame, label_text="Line Items")
        self.line_items_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.ship_button = ctk.CTkButton(self.details_frame, text="Ship Selected Items", command=self.ship_items)
        self.ship_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    def display_so_search_results(self):
        search_term = self.so_search_entry.get()
        for widget in self.so_results_frame.winfo_children():
            widget.destroy()
        sales_orders = find_open_sales_orders(search_term)
        for so in sales_orders:
            button_text = f"{so['order_num']} - {so['customer_name']}"
            button = ctk.CTkButton(
                self.so_results_frame,
                text=button_text,
                command=lambda current_so=so: self.select_so(current_so)
            )
            button.pack(pady=4, padx=10, fill="x")

    def select_so(self, sales_order_data):
        self.selected_so = sales_order_data
        so_num = self.selected_so['order_num']
        self.details_label.configure(text=f"2. Ship Items for SO #{so_num}")
        
        for widget in self.line_items_frame.winfo_children():
            widget.destroy()
        self.line_item_widgets = []

        line_items = get_so_line_items(so_num)
        for item in line_items:
            item_frame = ctk.CTkFrame(self.line_items_frame)
            item_frame.pack(fill="x", padx=5, pady=5)
            
            item_text = f"Qty Ordered: {item['qty']} - {item['description1']}"
            item_label = ctk.CTkLabel(item_frame, text=item_text, anchor="w")
            item_label.pack(side="left", padx=10, pady=5, fill="x", expand=True)
            
            qty_entry = ctk.CTkEntry(item_frame, width=70)
            qty_entry.insert(0, str(item['qty']))
            qty_entry.pack(side="right", padx=10, pady=5)

            self.line_item_widgets.append({"entry": qty_entry, "data": item})

    def ship_items(self):
        if not self.selected_so:
            print("No Sales Order selected.")
            return

        shipped_items = []
        for widget_info in self.line_item_widgets:
            try:
                shipped_qty = int(widget_info['entry'].get())
                if shipped_qty > 0:
                    item_data = widget_info['data']
                    item_data['shipped_qty'] = shipped_qty
                    shipped_items.append(item_data)
            except ValueError:
                print(f"Invalid quantity for item {widget_info['data']['kdc_id']}. Skipping.")

        if not shipped_items:
            print("No items with a valid quantity to ship.")
            return
            
        employee_num = 999
        success = ship_so_items(self.selected_so['order_num'], shipped_items, employee_num)

        if success:
            print("SO successfully shipped!")
            self.destroy()
        else:
            print("Failed to ship SO.")
