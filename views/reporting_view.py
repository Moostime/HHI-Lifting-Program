import customtkinter as ctk
from dal.reporting_dal import get_sales_by_customer

class ReportWindow(ctk.CTkToplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Sales Report by Customer")
        self.geometry("800x600")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Options Frame ---
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.start_label = ctk.CTkLabel(self.options_frame, text="Start Date (YYYY-MM-DD):")
        self.start_label.pack(side="left", padx=10, pady=10)
        self.start_entry = ctk.CTkEntry(self.options_frame)
        self.start_entry.pack(side="left", padx=5, pady=10)
        
        self.end_label = ctk.CTkLabel(self.options_frame, text="End Date (YYYY-MM-DD):")
        self.end_label.pack(side="left", padx=10, pady=10)
        self.end_entry = ctk.CTkEntry(self.options_frame)
        self.end_entry.pack(side="left", padx=5, pady=10)

        self.run_button = ctk.CTkButton(self.options_frame, text="Run Report", command=self.run_report)
        self.run_button.pack(side="left", padx=10, pady=10)

        # --- Results Frame ---
        self.results_frame = ctk.CTkScrollableFrame(self, label_text="Report Results")
        self.results_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=2) # Customer Name
        self.results_frame.grid_columnconfigure(1, weight=1) # Order Count
        self.results_frame.grid_columnconfigure(2, weight=1) # Total Sales

    def run_report(self):
        start_date = self.start_entry.get()
        end_date = self.end_entry.get()

        if not start_date or not end_date:
            print("Please enter a start and end date.")
            return

        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        report_data = get_sales_by_customer(start_date, end_date)

        # Create a header
        header_font = ctk.CTkFont(weight="bold")
        ctk.CTkLabel(self.results_frame, text="Customer Name", font=header_font).grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(self.results_frame, text="Order Count", font=header_font).grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(self.results_frame, text="Total Sales", font=header_font).grid(row=0, column=2, sticky="w", padx=5)

        # Populate data
        for index, row_data in enumerate(report_data):
            ctk.CTkLabel(self.results_frame, text=row_data['customer_name']).grid(row=index + 1, column=0, sticky="w", padx=5)
            ctk.CTkLabel(self.results_frame, text=str(row_data['order_count'])).grid(row=index + 1, column=1, sticky="w", padx=5)
            ctk.CTkLabel(self.results_frame, text=f"${row_data['total_sales']:.2f}").grid(row=index + 1, column=2, sticky="w", padx=5)
