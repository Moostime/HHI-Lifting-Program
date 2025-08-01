import customtkinter as ctk
from views.sales_order_view import SalesOrderWindow
from views.po_view import PurchaseOrderWindow
from views.receiving_view import ReceivingWindow
from views.shipping_view import ShippingWindow
from views.product_view import ProductManagementWindow
from views.reporting_view import ReportWindow
from views.job_status_view import JobStatusWindow
from views.order_search_view import OrderSearchWindow
from views.sling_builder_frame import SlingBuilderFrame

class App(ctk.CTk):
    def __init__(self, user_data):
        super().__init__()
        self.title("HHI Lifting - Sling Configurator & Quoting ERP")
        self.geometry("1400x800")
        
        self.current_user = user_data
        self.permissions = set(self.current_user.get('access_level', '').split(','))
        
        # --- Main Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        user_name = f"{self.current_user.get('FirstName', '')} {self.current_user.get('LastName', '')}"
        self.welcome_label = ctk.CTkLabel(self, text=f"Welcome, {user_name}!", font=ctk.CTkFont(size=14))
        self.welcome_label.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="w")
        
        # --- Tabbed Interface ---
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        self.tab_view.add("Sling Builder")
        self.tab_view.add("Component Sales")
        self.tab_view.add("Order Management")

        # Configure tab content
        self.configure_sling_builder_tab()
        self.configure_component_sales_tab()
        self.configure_order_management_tab()
        
    def configure_sling_builder_tab(self):
        """Creates the widgets for the Sling Builder tab."""
        tab = self.tab_view.tab("Sling Builder")
        self.sling_builder = SlingBuilderFrame(master=tab)
        self.sling_builder.pack(fill="both", expand=True)

    def configure_component_sales_tab(self):
        """Creates the widgets for the Component Sales tab."""
        tab = self.tab_view.tab("Component Sales")
        label = ctk.CTkLabel(tab, text="Component Sales & Quoting UI will go here.")
        label.pack(padx=20, pady=20)

    def configure_order_management_tab(self):
        """Creates widgets for the existing modules like SO, PO, etc."""
        tab = self.tab_view.tab("Order Management")
        
        button_frame = ctk.CTkFrame(tab)
        button_frame.pack(padx=20, pady=20)
        
        if '11' in self.permissions:
            self.open_job_status_button = ctk.CTkButton(button_frame, text="Job Status", command=self.open_job_status_window)
            self.open_job_status_button.pack(pady=10, padx=20, fill="x")
        if '12' in self.permissions:
            self.open_reports_button = ctk.CTkButton(button_frame, text="Run Reports", command=self.open_reporting_window)
            self.open_reports_button.pack(pady=10, padx=20, fill="x")
        if '4' in self.permissions:
            self.open_product_button = ctk.CTkButton(button_frame, text="Manage Products", command=self.open_product_window)
            self.open_product_button.pack(pady=10, padx=20, fill="x")
        if '8' in self.permissions:
            self.open_shipping_button = ctk.CTkButton(button_frame, text="Ship Sales Order", command=self.open_shipping_window)
            self.open_shipping_button.pack(pady=10, padx=20, fill="x")
        if '10' in self.permissions:
            self.open_receiving_button = ctk.CTkButton(button_frame, text="Receive Purchase Order", command=self.open_receiving_window)
            self.open_receiving_button.pack(pady=10, padx=20, fill="x")
        if '9' in self.permissions:
            self.open_po_button = ctk.CTkButton(button_frame, text="Create Purchase Order", command=self.open_po_window)
            self.open_po_button.pack(pady=10, padx=20, fill="x")
        if '6' in self.permissions:
            self.open_order_button = ctk.CTkButton(button_frame, text="Create Sales Order", command=self.open_sales_order_window)
            self.open_order_button.pack(pady=10, padx=20, fill="x")
        
        self.search_order_button = ctk.CTkButton(button_frame, text="Search / Modify Order", command=self.open_order_search_window)
        self.search_order_button.pack(pady=10, padx=20, fill="x")

    def open_sales_order_window(self):
        sales_order_win = SalesOrderWindow(self)
        sales_order_win.grab_set()

    def open_po_window(self):
        po_win = PurchaseOrderWindow(self)
        po_win.grab_set()
        
    def open_receiving_window(self):
        receiving_win = ReceivingWindow(self)
        receiving_win.grab_set()
        
    def open_shipping_window(self):
        shipping_win = ShippingWindow(self)
        shipping_win.grab_set()

    def open_product_window(self):
        product_win = ProductManagementWindow(self)
        product_win.grab_set()

    def open_reporting_window(self):
        report_win = ReportWindow(self)
        report_win.grab_set()

    def open_job_status_window(self):
        job_status_win = JobStatusWindow(self)
        job_status_win.grab_set()
        
    def open_order_search_window(self):
        order_search_win = OrderSearchWindow(self)
        order_search_win.grab_set()
