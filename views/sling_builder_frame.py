import customtkinter as ctk
import math
from dal.assembly_dal import get_wirerope_diameters, get_assembly_part_numbers, get_assembly_recipe, get_assy_name_from_builder, get_products_by_assy_name, get_working_loads, get_sling_angle_factors
from dal.product_dal import get_product_by_id, get_product_by_part_num
from views.sales_order_view import SalesOrderWindow

class SlingBuilderFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.component_choice_widgets = {}
        self.final_bom_components = []
        self.main_assembly_item = None
        self.recipe = []
        self.final_loads = {}
        self.column_map = {'V': 'Sleeve', 'S': 'Shackle', 'T': 'Thimble', 'M1': '1-Leg Link', 'M2': '2-Leg Link', 'M3': '3-Leg Link', 'M4': '4-Leg Link', 'H': 'Hook'}

        # Main 3-Column Grid Layout
        self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=2); self.grid_columnconfigure(2, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # Column 1: Configuration
        self.col1_frame = ctk.CTkFrame(self)
        self.col1_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.col1_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.col1_frame, text="1. Configure Assembly", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkLabel(self.col1_frame, text="Assembly Part Number:").grid(row=1, column=0, padx=10, pady=(10,0), sticky="w")
        self.part_num_combo = ctk.CTkComboBox(self.col1_frame, values=get_assembly_part_numbers())
        self.part_num_combo.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(self.col1_frame, text="Wire Diameter (Fractional):").grid(row=3, column=0, padx=10, pady=(10,0), sticky="w")
        self.dia_combo = ctk.CTkComboBox(self.col1_frame, values=[str(d) for d in get_wirerope_diameters()])
        self.dia_combo.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(self.col1_frame, text="Quantity of Assemblies:").grid(row=5, column=0, padx=10, pady=(10,0), sticky="w")
        self.qty_entry = ctk.CTkEntry(self.col1_frame)
        self.qty_entry.grid(row=6, column=0, padx=10, pady=5, sticky="ew")
        self.qty_entry.insert(0, "1")
        ctk.CTkLabel(self.col1_frame, text="Finished Length:").grid(row=7, column=0, padx=10, pady=(10,0), sticky="w")
        self.length_frame = ctk.CTkFrame(self.col1_frame, fg_color="transparent")
        self.length_frame.grid(row=8, column=0, padx=10, pady=5, sticky="ew")
        self.length_ft_entry = ctk.CTkEntry(self.length_frame, placeholder_text="Feet")
        self.length_ft_entry.pack(side="left", padx=(0,5), expand=True, fill="x")
        self.length_in_entry = ctk.CTkEntry(self.length_frame, placeholder_text="Inches")
        self.length_in_entry.pack(side="left", padx=(5,0), expand=True, fill="x")
        self.load_recipe_button = ctk.CTkButton(self.col1_frame, text="Load Components ->", command=self.load_recipe)
        self.load_recipe_button.grid(row=9, column=0, padx=10, pady=20, sticky="ew")

        # Column 2: Component Selection
        self.col2_frame = ctk.CTkScrollableFrame(self, label_text="2. Select Specific Components")
        self.col2_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Column 3: Final Details & BOM
        self.col3_frame = ctk.CTkScrollableFrame(self, label_text="3. Final Details & BOM")
        self.col3_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        self.col3_frame.grid_columnconfigure(1, weight=1)

        # Bottom Action Buttons
        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        self.action_frame.grid_columnconfigure((0,1), weight=1)
        self.generate_bom_button = ctk.CTkButton(self.action_frame, text="Generate BOM", command=self.generate_bom, state="disabled")
        self.generate_bom_button.grid(row=0, column=0, padx=5, sticky="ew")
        self.create_so_button = ctk.CTkButton(self.action_frame, text="Create Sales Order", command=self.create_sales_order, state="disabled")
        self.create_so_button.grid(row=0, column=1, padx=5, sticky="ew")

    def load_recipe(self):
        for widget in self.col2_frame.winfo_children(): widget.destroy()
        self.component_choice_widgets = {}
        self.generate_bom_button.configure(state="normal")
        self.create_so_button.configure(state="disabled")

        part_num = self.part_num_combo.get()
        diameter = self.dia_combo.get()
        
        self.recipe = get_assembly_recipe(part_num)
        if not self.recipe: return
            
        for recipe_item in self.recipe:
            column_code = recipe_item['column_name']
            component_class = self.column_map.get(column_code.strip(), "Unknown")
            ctk.CTkLabel(self.col2_frame, text=f"{component_class} (Qty per assy: {recipe_item['qty']}):").pack(anchor="w", padx=10, pady=(10,0))
            assy_name = get_assy_name_from_builder(diameter, column_code)
            if not assy_name:
                ctk.CTkLabel(self.col2_frame, text="No parts defined.").pack(anchor="w", padx=10, pady=5)
                continue

            options = get_products_by_assy_name(assy_name)
            option_strings = [f"{opt['kdc_id']}: {opt['description1']}" for opt in options]
            is_default = options[0]['default_assy'] == 1 if options else False
            
            row_frame = ctk.CTkFrame(self.col2_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=5)
            row_frame.grid_columnconfigure(0, weight=1)
            combo = ctk.CTkComboBox(row_frame, values=option_strings)
            combo.grid(row=0, column=0, sticky="ew")
            override_check = ctk.CTkCheckBox(row_frame, text="Override", command=lambda c=combo: self._on_override_toggle(c))
            override_check.grid(row=0, column=1, padx=(10,0))
            if option_strings: combo.set(option_strings[0])
            if is_default: combo.configure(state="disabled")
            else: override_check.select()
            self.component_choice_widgets[column_code] = {'combo': combo, 'recipe_item': recipe_item}

    def _on_override_toggle(self, combobox):
        if combobox.cget("state") == "disabled": combobox.configure(state="normal")
        else: combobox.configure(state="disabled")

    def _fraction_to_float(self, frac_str):
        try:
            if not frac_str: return 0.0
            if "-" in frac_str:
                parts = frac_str.split('-')
                return float(parts[0]) + (float(eval(parts[1])) if len(parts) > 1 and parts[1] else 0)
            return float(eval(frac_str))
        except (ValueError, TypeError, SyntaxError):
            try: return float(frac_str)
            except: return 0.0

    def _round_capacity(self, capacity_tons):
        """Rounds down a capacity in tons per industry standards."""
        if capacity_tons <= 0: return 0.0
        if capacity_tons < 10: return math.floor(capacity_tons * 10) / 10.0
        else: return math.floor(capacity_tons)

    def _calculate_wirerope_adder(self, diameter_str):
        diameter_float = self._fraction_to_float(diameter_str)
        if diameter_float == 0: return 0
        length = diameter_float / 0.0625
        width = length / 2
        st_eye = 6 * diameter_float
        return (length + width + st_eye) / 12

    def generate_bom(self):
        self.final_bom_components = []
        for widget in self.col3_frame.winfo_children(): widget.destroy()
        try:
            num_assemblies = int(self.qty_entry.get())
            len_ft = float(self.length_ft_entry.get() or 0)
            len_in = float(self.length_in_entry.get() or 0)
            finished_length_ft = len_ft + (len_in / 12)
            diameter = self.dia_combo.get()
            part_num = self.part_num_combo.get()
        except ValueError:
            print("Invalid number in input fields."); return

        assy_legs = self.recipe[0].get('legs') if self.recipe else 1
        
        single_leg_loads = get_working_loads(diameter) or {}
        single_leg_vertical_wll_tons = single_leg_loads.get('vertical', 0)
        
        wll_text = ""
        if assy_legs == 1:
            self.final_loads = single_leg_loads
            v_tons = self._round_capacity(self.final_loads.get('vertical', 0))
            c_tons = self._round_capacity(self.final_loads.get('choker', 0))
            b_tons = self._round_capacity(self.final_loads.get('basket', 0))
            wll_text = f"WLL (Tons): Vertical: {v_tons} | Choker: {c_tons} | Basket: {b_tons}"
        else:
            angle_factors = get_sling_angle_factors(assy_legs) or {}
            wll_at_60_tons = single_leg_vertical_wll_tons * float(angle_factors.get('factor_60_deg', 0))
            wll_at_45_tons = single_leg_vertical_wll_tons * float(angle_factors.get('factor_45_deg', 0))
            wll_at_30_tons = single_leg_vertical_wll_tons * float(angle_factors.get('factor_30_deg', 0))
            wll_60_rounded = self._round_capacity(wll_at_60_tons)
            wll_45_rounded = self._round_capacity(wll_at_45_tons)
            wll_30_rounded = self._round_capacity(wll_at_30_tons)
            self.final_loads = {'60_deg': wll_60_rounded, '45_deg': wll_45_rounded, '30_deg': wll_30_rounded}
            wll_text = f"WLL (Tons): 60°: {wll_60_rounded} | 45°: {wll_45_rounded} | 30°: {wll_30_rounded}"
        
        self.main_assembly_item = get_product_by_part_num(part_num)
        total_assembly_cost = 0.0
        
        for column_code, choice in self.component_choice_widgets.items():
            selected_string = choice['combo'].get()
            if not selected_string or ":" not in selected_string: continue
            kdc_id = int(selected_string.split(':')[0])
            component_product = get_product_by_id(kdc_id)
            if not component_product: continue
            
            qty_per_assy = choice['recipe_item']['qty']
            if component_product.get('category_id') == 4:
                adder_ft = self._calculate_wirerope_adder(diameter)
                cut_length = finished_length_ft + adder_ft
                component_product['qty'] = (cut_length * qty_per_assy) * num_assemblies
            elif not column_code.startswith('M'):
                component_product['qty'] = (qty_per_assy * assy_legs) * num_assemblies
            else:
                component_product['qty'] = qty_per_assy * num_assemblies
            
            component_cost = float(component_product.get('unit_cost', 0) or 0)
            total_assembly_cost += component_cost * (component_product['qty'] / num_assemblies if num_assemblies > 0 else 1)
            self.final_bom_components.append(component_product)

        if self.main_assembly_item:
            desc1 = self.main_assembly_item.get('description1', '')
            desc2 = self.main_assembly_item.get('description2', '') or ''
            default_desc = f"{diameter}\" x {int(len_ft)}' {int(len_in)}\" {desc1} {desc2}\n{wll_text}"
            self.main_assembly_item['qty'] = num_assemblies
            self.main_assembly_item['unit_price'] = total_assembly_cost
            
            ctk.CTkLabel(self.col3_frame, text="Assembly Description (Editable):", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, columnspan=2, sticky="w", padx=10)
            self.description_textbox = ctk.CTkTextbox(self.col3_frame, height=100)
            self.description_textbox.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
            self.description_textbox.insert("1.0", default_desc)
            
            test_load_tons = single_leg_vertical_wll_tons * 2
            ctk.CTkLabel(self.col3_frame, text="Test / Proof Load (Tons):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
            self.test_load_entry = ctk.CTkEntry(self.col3_frame)
            self.test_load_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
            self.test_load_entry.insert(0, f"{test_load_tons:.2f}")
            
            ctk.CTkLabel(self.col3_frame, text="Sales Price (Unit):").grid(row=5, column=0, padx=10, pady=5, sticky="w")
            self.price_entry = ctk.CTkEntry(self.col3_frame, placeholder_text="Enter Unit Price")
            self.price_entry.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
            if self.main_assembly_item: self.price_entry.insert(0, f"{self.main_assembly_item['unit_price']:.2f}")
            self.price_entry.bind("<KeyRelease>", self.update_extended_price)
            
            ctk.CTkLabel(self.col3_frame, text="Extended Price:").grid(row=6, column=0, padx=10, pady=5, sticky="w")
            self.ext_price_label = ctk.CTkLabel(self.col3_frame, text="$0.00")
            self.ext_price_label.grid(row=6, column=1, padx=10, pady=5, sticky="w")
            
            ctk.CTkLabel(self.col3_frame, text="Components:", font=ctk.CTkFont(weight="bold")).grid(row=7, column=0, columnspan=2, sticky="w", padx=10, pady=(10,0))
        
            for i, comp in enumerate(self.final_bom_components):
                display_text = f"  - Qty: {comp['qty']:.2f} --- {comp['description1']}"
                ctk.CTkLabel(self.col3_frame, text=display_text).grid(row=8+i, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        
        self.create_so_button.configure(state="normal")
        self.update_extended_price()

    def update_extended_price(self, event=None):
        try:
            qty = int(self.qty_entry.get())
            price = float(self.price_entry.get())
            self.ext_price_label.configure(text=f"${qty * price:.2f}")
        except (ValueError, TypeError):
            self.ext_price_label.configure(text="$0.00")

    def create_sales_order(self):
        """Creates a new sales order window and passes the BOM to it."""
        items_for_order = []
        if self.main_assembly_item:
            self.main_assembly_item['description1'] = self.description_textbox.get("1.0", "end-1c").strip()
            self.main_assembly_item['comment'] = self.description_textbox.get("1.0", "end-1c").strip()
            self.main_assembly_item['unit_price'] = float(self.price_entry.get() or 0)
            
            assy_legs = self.recipe[0].get('legs') if self.recipe else 1
            if assy_legs == 1:
                self.main_assembly_item['rated_load'] = f"Vertical: {self._round_capacity(self.final_loads.get('vertical', 0))} Tons"
            else:
                self.main_assembly_item['rated_load'] = f"60°: {self.final_loads.get('60_deg', 0)} Tons"
                
            self.main_assembly_item['test_load'] = self.test_load_entry.get()
            self.main_assembly_item['is_main_assembly'] = True
            items_for_order.append(self.main_assembly_item)
        
        for item in self.final_bom_components:
            line_item = item.copy()
            line_item['unit_price'] = 0
            line_item['comment'] = f"Component for {self.part_num_combo.get()}"
            items_for_order.append(line_item)
        
        sales_order_win = SalesOrderWindow(self.master, initial_items=items_for_order)
        sales_order_win.grab_set()
