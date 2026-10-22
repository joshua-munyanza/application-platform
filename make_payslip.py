import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# All made-up data lives in one dictionary, so later we can make
# hundreds of different payslips by changing only this block.
payslip = {
    "employer": "Karibu Traders Ltd",
    "employee": "Wanjiku Mwangi",
    "month": "March 2026",
    "gross": 55000,
    "deductions": {"PAYE": 6500, "NSSF": 1080, "SACCO deposit": 2420},
}

# Plain code does the arithmetic, never the model. Doing it here also
# means our "true" net pay is known exactly, which we need for testing later.
net = payslip["gross"] - sum(payslip["deductions"].values())

# exist_ok=True stops a crash on the second run, when the folder exists.
os.makedirs("data", exist_ok=True)

# Each line is (text, font size). Building a list first keeps the drawing
# code below short and easy to change.
lines = [
    (payslip["employer"], 16),
    (f"Payslip for {payslip['month']}", 12),
    (f"Employee: {payslip['employee']}", 12),
    (f"Gross pay: KES {payslip['gross']:,}", 12),
]
for name, amount in payslip["deductions"].items():
    lines.append((f"{name}: KES {amount:,}", 12))
lines.append((f"Net pay: KES {net:,}", 14))

pdf = canvas.Canvas("data/payslip_001.pdf", pagesize=A4)
width, height = A4

# PDF coordinates count UP from the bottom of the page, so we start
# near the top (height - 80) and move down after each line.
y = height - 80
for text, size in lines:
    pdf.setFont("Helvetica", size)
    pdf.drawString(60, y, text)
    y -= 28

pdf.save()
print(f"Created data/payslip_001.pdf (net pay {net})")