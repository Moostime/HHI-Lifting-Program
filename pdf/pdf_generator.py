from fpdf import FPDF
import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Work Order', 1, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_work_order_pdf(customer_data, order_items):
    pdf = PDF()
    pdf.add_page()
    
    # Customer Info
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(40, 10, f"Customer: {customer_data['customer_name']}")
    pdf.ln(10)
    
    # Table Header
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(20, 10, 'Qty', 1)
    pdf.cell(110, 10, 'Description', 1)
    pdf.cell(30, 10, 'Unit Price', 1)
    pdf.cell(30, 10, 'Extended', 1)
    pdf.ln()

    # Table Rows
    pdf.set_font('Arial', '', 10)
    total_price = 0.0
    for item in order_items:
        ext_price = item['qty'] * item['unit_price']
        total_price += ext_price
        
        pdf.cell(20, 10, str(item['qty']), 1)
        pdf.cell(110, 10, item['description1'], 1)
        pdf.cell(30, 10, f"${item['unit_price']:.2f}", 1)
        pdf.cell(30, 10, f"${ext_price:.2f}", 1)
        pdf.ln()
    
    # Total
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(160, 10, 'Total:', 1, 0, 'R')
    pdf.cell(30, 10, f"${total_price:.2f}", 1)
    pdf.ln()
    
    filename = "work_order.pdf"
    pdf.output(filename)
    return filename
