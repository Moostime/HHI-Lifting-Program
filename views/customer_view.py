import customtkinter as ctk
from dal.customer_dal import update_customer, create_customer

class CustomerWindow(ctk.CTkToplevel):
    """The pop-up window for adding or editing a customer."""
    def __init__(self, master, customer_data=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.customer_data = customer_data
        self.title("Add/Modify Customer")
        self.geometry("450x350")
        self.grid_columnconfigure(1, weight=1)

        # -- Widgets --
        self.id_label = ctk.CTkLabel(self, text="Customer ID:")
        self.id_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.id_entry = ctk.CTkEntry(self)
        self.id_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        self.name_label = ctk.CTkLabel(self, text="Name:")
        self.name_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.name_entry = ctk.CTkEntry(self)
        self.name_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.address_label = ctk.CTkLabel(self, text="Address:")
        self.address_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.address_entry = ctk.CTkEntry(self)
        self.address_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        self.city_label = ctk.CTkLabel(self, text="City:")
        self.city_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.city_entry = ctk.CTkEntry(self)
        self.city_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        self.state_label = ctk.CTkLabel(self, text="State:")
        self.state_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.state_entry = ctk.CTkEntry(self)
        self.state_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        
        self.zip_label = ctk.CTkLabel(self, text="Zip:")
        self.zip_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.zip_entry = ctk.CTkEntry(self)
        self.zip_entry.grid(row=5, column=1, padx=10, pady=10, sticky="ew")

        # -- Buttons --
        self.save_button = ctk.CTkButton(self, text="Save", command=self.save_customer)
        self.save_button.grid(row=6, column=0, padx=10, pady=20)
        
        self.close_button = ctk.CTkButton(self, text="Close", command=self.destroy)
        self.close_button.grid(row=6, column=1, padx=10, pady=20)

        if self.customer_data:
            self.load_customer_info()

    def load_customer_info(self):
        self.id_entry.insert(0, self.customer_data.get('cust_id', ''))
        self.id_entry.configure(state="disabled")
        self.name_entry.insert(0, self.customer_data.get('customer_name', ''))
        self.address_entry.insert(0, self.customer_data.get('address1', ''))
        self.city_entry.insert(0, self.customer_data.get('city', ''))
        self.state_entry.insert(0, self.customer_data.get('state', ''))
        self.zip_entry.insert(0, self.customer_data.get('zip', ''))

    def save_customer(self):
        data = {
            'cust_id': self.id_entry.get(),
            'customer_name': self.name_entry.get(),
            'address1': self.address_entry.get(),
            'city': self.city_entry.get(),
            'state': self.state_entry.get(),
            'zip': self.zip_entry.get(),
        }
        if self.customer_data:
            update_customer(data)
        else:
            create_customer(data)
        
        # Note: This window no longer has a reference to the main app's search function.
        # We will need a better way to refresh the parent list in the future.
        self.destroy()
