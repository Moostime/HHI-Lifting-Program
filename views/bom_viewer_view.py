import customtkinter as ctk
from dal.bom_dal import get_distinct_part_numbers, get_distinct_sizes_for_part_num, get_bom_by_sku

class BomViewerWindow(ctk.CTkToplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("BOM Viewer")
        self.geometry("800x600")

        self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        # --- Options Frame ---
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")
        self.options_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.options_frame, text="1. Select Assembly", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=10)
        
        ctk.CTkLabel(self.options_frame, text="Assembly Part Number:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.part_num_combo = ctk.CTkComboBox(self.options_frame, values=get_distinct_part_numbers(), command=self.on_part_num_selected)
        self.part_num_combo.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.options_frame, text="Component Size:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.size_combo = ctk.CTkComboBox(self.options_frame, values=["Select part number first"], state="disabled")
        self.size_combo.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        self.view_button = ctk.CTkButton(self.options_frame, text="View BOM", command=self.view_bom)
        self.view_button.grid(row=5, column=0, padx=10, pady=20, sticky="ew")
        
        # --- Results Frame ---
        self.results_frame = ctk.CTkScrollableFrame(self, label_text="Bill of Materials")
        self.results_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        
        self.grab_set()

    def on_part_num_selected(self, part_num):
        sizes = get_distinct_sizes_for_part_num(part_num)
        if sizes:
            self.size_combo.configure(values=[str(s) for s in sizes], state="normal")
            self.size_combo.set(str(sizes[0]))
        else:
            self.size_combo.configure(values=["No sizes found"], state="disabled")

    def view_bom(self):
        part_num = self.part_num_combo.get()
        size = self.size_combo.get()

        if not part_num or not size:
            print("Please select a part number and size.")
            return
            
        # The nu_sku from your table is a combination of the header kdc_id and the size
        # We will need to adjust the DAL if this logic is different
        # For now, we will assume a simplified lookup. A better SKU might be needed.
        # This is a conceptual part of the code that needs real data to perfect.
        # Let's search by part_num and size for now.
        
        # We need a function get_bom_by_part_and_size in bom_dal. For now we will adapt
        nu_sku_guess = f"{part_num}-{size}" # This is a guess at the SKU format
        print(f"Searching for BOM with SKU guess: {nu_sku_guess}")
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        bom = get_bom_by_sku(nu_sku_guess) # This might not work if SKU format is different
        if not bom:
             ctk.CTkLabel(self.results_frame, text="No components found for this SKU.").pack(anchor="w", padx=10)
             # Let's add a fallback search
             # bom = get_bom_by_part_and_size(part_num, size) -> would be a better function
             
        for item in bom:
            item_text = f"Qty: {item['per_assy_qty']} - {item['description1']}"
            ctk.CTkLabel(self.results_frame, text=item_text).pack(anchor="w", padx=10)
