import customtkinter as ctk
from dal.order_dal import search_products # Reuse the existing product search
from dal.product_dal import get_product_by_id, update_product

class ProductEditorWindow(ctk.CTkToplevel):
    """The pop-up window for editing a single product."""
    def __init__(self, master, kdc_id):
        super().__init__(master)
        self.title("Edit Product")
        self.geometry("400x250")
        
        self.kdc_id = kdc_id

        self.grid_columnconfigure(1, weight=1)

        # -- Widgets --
        self.desc_label = ctk.CTkLabel(self, text="Description:")
        self.desc_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.desc_entry = ctk.CTkEntry(self)
        self.desc_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        self.price_label = ctk.CTkLabel(self, text="List Price:")
        self.price_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.price_entry = ctk.CTkEntry(self)
        self.price_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.cost_label = ctk.CTkLabel(self, text="Unit Cost:")
        self.cost_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.cost_entry = ctk.CTkEntry(self)
        self.cost_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # -- Buttons --
        self.save_button = ctk.CTkButton(self, text="Save Changes", command=self.save_product)
        self.save_button.grid(row=3, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
        
        self.load_product_data()
        self.grab_set()

    def load_product_data(self):
        product = get_product_by_id(self.kdc_id)
        if product:
            self.desc_entry.insert(0, product.get('description1', ''))
            self.price_entry.insert(0, product.get('list_price', '0.00'))
            self.cost_entry.insert(0, product.get('unit_cost', '0.00'))

    def save_product(self):
        product_data = {
            'kdc_id': self.kdc_id,
            'description1': self.desc_entry.get(),
            'list_price': self.price_entry.get(),
            'unit_cost': self.cost_entry.get()
        }
        success = update_product(product_data)
        if success:
            print(f"Product {self.kdc_id} updated successfully.")
            # Refresh the search in the parent window
            self.master.display_product_search_results()
            self.destroy()
        else:
            print(f"Failed to update product {self.kdc_id}.")


class ProductManagementWindow(ctk.CTkToplevel):
    """The main window for searching and selecting products to edit."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Product Management")
        self.geometry("800x600")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # --- Search Frame ---
        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search products...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        self.search_button = ctk.CTkButton(self.search_frame, text="Search", command=self.display_product_search_results)
        self.search_button.pack(side="left", padx=5, pady=5)

        # --- Results Frame ---
        self.results_frame = ctk.CTkScrollableFrame(self, label_text="Search Results")
        self.results_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def display_product_search_results(self):
        search_term = self.search_entry.get()
        if not search_term: return

        for widget in self.results_frame.winfo_children():
            widget.destroy()

        products = search_products(search_term)
        for product in products:
            button_text = f"{product['kdc_id']} - {product['description1']}"
            button = ctk.CTkButton(
                self.results_frame,
                text=button_text,
                command=lambda kdc_id=product['kdc_id']: self.open_product_editor(kdc_id)
            )
            button.pack(pady=4, padx=10, fill="x")
            
    def open_product_editor(self, kdc_id):
        editor_win = ProductEditorWindow(self, kdc_id=kdc_id)
