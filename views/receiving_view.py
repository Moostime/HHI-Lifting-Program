import customtkinter as ctk
from dal.receiving_dal import find_open_purchase_orders, get_po_line_items, receive_po_items

class ReceivingWindow(ctk.CTkToplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Receive Purchase Order")
        self.geometry("1000x600")
        
        self.selected_po = None
        self.line_item_widgets = [] # To keep track of the entry boxes

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2) # Make the details panel wider
        self.grid_rowconfigure(0, weight=1)

        # --- 1. PO Search Frame (Left) ---
        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.search_frame.grid_rowconfigure(2, weight=1)

        self.po_search_label = ctk.CTkLabel(self.search_frame, text="1. Find Purchase Order", font=ctk.CTkFont(size=16, weight="bold"))
        self.po_search_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        self.po_search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search by PO number...")
        self.po_search_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.po_search_button = ctk.CTkButton(self.search_frame, text="Search", command=self.display_po_search_results)
        self.po_search_button.grid(row=1, column=1, padx=10, pady=5)

        self.po_results_frame = ctk.CTkScrollableFrame(self.search_frame, label_text="Open POs")
        self.po_results_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # --- 2. PO Details Frame (Right) ---
        self.details_frame = ctk.CTkFrame(self)
        self.details_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.details_frame.grid_rowconfigure(1, weight=1)
        
        self.details_label = ctk.CTkLabel(self.details_frame, text="2. Receive Items", font=ctk.CTkFont(size=16, weight="bold"))
        self.details_label.grid(row=0, column=0, padx=10, pady=10)

        self.line_items_frame = ctk.CTkScrollableFrame(self.details_frame, label_text="Line Items")
        self.line_items_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.receive_button = ctk.CTkButton(self.details_frame, text="Receive Selected Items", command=self.receive_items)
        self.receive_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    def display_po_search_results(self):
        search_term = self.po_search_entry.get()

        for widget in self.po_results_frame.winfo_children():
            widget.destroy()

        purchase_orders = find_open_purchase_orders(search_term)
        for po in purchase_orders:
            button_text = f"{po['order_num']} - {po['vendor_name']}"
            button = ctk.CTkButton(
                self.po_results_frame,
                text=button_text,
                command=lambda current_po=po: self.select_po(current_po)
            )
            button.pack(pady=4, padx=10, fill="x")

    def select_po(self, purchase_order_data):
        """Fetches and displays the line items for the selected PO."""
        self.selected_po = purchase_order_data
        po_num = self.selected_po['order_num']
        self.details_label.configure(text=f"2. Receive Items for PO #{po_num}")
        print(f"Selected PO: {po_num}")

        for widget in self.line_items_frame.winfo_children():
            widget.destroy()
        self.line_item_widgets = [] # Clear the old list of widgets

        line_items = get_po_line_items(po_num)
        for item in line_items:
            # Create a frame for each line item row
            item_frame = ctk.CTkFrame(self.line_items_frame)
            item_frame.pack(fill="x", padx=5, pady=5)
            
            item_text = f"Qty Ordered: {item['qty']} - {item['description1']}"
            
            # The parent of the label is 'item_frame'
            item_label = ctk.CTkLabel(item_frame, text=item_text, anchor="w")
            item_label.pack(side="left", padx=10, pady=5, fill="x", expand=True)
            
            qty_entry = ctk.CTkEntry(item_frame, width=70)
            qty_entry.insert(0, str(item['qty'])) # Pre-fill with ordered quantity
            qty_entry.pack(side="right", padx=10, pady=5)

            # Store the widget and its associated data for later
            self.line_item_widgets.append({"entry": qty_entry, "data": item})

    def receive_items(self):
        if not self.selected_po:
            print("No Purchase Order selected.")
            return

        received_items = []
        for widget_info in self.line_item_widgets:
            try:
                received_qty = int(widget_info['entry'].get())
                if received_qty > 0:
                    item_data = widget_info['data']
                    item_data['received_qty'] = received_qty
                    received_items.append(item_data)
            except ValueError:
                print(f"Invalid quantity for item {widget_info['data']['kdc_id']}. Skipping.")

        if not received_items:
            print("No items with a valid quantity to receive.")
            return
            
        employee_num = 999
        success = receive_po_items(self.selected_po['order_num'], received_items, employee_num)

        if success:
            print("PO successfully received!")
            self.destroy()
        else:
            print("Failed to receive PO.")
