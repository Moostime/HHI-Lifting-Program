# /views/reporting_view.py

import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import pandas as pd
import tkinter.font
import threading
from datetime import date, timedelta, datetime
import calendar
from tkinter import font as tkfont

from dal import reporting_dal
from dal import reporting_dal_new

class ReportingView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill="both", expand=True)

        # Data Persistence
        self.inventory_df = pd.DataFrame()
        self.reorder_df = pd.DataFrame()
        self.open_orders_df = pd.DataFrame()
        self.po_totals_df = pd.DataFrame()
        self.big_wire_df = pd.DataFrame()
        self.rental_df = pd.DataFrame()
        self.assembly_cost_df = pd.DataFrame()
        self.economic_nexus_raw_df = pd.DataFrame()
        self.economic_nexus_display_df = pd.DataFrame()
        self._search_job = None
        self._active_vendor_ids = [] # To track filtered list for Open PO sync

        # Main Tab Interface
        self.tabview = ctk.CTkTabview(self, width=1380, height=700)
        self.tabview.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.tabs = {
            "Inventory": self.tabview.add("Inventory"),
            "Re-Order": self.tabview.add("Re-Order"),
            "Open Orders": self.tabview.add("Open Orders"),
            "PO Totals": self.tabview.add("PO Totals"),
            "Big Wire": self.tabview.add("Big Wire"),
            "Rental": self.tabview.add("Rental"),
            "Assembly Cost": self.tabview.add("Assembly Cost"),
            "Economic Nexus": self.tabview.add("Economic Nexus")
        }
        
        # Global Styling
        self.tree_style = ttk.Style()
        self.tree_style.theme_use("clam")
        
        self.tree_style.configure("Treeview", 
            background="#2a2d2e", foreground="white", rowheight=28,
            fieldbackground="#343638", bordercolor="#343638", borderwidth=0)
        self.tree_style.map('Treeview', background=[('selected', '#22559b')])
        self.tree_style.configure("Treeview.Heading", 
            background="#565b5e", foreground="white", relief="flat")
        self.tree_style.map("Treeview.Heading", background=[('active', '#3484F0')])
        
        # Initialize Sub-Views
        self._setup_inventory()
        self._setup_reorder()
        self._setup_open_orders()
        self._setup_sales_summary() 
        self._setup_big_wire()
        self._setup_rental()
        self._setup_assembly_cost_tab()
        self._setup_economic_nexus_tab()

    # --- HELPERS FOR DYNAMIC LOGIC ---

    def _get_dynamic_month_ranges(self):
        """Calculates the date ranges for the last 6 months (rolling). Fixes 2026 breakage."""
        ranges = []
        today = date.today()
        for i in range(5, -1, -1):
            year = today.year
            month = today.month - i
            while month <= 0:
                month += 12
                year -= 1
            start_date = f"{year}-{month:02d}-01"
            last_day = calendar.monthrange(year, month)[1]
            end_date = f"{year}-{month:02d}-{last_day}"
            label = datetime(year, month, 1).strftime("%b '%y")
            ranges.append({"label": label, "start": start_date, "end": end_date})
        return ranges

    # --- PO TOTALS (DYNAMIC SALES SUMMARY) ---

    def _setup_sales_summary(self):
        t = self.tabs["PO Totals"]
        top_frame = ctk.CTkFrame(t)
        top_frame.pack(pady=(10,0), padx=10, fill="x")
        
        totals_frame = ctk.CTkFrame(top_frame)
        totals_frame.pack(side="right")
        
        # Open PO Total Label - Interactive for Auditing
        self.po_open_total_label = ctk.CTkLabel(
            totals_frame, 
            text="Open PO Value: $0.00", 
            font=("Arial", 12, "bold", "underline"), 
            text_color="#3484F0",
            cursor="hand2"
        )
        self.po_open_total_label.pack(anchor="e")
        self.po_open_total_label.bind("<Button-1>", lambda e: self._show_open_po_breakdown_window())
        
        self.po_ytd_total_label = ctk.CTkLabel(totals_frame, text="YTD: $0.00", font=("Arial", 12, "bold"))
        self.po_ytd_total_label.pack(anchor="e")
        self.po_prev_year_total_label = ctk.CTkLabel(totals_frame, text="Prev Year: $0.00", font=("Arial", 12, "bold"))
        self.po_prev_year_total_label.pack(anchor="e")
        self.po_2_years_ago_total_label = ctk.CTkLabel(totals_frame, text="2 Years Ago: $0.00", font=("Arial", 12, "bold"))
        self.po_2_years_ago_total_label.pack(anchor="e")
        
        self.po_totals_load_button = ctk.CTkButton(t, text="Load Data", command=self._load_sales_summary, font=("Arial", 12, "bold"))
        self.po_totals_load_button.pack(pady=5)
        
        self.loading_label_po_totals = ctk.CTkLabel(t, text="Loading...", font=("Arial", 12, "italic"), text_color="gray")
        
        self.tree_sales = ttk.Treeview(t, show='headings')
        self.tree_sales.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_sales.bind("<Double-1>", self._on_po_totals_double_click)
        
        search_frame = ctk.CTkFrame(t)
        search_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(search_frame, text="Search:", font=("Arial", 12)).pack(side="left", padx=5)
        self.po_totals_search_entry = ctk.CTkEntry(search_frame, placeholder_text="Type to search...", font=("Arial", 12))
        self.po_totals_search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.po_totals_search_entry.bind("<KeyRelease>", lambda e: self._debounce_filter(self.tree_sales, self.po_totals_df, self.po_totals_search_entry.get()))
        
        button_frame = ctk.CTkFrame(t)
        button_frame.pack(pady=5)
        ctk.CTkButton(button_frame, text="Filter Today", command=self._filter_today_sales, font=("Arial", 10, "bold")).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Show All", command=self._reset_po_totals_filter, font=("Arial", 10, "bold")).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Export CSV", command=lambda: self._export_to_csv(self.po_totals_df, "po_totals.csv"), font=("Arial", 10, "bold")).pack(side="left", padx=5)

    def _load_sales_summary(self):
        """Fetches table and then calculates Open PO Value based ONLY on displayed vendors."""
        self.po_totals_load_button.configure(state="disabled")
        self.loading_label_po_totals.pack(pady=5)
        
        configs = self._get_dynamic_month_ranges()
        sum_clauses = [f"FORMAT(SUM(IF(orders.order_date BETWEEN '{c['start']}' AND '{c['end']}', orders_detail.ext_price, 0)), 2) AS `{c['label']}`" for c in configs]
        
        summary_query = f"""
            SELECT 
                orders.cust_id, 
                vendors.vendor_name, 
                {", ".join(sum_clauses)},
                FORMAT(SUM(IF(orders.order_date = CURDATE(), orders_detail.ext_price, 0)), 2) AS TODAY,
                FORMAT(SUM(IF(orders.order_date BETWEEN CONCAT(YEAR(CURDATE()), '-01-01') AND CURDATE(), orders_detail.ext_price, 0)), 2) AS YTD,
                FORMAT(SUM(IF(orders.order_date BETWEEN CONCAT(YEAR(CURDATE())-1, '-01-01') AND CONCAT(YEAR(CURDATE())-1, '-12-31'), orders_detail.ext_price, 0)), 2) AS 'PrevYear',
                FORMAT(SUM(IF(orders.order_date BETWEEN CONCAT(YEAR(CURDATE())-2, '-01-01') AND CONCAT(YEAR(CURDATE())-2, '-12-31'), orders_detail.ext_price, 0)), 2) AS '2YearsAgo'
            FROM orders 
            JOIN orders_detail ON orders.order_num = orders_detail.order_num 
            JOIN vendors ON vendors.vendor_id = orders.cust_id 
            WHERE orders.order_num LIKE '4%' 
            AND orders_detail.q_p_s2 = 2 
            GROUP BY orders.cust_id, vendors.vendor_name 
            ORDER BY SUM(IF(orders.order_date BETWEEN CONCAT(YEAR(CURDATE()), '-01-01') AND CURDATE(), orders_detail.ext_price, 0)) DESC;
        """

        def task():
            df, error1 = reporting_dal._exec_query(summary_query)
            if error1:
                if self.winfo_exists():
                    self.after(0, lambda: messagebox.showerror("Error", error1))
                return

            # --- FILTERING LOGIC ---
            # 1. Remove Holloway
            holloway_ids = [7882, 1001, '7882', '1001']
            df = df[~df['cust_id'].isin(holloway_ids)].copy()

            # 2. Capture only vendors with purchase activity > 0
            configs = self._get_dynamic_month_ranges()
            val_cols = [c['label'] for c in configs] + ['TODAY', 'YTD', 'PrevYear', '2YearsAgo']

            def has_purchases(row):
                for col in val_cols:
                    if col in row:
                        val_str = str(row[col]).replace(',', '').strip()
                        try:
                            if float(val_str) > 0: return True
                        except: continue
                return False

            df = df[df.apply(has_purchases, axis=1)].reset_index(drop=True)
            self._active_vendor_ids = df['cust_id'].unique().tolist()
            
            # --- SECONDARY FETCH: CALCULATE OPEN PO FOR THESE VENDORS ONLY ---
            if not self._active_vendor_ids:
                open_val, error2 = 0, None
            else:
                id_list = ", ".join([str(i) for i in self._active_vendor_ids])
                open_po_query = f"""
                    SELECT SUM((line_qty - received_qty) * unit_price) as total_open_value
                    FROM (
                        SELECT 
                            MAX(od.qty) as line_qty,
                            SUM(pt.units_received) as received_qty,
                            MAX(od.unit_price) as unit_price
                        FROM product_trans pt
                        JOIN orders_detail od ON pt.order_num = od.order_num AND pt.assy_id = od.assy_id
                        JOIN orders o ON pt.order_num = o.order_num
                        WHERE pt.q_p_s = 2 AND od.q_p_s2 = 2
                        AND o.cust_id IN ({id_list})
                        GROUP BY pt.order_num, pt.assy_id
                        HAVING (MAX(od.qty) - SUM(pt.units_received)) > 0
                    ) as open_lines;
                """
                open_df, error2 = reporting_dal._exec_query(open_po_query)
                open_val = open_df.iloc[0]['total_open_value'] if not error2 and not open_df.empty else 0

            if self.winfo_exists():
                self.after(0, self._update_sales_summary_ui, df, None, open_val, error2)
        
        threading.Thread(target=task, daemon=True).start()

    def _update_sales_summary_ui(self, df, error1, open_po_total, error2):
        if not self.winfo_exists(): return
        self.loading_label_po_totals.pack_forget()
        self.po_totals_load_button.configure(state="normal")
        
        self.po_totals_df = df
        self._fill_tree(self.tree_sales, df)

        ytd_sum, prev_sum, ago_sum = 0, 0, 0
        if not df.empty:
            if 'YTD' in df.columns: ytd_sum = pd.to_numeric(df['YTD'].str.replace(',', ''), errors='coerce').sum()
            if 'PrevYear' in df.columns: prev_sum = pd.to_numeric(df['PrevYear'].str.replace(',', ''), errors='coerce').sum()
            if '2YearsAgo' in df.columns: ago_sum = pd.to_numeric(df['2YearsAgo'].str.replace(',', ''), errors='coerce').sum()

        self.po_open_total_label.configure(text=f"Open PO Value: ${open_po_total:,.2f}" if not error2 else "Error Fetching PO Value")
        self.po_ytd_total_label.configure(text=f"YTD: ${ytd_sum:,.2f}")
        self.po_prev_year_total_label.configure(text=f"Prev Year: ${prev_sum:,.2f}")
        self.po_2_years_ago_total_label.configure(text=f"2 Years Ago: ${ago_sum:,.2f}")

    def _on_po_totals_double_click(self, event):
        if not self.tree_sales.selection(): return
        item = self.tree_sales.item(self.tree_sales.focus())
        vals = item['values']
        if not vals: return
        try:
            today_idx = list(self.tree_sales["columns"]).index('TODAY')
            if pd.to_numeric(str(vals[today_idx]).replace(',', ''), errors='coerce') > 0:
                self._show_po_details_window(int(vals[0]), vals[1])
        except (ValueError, IndexError): pass

    def _filter_today_sales(self):
        if self.po_totals_df.empty: return
        df = self.po_totals_df.copy()
        df['TODAY_num'] = pd.to_numeric(df['TODAY'].astype(str).str.replace(',', ''), errors='coerce')
        filtered = df[df['TODAY_num'] > 0].sort_values(by='TODAY_num', ascending=False).drop(columns=['TODAY_num'])
        self._fill_tree(self.tree_sales, filtered)

    def _reset_po_totals_filter(self):
        if not self.po_totals_df.empty:
            self._fill_tree(self.tree_sales, self.po_totals_df)

    # --- INVENTORY SEARCH TAB ---

    def _setup_inventory(self):
        t = self.tabs["Inventory"]
        f = ctk.CTkFrame(t)
        f.pack(pady=10, padx=10, fill="x")
        f.grid_columnconfigure(7, weight=1)
        
        ctk.CTkLabel(f, text="Vendor:").grid(row=0, column=0, padx=(10,5), pady=10)
        self.inv_vendor_combo = ctk.CTkComboBox(f, width=200, command=self._on_inventory_vendor_select)
        self.inv_vendor_combo.grid(row=0, column=1, padx=(0,10))
        
        ctk.CTkLabel(f, text="Class:").grid(row=0, column=2, padx=(10,5), pady=10)
        self.inv_class_combo = ctk.CTkComboBox(f, width=150, state="readonly", command=self._on_inventory_class_select)
        self.inv_class_combo.grid(row=0, column=3, padx=(0,10))
        
        ctk.CTkLabel(f, text="Figure #:").grid(row=0, column=4, padx=(10,5), pady=10)
        self.inv_figure_combo = ctk.CTkComboBox(f, width=150, state="readonly")
        self.inv_figure_combo.grid(row=0, column=5, padx=(0,10))
        
        ctk.CTkLabel(f, text="Search:").grid(row=0, column=6, padx=(20,5), pady=10)
        self.inventory_search_entry = ctk.CTkEntry(f, placeholder_text="Search descriptions...")
        self.inventory_search_entry.grid(row=0, column=7, padx=(0,10), pady=10, sticky="ew")
        
        self.inv_go_button = ctk.CTkButton(f, text="Go", width=50, command=self._refresh_inventory_data)
        self.inv_go_button.grid(row=0, column=8, padx=10)
        
        self.inv_reset_button = ctk.CTkButton(f, text="Reset", command=self._reset_inventory_filters)
        self.inv_reset_button.grid(row=0, column=9, padx=(0,10))
        
        self.loading_label_inventory = ctk.CTkLabel(t, text="", font=("Arial", 12, "italic"), text_color="gray")
        self.loading_label_inventory.pack(pady=5)
        
        self.tree_inventory = ttk.Treeview(t, show='headings')
        self.tree_inventory.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_inventory.bind("<Double-1>", self._on_inventory_double_click)
        
        ctk.CTkButton(t, text="Export CSV", command=lambda: self._export_to_csv(self.inventory_df, "inventory.csv"), font=("Arial", 10, "bold")).pack(side="right", padx=20, pady=5)
        self._reset_inventory_filters()

    def _on_inventory_vendor_select(self, choice=None):
        classes, err = reporting_dal.get_hardware_product_classes(self.inv_vendor_combo.get())
        self.inv_class_combo.configure(values=classes)
        self.inv_class_combo.set("All")
        self._on_inventory_class_select()

    def _on_inventory_class_select(self, choice=None):
        figs, err = reporting_dal.get_hardware_figure_nums(self.inv_vendor_combo.get(), self.inv_class_combo.get())
        self.inv_figure_combo.configure(values=figs)
        self.inv_figure_combo.set("All")

    def _reset_inventory_filters(self):
        self.inventory_search_entry.delete(0, "end")
        vendors, err = reporting_dal.fetch_hardware_vendors()
        self.inv_vendor_combo.configure(values=vendors)
        self.inv_vendor_combo.set("All")
        self._on_inventory_vendor_select()
        self.tree_inventory.delete(*self.tree_inventory.get_children())
        self.inventory_df = pd.DataFrame()

    def _refresh_inventory_data(self):
        self.loading_label_inventory.configure(text="Searching...")
        self.inv_go_button.configure(state="disabled")
        v, c, f, s = self.inv_vendor_combo.get(), self.inv_class_combo.get(), self.inv_figure_combo.get(), self.inventory_search_entry.get()
        def task():
            df, error = reporting_dal.fetch_filtered_inventory_data(v, c, f, s)
            if self.winfo_exists():
                self.after(0, self._update_inventory_ui, df, error)
        threading.Thread(target=task, daemon=True).start()

    def _update_inventory_ui(self, df, error):
        if not self.winfo_exists(): return
        self.loading_label_inventory.configure(text="")
        self.inv_go_button.configure(state="normal")
        self.tree_inventory.delete(*self.tree_inventory.get_children())
        if error:
            messagebox.showerror("Error", error)
            return
        self.inventory_df = df
        
        # Determine cols to show
        cols = [c for c in df.columns if c not in ['kdc_id', 'vendor_id']]
        self.tree_inventory['columns'] = cols
        for col in cols:
            p = {"text": col, "width": 100, "anchor": "w"}
            if "description" in col.lower(): p["width"] = 350
            elif "vendor" in col.lower(): p["width"] = 150
            elif any(k in col.lower() for k in ['price', 'cost']): p["anchor"] = 'e' # Right alignment for accounting
            elif len(col) < 8 or any(k in col.lower() for k in ['avail', 'hand', 'order', 'avg', 'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'commit']):
                p["anchor"] = 'center'
                p["width"] = 60 if len(col) < 5 else 85
            self.tree_inventory.heading(col, text=p["text"])
            self.tree_inventory.column(col, width=p["width"], anchor=p["anchor"])
            
        self._fill_tree(self.tree_inventory, df[cols])

    def _on_inventory_double_click(self, event):
        sid = self.tree_inventory.focus()
        if not sid: return
        # Find row by iid (kdc_id)
        try:
            row = self.inventory_df[self.inventory_df['kdc_id'] == int(sid)].iloc[0]
            self._show_inventory_details_window(int(sid), row['stock_id'], row['description1'])
        except Exception: pass

    # --- RE-ORDER TAB ---

    def _setup_reorder(self):
        t = self.tabs["Re-Order"]
        self.reorder_load_button = ctk.CTkButton(t, text="Check Re-Orders", command=self._load_reorder, font=("Arial", 12, "bold"))
        self.reorder_load_button.pack(pady=10)
        self.loading_label_reorder = ctk.CTkLabel(t, text="Loading...", font=("Arial", 12, "italic"), text_color="gray")
        self.tree_reorder = ttk.Treeview(t, show='headings')
        self.tree_reorder.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_reorder.bind("<Double-1>", self._on_reorder_double_click)
        
        sf = ctk.CTkFrame(t)
        sf.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(sf, text="Search:").pack(side="left", padx=5)
        self.reorder_search_entry = ctk.CTkEntry(sf, placeholder_text="Type to search...")
        self.reorder_search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.reorder_search_entry.bind("<KeyRelease>", lambda e: self._debounce_filter(self.tree_reorder, self.reorder_df, self.reorder_search_entry.get()))
        ctk.CTkButton(t, text="Export CSV", command=lambda: self._export_to_csv(self.reorder_df, "reorder.csv"), font=("Arial", 10, "bold")).pack(pady=5)

    def _load_reorder(self):
        self._load_data_threaded(reporting_dal.fetch_reorder_data, self._update_reorder_ui, self.reorder_load_button, self.loading_label_reorder)

    def _update_reorder_ui(self, df, error, button, label):
        if not self.winfo_exists(): return
        label.pack_forget()
        button.configure(state="normal")
        if error: messagebox.showerror("Error", error)
        self.reorder_df = df
        display_df = df.drop(columns=['kdc_id', 'vendor_id'], errors='ignore') if not df.empty else df
        self._fill_tree(self.tree_reorder, display_df)

    def _on_reorder_double_click(self, event):
        """Opens history details when a reorder item is double-clicked."""
        if not self.tree_reorder.selection(): return
        item_iid = self.tree_reorder.focus()
        idx = self.tree_reorder.index(item_iid)
        row = self.reorder_df.iloc[idx]
        self._show_inventory_details_window(int(row['kdc_id']), row['stock_id'], row['description1'])

    # --- RENTAL TAB ---

    def _setup_rental(self):
        t = self.tabs["Rental"]
        cf = ctk.CTkFrame(t)
        cf.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(cf, text="Start Date (YYYY-MM-DD):").pack(side="left", padx=5)
        self.rental_start_date_entry = ctk.CTkEntry(cf)
        self.rental_start_date_entry.pack(side="left", padx=5)
        self.rental_start_date_entry.insert(0, (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
        
        ctk.CTkLabel(cf, text="End Date:").pack(side="left", padx=5)
        self.rental_end_date_entry = ctk.CTkEntry(cf)
        self.rental_end_date_entry.pack(side="left", padx=5)
        self.rental_end_date_entry.insert(0, date.today().strftime('%Y-%m-%d'))
        
        self.rental_load_button = ctk.CTkButton(cf, text="Fetch Rental Data", command=self._load_rental)
        self.rental_load_button.pack(side="left", padx=10)

        ctk.CTkButton(cf, text="Export CSV", command=lambda: self._export_to_csv(self.rental_df, "rental.csv"), font=("Arial", 10, "bold")).pack(side="left", padx=5)

        self.rental_total_label = ctk.CTkLabel(cf, text="Total: $0.00", font=("Arial", 14, "bold"))
        self.rental_total_label.pack(side="right", padx=10)
        
        self.loading_label_rental = ctk.CTkLabel(t, text="Loading...", font=("Arial", 12, "italic"), text_color="gray")
        self.tree_rental = ttk.Treeview(t, show='headings')
        self.tree_rental.pack(fill="both", expand=True, padx=10, pady=10)

    def _load_rental(self):
        s, e = self.rental_start_date_entry.get(), self.rental_end_date_entry.get()
        params = {'start_date': s, 'end_date': e}
        self._load_data_threaded(reporting_dal.fetch_rental_data, self._update_rental_ui, self.rental_load_button, self.loading_label_rental, params)

    def _update_rental_ui(self, df, error, button, label):
        if not self.winfo_exists(): return
        label.pack_forget()
        button.configure(state="normal")
        if error: messagebox.showerror("Error", error)
        self.rental_df = df
        self._fill_tree(self.tree_rental, df)
        total = pd.to_numeric(df['ext_price'], errors='coerce').sum() if not df.empty and 'ext_price' in df.columns else 0
        self.rental_total_label.configure(text=f"Total: ${total:,.2f}")

    # --- BIG WIRE ANALYSIS TAB ---

    def _setup_big_wire(self):
        t = self.tabs["Big Wire"]
        self.big_wire_load_button = ctk.CTkButton(t, text="Generate Analysis", command=self._load_big_wire, font=("Arial", 12, "bold"))
        self.big_wire_load_button.pack(pady=10)
        self.loading_label_big_wire = ctk.CTkLabel(t, text="Loading...", font=("Arial", 12, "italic"), text_color="gray")
        self.tree_big_wire = ttk.Treeview(t, show='headings')
        self.tree_big_wire.pack(fill="both", expand=True, padx=10, pady=10)
        
        sf = ctk.CTkFrame(t)
        sf.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(sf, text="Search:").pack(side="left", padx=5)
        self.big_wire_search_entry = ctk.CTkEntry(sf, placeholder_text="Type to search...")
        self.big_wire_search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.big_wire_search_entry.bind("<KeyRelease>", lambda e: self._debounce_filter(self.tree_big_wire, self.big_wire_df, self.big_wire_search_entry.get()))
        ctk.CTkButton(t, text="Export CSV", command=lambda: self._export_to_csv(self.big_wire_df, "big_wire.csv"), font=("Arial", 10, "bold")).pack(pady=5)

    def _load_big_wire(self):
        self._load_data_threaded(reporting_dal.fetch_product_analysis_data, self._update_big_wire_ui, self.big_wire_load_button, self.loading_label_big_wire)

    def _update_big_wire_ui(self, df, error, button, label):
        if not self.winfo_exists(): return
        label.pack_forget()
        button.configure(state="normal")
        if error: messagebox.showerror("Error", error)
        self.big_wire_df = df
        self._fill_tree(self.tree_big_wire, df)

    # --- OPEN ORDERS TAB ---

    def _setup_open_orders(self):
        t = self.tabs["Open Orders"]
        self.open_orders_load_button = ctk.CTkButton(t, text="Fetch Open Customer Orders", command=self._load_open_orders, font=("Arial", 12, "bold"))
        self.open_orders_load_button.pack(pady=10)
        self.loading_label_open_orders = ctk.CTkLabel(t, text="Loading...", font=("Arial", 12, "italic"), text_color="gray")
        self.tree_open = ttk.Treeview(t, show='headings')
        self.tree_open.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_open.bind("<Double-1>", self._on_open_orders_double_click)
        
        ctk.CTkButton(t, text="Export CSV", command=lambda: self._export_to_csv(self.open_orders_df, "open_orders.csv"), font=("Arial", 10, "bold")).pack(pady=5)

    def _load_open_orders(self):
        self._load_data_threaded(reporting_dal.fetch_open_orders_data, self._update_open_orders_ui, self.open_orders_load_button, self.loading_label_open_orders)

    def _update_open_orders_ui(self, df, error, button, label):
        if not self.winfo_exists(): return
        label.pack_forget()
        button.configure(state="normal")
        if error: messagebox.showerror("Error", error)
        self.open_orders_df = df
        self._fill_tree(self.tree_open, df)

    def _on_open_orders_double_click(self, event):
        if not self.tree_open.selection(): return
        vals = self.tree_open.item(self.tree_open.focus())['values']
        if vals: self._show_customer_orders_window(vals[0])

    # --- ASSEMBLY COST TAB ---

    def _setup_assembly_cost_tab(self):
        tab = self.tabs["Assembly Cost"]
        cf = ctk.CTkFrame(tab)
        cf.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(cf, text="Sales Order #:").pack(side="left", padx=(10, 5))
        self.ac_order_num_entry = ctk.CTkEntry(cf, placeholder_text="Enter Order #")
        self.ac_order_num_entry.pack(side="left", padx=5)
        self.ac_generate_button = ctk.CTkButton(cf, text="Generate Cost Report", command=self._generate_assembly_cost_report)
        self.ac_generate_button.pack(side="left", padx=20)
        self.ac_loading_label = ctk.CTkLabel(tab, text="Loading...", font=("Arial", 12, "italic"), text_color="gray")
        
        self.ac_tree = ttk.Treeview(tab, show='headings')
        self.ac_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        bf = ctk.CTkFrame(tab)
        bf.pack(fill="x", padx=10, pady=5)
        self.ac_search_entry = ctk.CTkEntry(bf, placeholder_text="Search visible components...")
        self.ac_search_entry.pack(side="left", fill="x", expand=True, padx=10)
        self.ac_search_entry.bind("<KeyRelease>", lambda e: self._debounce_filter(self.ac_tree, self.assembly_cost_df, e.widget.get()))
        ctk.CTkButton(bf, text="Export CSV", command=lambda: self._export_to_csv(self.assembly_cost_df, "assy_cost.csv")).pack(side="right", padx=10)

    def _generate_assembly_cost_report(self):
        order_num = self.ac_order_num_entry.get()
        if not order_num:
            messagebox.showerror("Input Error", "Please provide a Sales Order Number.")
            return
        self.ac_generate_button.configure(text="Processing...", state="disabled")
        self.ac_loading_label.pack(pady=5)
        def task():
            df, error = reporting_dal.generate_assembly_cost_report(order_num)
            if self.winfo_exists():
                self.after(0, self._update_assembly_cost_ui, df, error)
        threading.Thread(target=task, daemon=True).start()

    def _update_assembly_cost_ui(self, df, error):
        """RESTORED: Full detailed logic with margin color-coding and subtotals."""
        if not self.winfo_exists(): return
        self.ac_loading_label.pack_forget()
        self.ac_generate_button.configure(text="Generate Cost Report", state="normal")
        for i in self.ac_tree.get_children(): self.ac_tree.delete(i)
        if error: messagebox.showerror("Error", error); return
        if df.empty: messagebox.showinfo("Info", "No costed components found."); return
        
        self.assembly_cost_df = df.copy()
        try:
            df['Unit Cost'] = pd.to_numeric(df['Unit Cost'], errors='coerce').fillna(0)
            df['Extended Cost'] = pd.to_numeric(df['Extended Cost'], errors='coerce').fillna(0)
            df['Assy Sales Price'] = pd.to_numeric(df['Assy Sales Price'], errors='coerce').fillna(0)
            
            bold_font = tkfont.Font(font=self.tree_style.lookup("Treeview", "font"))
            bold_font.configure(weight="bold")
            
            self.ac_tree.tag_configure('subtotal_cost', font=bold_font)
            self.ac_tree.tag_configure('grandtotal', font=bold_font, background='#34495e')
            self.ac_tree.tag_configure('spacer', background='#212324')
            self.ac_tree.tag_configure('oddrow', background='#343638')
            self.ac_tree.tag_configure('evenrow', background='#2a2d2e')
            self.ac_tree.tag_configure('margin_low', font=bold_font, foreground='#e74c3c')
            self.ac_tree.tag_configure('margin_med', font=bold_font, foreground='#f39c12')
            self.ac_tree.tag_configure('margin_high', font=bold_font, foreground='#2ecc71')
            
            cols = [c for c in df.columns if c != 'Assy Sales Price']
            self.ac_tree["columns"] = cols
            for col in cols:
                anchor = "e" if any(k in col.lower() for k in ["cost", "qty", "price", "amount"]) else "w" if any(k in col for k in ["Description", "Part", "Vendor"]) else "center"
                width = 300 if "Description" in col else 150 if any(k in col for k in ["Part", "Vendor"]) else 100
                self.ac_tree.heading(col, text=col, anchor=anchor)
                self.ac_tree.column(col, anchor=anchor, width=width)
            
            grouped = df.groupby('Assy ID')
            gt_cost, gt_sales, row_idx = 0, 0, 0
            
            for assy_id, group in grouped:
                for _, row in group.iterrows():
                    vals = [row[c] for c in cols]
                    vals[cols.index('Unit Cost')] = f"${row['Unit Cost']:,.2f}"
                    vals[cols.index('Extended Cost')] = f"${row['Extended Cost']:,.2f}"
                    self.ac_tree.insert("", "end", values=vals, tags=('evenrow' if row_idx % 2 == 0 else 'oddrow',))
                    row_idx += 1

                sub_c = group['Extended Cost'].sum()
                gt_cost += sub_c
                c_vals = [''] * len(cols)
                c_vals[cols.index('Unit Cost')] = 'Subtotal Cost:'
                c_vals[cols.index('Extended Cost')] = f"${sub_c:,.2f}"
                self.ac_tree.insert("", "end", values=c_vals, tags=('subtotal_cost',))

                s_price = group['Assy Sales Price'].iloc[0] if not group.empty else 0
                gt_sales += s_price
                margin = ((s_price - sub_c) / s_price * 100) if s_price > 0 else 0
                
                m_tag = 'margin_low' if margin <= 10 else 'margin_med' if margin <= 19 else 'margin_high'
                p_vals = [''] * len(cols)
                p_vals[cols.index('Component Description')] = f"Margin: {margin:.2f}%"
                p_vals[cols.index('Unit Cost')] = "Sales Price:"
                p_vals[cols.index('Extended Cost')] = f"${s_price:,.2f}"
                self.ac_tree.insert("", "end", values=p_vals, tags=(m_tag,))
                self.ac_tree.insert("", "end", values=[''] * len(cols), tags=('spacer',))
            
            # Grand Totals
            gt_c_vals = [''] * len(cols)
            gt_c_vals[cols.index('Unit Cost')] = 'Grand Total Cost:'
            gt_c_vals[cols.index('Extended Cost')] = f"${gt_cost:,.2f}"
            self.ac_tree.insert("", "end", values=gt_c_vals, tags=('grandtotal',))

            o_margin = ((gt_sales - gt_cost) / gt_sales * 100) if gt_sales > 0 else 0
            o_m_tag = 'margin_low' if o_margin <= 10 else 'margin_med' if o_margin <= 19 else 'margin_high'
            gt_s_vals = [''] * len(cols)
            gt_s_vals[cols.index('Component Description')] = f"Overall Margin: {o_margin:.2f}%"
            gt_s_vals[cols.index('Unit Cost')] = 'Grand Total Sales:'
            gt_s_vals[cols.index('Extended Cost')] = f"${gt_sales:,.2f}"
            self.ac_tree.insert("", "end", values=gt_s_vals, tags=(o_m_tag, 'grandtotal'))

        except Exception as e: messagebox.showerror("Error", f"Formatting Exception: {e}")

    # --- ECONOMIC NEXUS TAB ---

    def _setup_economic_nexus_tab(self):
        tab = self.tabs["Economic Nexus"]
        cf = ctk.CTkFrame(tab)
        cf.pack(pady=10, padx=10, fill="x")
        
        today = date.today()
        first = today.replace(day=1)
        
        ctk.CTkLabel(cf, text="Start Date (YYYY-MM-DD):").pack(side="left", padx=5)
        self.en_start_date_entry = ctk.CTkEntry(cf)
        self.en_start_date_entry.pack(side="left", padx=5)
        self.en_start_date_entry.insert(0, first.strftime("%Y-%m-%d"))
        
        ctk.CTkLabel(cf, text="End Date:").pack(side="left", padx=5)
        self.en_end_date_entry = ctk.CTkEntry(cf)
        self.en_end_date_entry.pack(side="left", padx=5)
        self.en_end_date_entry.insert(0, today.strftime("%Y-%m-%d"))
        
        self.en_fetch_button = ctk.CTkButton(cf, text="Run Report", command=self._fetch_economic_nexus_data)
        self.en_fetch_button.pack(side="left", padx=10)
        
        vf = ctk.CTkFrame(tab, fg_color="transparent")
        vf.pack(pady=5, padx=10, fill="x")
        self.en_detailed_button = ctk.CTkButton(vf, text="Full List", state="disabled", command=self._display_nexus_detailed)
        self.en_detailed_button.pack(side="left", padx=5)
        self.en_invoice_button = ctk.CTkButton(vf, text="By Invoice", state="disabled", command=self._display_nexus_by_invoice)
        self.en_invoice_button.pack(side="left", padx=5)
        self.en_state_button = ctk.CTkButton(vf, text="By State", state="disabled", command=self._display_nexus_by_state)
        self.en_state_button.pack(side="left", padx=5)
        
        self.en_loading_label = ctk.CTkLabel(tab, text="Loading...", font=("Arial", 12, "italic"), text_color="gray")
        self.en_tree = ttk.Treeview(tab, show='headings')
        self.en_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkButton(tab, text="Export CSV", command=lambda: self._export_to_csv(self.economic_nexus_display_df, "nexus.csv")).pack(pady=5)

    def _fetch_economic_nexus_data(self):
        start, end = self.en_start_date_entry.get(), self.en_end_date_entry.get()
        if not (start and end): return
        self.en_fetch_button.configure(text="Processing...", state="disabled")
        self.en_loading_label.pack(pady=5)
        def task():
            df, error = reporting_dal.generate_economic_nexus_report(start, end)
            if self.winfo_exists():
                self.after(0, self._update_economic_nexus_ui, df, error)
        threading.Thread(target=task, daemon=True).start()

    def _update_economic_nexus_ui(self, df, error):
        if not self.winfo_exists(): return
        self.en_loading_label.pack_forget()
        self.en_fetch_button.configure(text="Run Report", state="normal")
        if error: messagebox.showerror("Error", error); return
        self.economic_nexus_raw_df = df
        self.en_detailed_button.configure(state="normal")
        self.en_invoice_button.configure(state="normal")
        self.en_state_button.configure(state="normal")
        self._display_nexus_detailed()

    def _display_nexus_detailed(self):
        self.economic_nexus_display_df = self.economic_nexus_raw_df
        self._fill_tree(self.en_tree, self.economic_nexus_display_df)

    def _display_nexus_by_invoice(self):
        df = self.economic_nexus_raw_df
        if df.empty: return
        self.economic_nexus_display_df = df.groupby(['State', 'Customer', 'Invoice Number']).agg(Total_Amount=('Amount', 'sum')).reset_index()
        self._fill_tree(self.en_tree, self.economic_nexus_display_df)

    def _display_nexus_by_state(self):
        df = self.economic_nexus_raw_df
        if df.empty: return
        self.economic_nexus_display_df = df.groupby(['State']).agg(Total_Amount=('Amount', 'sum')).reset_index()
        self._fill_tree(self.en_tree, self.economic_nexus_display_df)

    # --- SHARED UI HANDLERS ---

    def _load_data_threaded(self, query_func, ui_update_func, load_button, loading_label, params=None):
        load_button.configure(state="disabled")
        loading_label.pack(pady=5)
        def task():
            df, error = query_func(**params) if params else query_func()
            if self.winfo_exists():
                self.after(0, ui_update_func, df, error, load_button, loading_label)
        threading.Thread(target=task, daemon=True).start()

    def _fill_tree(self, tree, df):
        if not self.winfo_exists(): return
        tree.delete(*tree.get_children())
        if df is None or df.empty: return
        
        tree.tag_configure('oddrow', background='#343638')
        tree.tag_configure('evenrow', background='#2a2d2e')
        tree.tag_configure('negative_avail', foreground='#F45050')
        tree.tag_configure('total_row', font=('Arial', 12, 'bold'))

        tree["columns"] = list(df.columns)
        font = tkfont.Font(font=self.tree_style.lookup("Treeview", "font"))
        
        for col in df.columns:
            tree.heading(col, text=col)
            # Professional accounting alignment
            anchor = "w" if any(k in col.lower() for k in ['id', 'name', 'desc', 'figure', 'customer', 'item', 'comment', 'state']) else "e" if any(k in col.lower() for k in ['total', 'price', 'cost', 'amount', 'ytd', 'prev', 'ago']) or "'" in col or any(k in col.lower() for k in ['avail', 'hand', 'order', 'qty']) else "center"
            width = 250 if any(k in col for k in ['Description', 'Comment', 'Customer', 'Ship To']) else max(font.measure(col) + 20, 80)
            tree.column(col, anchor=anchor, width=width)
            
        for i, row in df.iterrows():
            tags = ['evenrow' if i % 2 == 0 else 'oddrow']
            
            if 'Avail' in df.columns and pd.to_numeric(row.get('Avail'), errors='coerce') < 0:
                tags.append('negative_avail')
                
            if 'ORDER TOTAL:' in str(row.values):
                tags.append('total_row')

            f_vals = []
            for idx, v in enumerate(list(row.fillna('').values)):
                col_name = df.columns[idx].lower()
                # If it's a numeric ID, Year, or Number column, show as integer string (no decimals)
                if isinstance(v, (int, float)) and any(x in col_name for x in ['id', 'year', 'num']):
                    f_vals.append(str(int(v)))
                # If it's any other number, format with commas and 2 decimals (Accounting style)
                elif isinstance(v, (int, float)):
                    f_vals.append(f"{v:,.2f}")
                else:
                    f_vals.append(v)
            
            tree.insert("", "end", values=f_vals, tags=tuple(tags))

    def _export_to_csv(self, df, default_filename="export.csv"):
        if df.empty: messagebox.showwarning("Warning", "No data to export."); return
        fp = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile=default_filename)
        if fp: df.to_csv(fp, index=False)

    def _debounce_filter(self, tree, original_df, term):
        if self._search_job: 
            try:
                self.after_cancel(self._search_job)
            except:
                pass
        if self.winfo_exists():
            self._search_job = self.after(300, lambda: self._filter_tree(tree, original_df, term))

    def _filter_tree(self, tree, original_df, term):
        if not term: filtered_df = original_df
        else:
            low_term = term.lower()
            filtered_df = original_df[original_df.astype(str).apply(lambda row: row.str.lower().str.contains(low_term, na=False).any(), axis=1)]
        if self.winfo_exists():
            self._fill_tree(tree, filtered_df)

    # --- AUDIT WINDOWS (BREAKDOWN VIEWS) ---

    def _show_open_po_breakdown_window(self):
        """Opens breakdown window filtered specifically by the displayed vendor list."""
        if not self._active_vendor_ids:
            messagebox.showinfo("Audit", "No active vendors currently loaded.")
            return

        w = ctk.CTkToplevel(self)
        w.title("Open Purchase Order Audit")
        w.geometry("1100x650")
        w.grab_set()

        ctk.CTkLabel(w, text="Audit Breakdown: Every Open PO Line Item (Active Vendors)", font=("Arial", 18, "bold")).pack(pady=10)
        
        id_list = ", ".join([str(i) for i in self._active_vendor_ids])
        query = f"""
            SELECT 
                pt.order_num AS 'Order #',
                MAX(v.vendor_name) AS 'Vendor',
                MAX(p.stock_id) AS 'Stock ID',
                MAX(od.qty) AS 'Qty Ordered',
                SUM(pt.units_received) AS 'Qty Received',
                MAX(od.qty) - SUM(pt.units_received) AS 'Qty Open',
                MAX(od.unit_price) AS 'Unit Price',
                (MAX(od.qty) - SUM(pt.units_received)) * MAX(od.unit_price) AS 'Extended Value'
            FROM product_trans pt
            JOIN orders_detail od ON pt.order_num = od.order_num AND pt.assy_id = od.assy_id
            JOIN products p ON od.kdc_id = p.kdc_id
            JOIN orders o ON pt.order_num = o.order_num
            LEFT JOIN vendors v ON p.vendor_id = v.vendor_id
            WHERE pt.q_p_s = 2 AND od.q_p_s2 = 2
            AND o.cust_id IN ({id_list})
            GROUP BY pt.order_num, pt.assy_id
            HAVING (MAX(od.qty) - SUM(pt.units_received)) > 0
            ORDER BY `Extended Value` DESC;
        """

        dt = ttk.Treeview(w, show='headings')
        dt.pack(fill="both", expand=True, padx=20, pady=10)
        
        loading = ctk.CTkLabel(w, text="Fetching audit data...")
        loading.pack()

        def task():
            df, error = reporting_dal._exec_query(query)
            if self.winfo_exists():
                loading.pack_forget()
                if error: 
                    messagebox.showerror("Audit Error", error, parent=w)
                else:
                    self._fill_tree(dt, df)
                    w.current_df = df

        threading.Thread(target=task, daemon=True).start()

        bf = ctk.CTkFrame(w); bf.pack(fill="x", padx=20, pady=10)
        se = ctk.CTkEntry(bf, placeholder_text="Search orders/vendors..."); se.pack(side="left", fill="x", expand=True, padx=5)
        se.bind("<KeyRelease>", lambda e: self._debounce_filter(dt, getattr(w, 'current_df', pd.DataFrame()), se.get()))
        ctk.CTkButton(bf, text="Export CSV", command=lambda: self._export_to_csv(getattr(w, 'current_df', pd.DataFrame()), "open_po_audit.csv")).pack(side="right", padx=5)

    def _show_inventory_details_window(self, kdc_id, stock_id, description):
        """Restored: History window with Search and Export features."""
        w = ctk.CTkToplevel(self); w.title(f"History: {description}"); w.geometry("1100x650"); w.grab_set()
        tf = ctk.CTkFrame(w); tf.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(tf, text=f"History for: {description}", font=("Arial", 16, "bold")).pack(side="left")
        
        dt = ttk.Treeview(w, show='headings'); dt.pack(fill="both", expand=True, padx=10, pady=5)
        dt.tag_configure('oddrow', background='#343638'); dt.tag_configure('evenrow', background='#2a2d2e')
        cols = {'Date': 120, 'Order #': 120, 'Ordered': 100, 'Received': 100, 'Sold': 100, 'Shipped': 100, 'User': 150}
        dt['columns'] = list(cols.keys())
        for c, wd in cols.items():
            dt.heading(c, text=c)
            # Right-align quantities for accounting style
            anchor = "e" if wd == 100 else "w"
            dt.column(c, width=wd, anchor=anchor)
            
        t_map = {"All Time": None, "2 Year": 2, "4 Year": 4, "7 Year": 7}
        tt_filt, tf_filt = ctk.StringVar(value="Sales"), ctk.StringVar(value="2 Year")
        
        def r_data(*args):
            df, error = reporting_dal.fetch_inventory_details(kdc_id, trans_type=tt_filt.get(), timeframe_years=t_map[tf_filt.get()])
            if not w.winfo_exists(): return
            if error:
                messagebox.showerror("Error", error, parent=w)
                return
            w.current_df = df 
            dt.delete(*dt.get_children())
            for i, row in df.iterrows():
                v = (row['Transaction Date'].strftime('%Y-%m-%d'), row['Order #'], int(row.get('Ordered', 0)), int(row.get('Received', 0)), int(row.get('Sold', 0)), int(row.get('Shipped', 0)), row['User'])
                dt.insert("", "end", values=v, tags=('evenrow' if i % 2 == 0 else 'oddrow',))
        
        ctk.CTkComboBox(tf, values=list(t_map.keys()), variable=tf_filt, command=r_data, state="readonly").pack(side="right", padx=5)
        ctk.CTkComboBox(tf, values=["All", "Sales", "Rentals"], variable=tt_filt, command=r_data, state="readonly").pack(side="right", padx=5)
        
        # Search & Export Bar
        bf = ctk.CTkFrame(w); bf.pack(fill="x", padx=10, pady=5)
        se = ctk.CTkEntry(bf, placeholder_text="Filter transactions..."); se.pack(side="left", fill="x", expand=True, padx=5)
        se.bind("<KeyRelease>", lambda e: self._debounce_filter(dt, getattr(w, 'current_df', pd.DataFrame()), se.get()))
        ctk.CTkButton(bf, text="Export CSV", command=lambda: self._export_to_csv(getattr(w, 'current_df', pd.DataFrame()), f"{stock_id}_history.csv")).pack(side="right", padx=5)
        
        dt.bind("<Double-1>", lambda event, tree=dt: self._on_inventory_detail_double_click(event, tree))
        r_data()

    def _show_customer_orders_window(self, name):
        """Restored: Customer orders window with dataframe processing, search, and export."""
        w = ctk.CTkToplevel(self); w.title(f"Orders: {name}"); w.geometry("1100x650"); w.grab_set()
        ctk.CTkLabel(w, text=f"Open Orders for: {name}", font=("Arial", 16, "bold")).pack(pady=10)
        
        df, error = reporting_dal.fetch_customer_orders_data(name)
        if not w.winfo_exists(): return
        if error: messagebox.showerror("Error", error); return
        
        processed_df = pd.DataFrame()
        if not df.empty:
            df['Item Description'] = df['Item Description'].astype(str).apply(lambda x: (x[:45] + '...') if len(x) > 45 else x)
            df['Extended Price'] = pd.to_numeric(df['Extended Price'], errors='coerce').fillna(0)
            df['Unit Price'] = pd.to_numeric(df['Unit Price'], errors='coerce').fillna(0)
            processed_df = df 

        t = ttk.Treeview(w, show='headings'); t.pack(fill="both", expand=True, padx=10, pady=5)
        t.bind("<ButtonRelease-1>", lambda event, tree=t: self._on_detail_tree_click(event, tree))
        
        self._fill_tree(t, processed_df)
        w.current_df = processed_df

        bf = ctk.CTkFrame(w); bf.pack(fill="x", padx=10, pady=5)
        se = ctk.CTkEntry(bf, placeholder_text="Filter items..."); se.pack(side="left", fill="x", expand=True, padx=5)
        se.bind("<KeyRelease>", lambda e: self._debounce_filter(t, w.current_df, se.get()))
        ctk.CTkButton(bf, text="Export CSV", command=lambda: self._export_to_csv(w.current_df, f"{name}_orders.csv")).pack(side="right", padx=5)

    def _show_po_details_window(self, cid, vname):
        w = ctk.CTkToplevel(self); w.title(f"Today PO: {vname}"); w.geometry("800x500"); w.grab_set()
        ctk.CTkLabel(w, text=f"Today's Breakdown for {vname}", font=("Arial", 16, "bold")).pack(pady=10)
        df, error = reporting_dal.fetch_po_details_data(cid, date.today().strftime('%Y-%m-%d'))
        if not w.winfo_exists(): return
        if error: messagebox.showerror("Error", error); return
        t = ttk.Treeview(w, show='headings'); t.pack(fill="both", expand=True, padx=10, pady=10)
        self._fill_tree(t, df)

    def _show_full_order_details_window(self, onum):
        w = ctk.CTkToplevel(self); w.title(f"Order #{onum}"); w.geometry("1000x600"); w.grab_set()
        df, error = reporting_dal.fetch_full_order_details(onum)
        if not w.winfo_exists(): return
        if error: messagebox.showerror("Error", error); return
        t = ttk.Treeview(w, show='headings'); t.pack(fill="both", expand=True, padx=10, pady=10)
        self._fill_tree(t, df)

    def _on_detail_tree_click(self, event, tree):
        sel = tree.selection()
        if not sel: return
        vals = tree.item(sel[0])['values']
        try:
            o_idx = tree["columns"].index('Order #')
            onum = vals[o_idx]
            for cid in tree.get_children():
                tree.selection_add(cid) if tree.item(cid)['values'][o_idx] == onum else tree.selection_remove(cid)
        except ValueError: pass

    def _on_inventory_detail_double_click(self, event, tree):
        item = tree.item(tree.focus())
        if item and 'values' in item:
            try:
                onum = item['values'][tree["columns"].index('Order #')]
                if onum: self._show_full_order_details_window(onum)
            except (ValueError, IndexError): pass