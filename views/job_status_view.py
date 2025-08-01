import customtkinter as ctk
from dal.job_status_dal import get_wip_orders

class JobStatusWindow(ctk.CTkToplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Job Status (Work In Progress)")
        self.geometry("1100x700")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Results Frame ---
        self.results_frame = ctk.CTkScrollableFrame(self, label_text="Live Job Status")
        self.results_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Configure columns for the grid layout inside the scrollable frame
        self.results_frame.grid_columnconfigure(0, weight=1) # Order #
        self.results_frame.grid_columnconfigure(1, weight=3) # Customer
        self.results_frame.grid_columnconfigure(2, weight=4) # Description
        self.results_frame.grid_columnconfigure(3, weight=2) # WIP Date
        self.results_frame.grid_columnconfigure(4, weight=2) # Tested Date

        self.load_job_status()

    def load_job_status(self):
        """Fetches and displays the WIP orders in a grid."""
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        wip_orders = get_wip_orders()

        # Create a header
        header_font = ctk.CTkFont(weight="bold")
        headers = ["Order #", "Customer", "Description", "WIP Date", "Tested Date"]
        for col, header_text in enumerate(headers):
            ctk.CTkLabel(self.results_frame, text=header_text, font=header_font).grid(row=0, column=col, sticky="w", padx=5, pady=5)

        # Populate data
        for index, order in enumerate(wip_orders):
            row = index + 1 # Start data on row 1
            ctk.CTkLabel(self.results_frame, text=order['order_num']).grid(row=row, column=0, sticky="w", padx=5)
            ctk.CTkLabel(self.results_frame, text=order['customer_name']).grid(row=row, column=1, sticky="w", padx=5)
            ctk.CTkLabel(self.results_frame, text=order['description1']).grid(row=row, column=2, sticky="w", padx=5)
            ctk.CTkLabel(self.results_frame, text=str(order['wip_date'])).grid(row=row, column=3, sticky="w", padx=5)
            ctk.CTkLabel(self.results_frame, text=str(order['tested_date']) if order['tested_date'] else "").grid(row=row, column=4, sticky="w", padx=5)
