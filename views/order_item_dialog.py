import customtkinter as ctk

class OrderItemDialog(ctk.CTkToplevel):
    def __init__(self, master, product_data, existing_details=None):
        super().__init__(master)
        self.title(f"Add/Edit {product_data.get('stock_id', '')}")
        self.geometry("450x550")

        self._product_data = product_data
        self.result = None

        self.grid_columnconfigure(1, weight=1)

        # --- Main Details ---
        self.qty_label = ctk.CTkLabel(self, text="Quantity:")
        self.qty_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.qty_entry = ctk.CTkEntry(self)
        self.qty_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        self.price_label = ctk.CTkLabel(self, text="Unit Price:")
        self.price_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.price_entry = ctk.CTkEntry(self)
        self.price_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.comment_label = ctk.CTkLabel(self, text="Comment:")
        self.comment_label.grid(row=2, column=0, padx=10, pady=10, sticky="nw")
        self.comment_textbox = ctk.CTkTextbox(self, height=80)
        self.comment_textbox.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # --- Testing Requirements Frame ---
        self.test_frame = ctk.CTkFrame(self)
        self.test_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.test_frame.grid_columnconfigure(1, weight=1)
        
        self.test_label = ctk.CTkLabel(self.test_frame, text="Testing Requirements", font=ctk.CTkFont(weight="bold"))
        self.test_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        self.rated_load_label = ctk.CTkLabel(self.test_frame, text="Rated Load:")
        self.rated_load_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.rated_load_entry = ctk.CTkEntry(self.test_frame)
        self.rated_load_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.test_load_label = ctk.CTkLabel(self.test_frame, text="Test Load:")
        self.test_load_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.test_load_entry = ctk.CTkEntry(self.test_frame)
        self.test_load_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        # --- Buttons ---
        self.ok_button = ctk.CTkButton(self, text="OK", command=self._ok_event)
        self.ok_button.grid(row=4, column=0, padx=10, pady=20)
        
        self.cancel_button = ctk.CTkButton(self, text="Cancel", command=self._cancel_event)
        self.cancel_button.grid(row=4, column=1, padx=10, pady=20)
        
        if existing_details:
            self.qty_entry.insert(0, existing_details.get("qty", "1"))
            self.price_entry.insert(0, str(existing_details.get("unit_price", "0.00")))
            self.comment_textbox.insert("1.0", existing_details.get("comment", ""))
            
            # Safely insert rated_load and test_load, converting None to ""
            rated_load = existing_details.get("rated_load") or ""
            test_load = existing_details.get("test_load") or ""
            self.rated_load_entry.insert(0, rated_load)
            self.test_load_entry.insert(0, test_load)
        else:
            self.qty_entry.insert(0, "1")
            self.price_entry.insert(0, str(product_data.get('list_price', '0.00')))
        
        self.grab_set()
        self.wait_window()

    def _ok_event(self, event=None):
        try:
            self.result = {
                "qty": int(self.qty_entry.get()),
                "unit_price": float(self.price_entry.get()),
                "comment": self.comment_textbox.get("1.0", "end-1c"),
                "rated_load": self.rated_load_entry.get(),
                "test_load": self.test_load_entry.get()
            }
        except (ValueError, TypeError):
            self.result = None
        self.destroy()

    def _cancel_event(self):
        self.result = None
        self.destroy()

    def get_input(self):
        return self.result
