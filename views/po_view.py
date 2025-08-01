import customtkinter as ctk
from dal.vendor_dal import search_vendors
from dal.order_dal import create_purchase_order

class PurchaseOrderWindow(ctk.CTkToplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Purchase Order")
        self.geometry("800x600")

        self.selected_vendor = None
        self.po_items = []

        # --- Main Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- Vendor Selection ---
        self.vendor_frame = ctk.CTkFrame(self)
        self.vendor_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.vendor_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.vendor_frame, text="Vendor Search:").grid(row=0, column=0, padx=10, pady=5)
        self.vendor_search_entry = ctk.CTkEntry(self.vendor_frame)
        self.vendor_search_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.vendor_search_button = ctk.CTkButton(self.vendor_frame, text="Search", command=self.display_vendor_search_results)
        self.vendor_search_button.grid(row=0, column=2, padx=10, pady=5)
        self.selected_vendor_label = ctk.CTkLabel(self.vendor_frame, text="No Vendor Selected", text_color="yellow")
        self.selected_vendor_label.grid(row=1, column=0, columnspan=3, padx=10, pady=5)

        # --- Search Results ---
        self.vendor_results_frame = ctk.CTkScrollableFrame(self, label_text="Search Results")
        self.vendor_results_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # --- PO Items ---
        self.po_items_frame = ctk.CTkScrollableFrame(self, label_text="PO Items")
        self.po_items_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # --- Save Button ---
        self.save_button = ctk.CTkButton(self, text="Save Purchase Order", command=self.save_po)
        self.save_button.grid(row=3, column=0, padx=10, pady=10)

    def display_vendor_search_results(self):
        search_term = self.vendor_search_entry.get()
        if not search_term: return
        for widget in self.vendor_results_frame.winfo_children():
            widget.destroy()
        
        vendors = search_vendors(search_term)
        for vendor in vendors:
            button = ctk.CTkButton(self.vendor_results_frame, text=f"{vendor['id_vendor']} - {vendor['vendor_name']}",
                                  command=lambda v=vendor: self.select_vendor(v))
            button.pack(pady=4, padx=10, fill="x")

    def select_vendor(self, vendor_data):
        self.selected_vendor = vendor_data
        self.selected_vendor_label.configure(text=f"Selected: {self.selected_vendor['vendor_name']}", text_color="lightgreen")

    def save_po(self):
        if not self.selected_vendor:
            print("ERROR: A vendor must be selected.")
            return
        
        # In a real scenario, you'd populate self.po_items
        # For now, we'll use a placeholder
        placeholder_items = [
            {'kdc_id': 12345, 'qty': 10, 'unit_cost': 5.99},
            {'kdc_id': 67890, 'qty': 2, 'unit_cost': 199.95}
        ]
        self.po_items = placeholder_items

        if not self.po_items:
            print("ERROR: No items in the purchase order.")
            return

        employee_num = self.master.current_user['EmployeeNum']
        new_po_num = create_purchase_order(self.selected_vendor['id_vendor'], employee_num, self.po_items)

        if new_po_num:
            print(f"Purchase Order {new_po_num} saved successfully!")
            self.destroy()
        else:
            print("Failed to save the purchase order.")
