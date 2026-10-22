import sys
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def make_payslip(data, path, printed_net=None):
    # The true net pay is always calculated by code from the numbers above it.
    true_net = data["gross"] - sum(data["deductions"].values())

    # printed_net lets us print a WRONG net pay on purpose, so we can test
    # our checker. Normally it stays empty and the true figure is printed.
    net = true_net if printed_net is None else printed_net

    lines = [
        (data["employer"], 16),
        (f"Payslip for {data['month']}", 12),
        (f"Employee: {data['employee']}", 12),
        (f"Gross pay: KES {data['gross']:,}", 12),
    ]
    for name, amount in data["deductions"].items():
        lines.append((f"{name}: KES {amount:,}", 12))
    lines.append((f"Net pay: KES {net:,}", 14))

    pdf = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    # PDF coordinates count UP from the bottom of the page, so we start
    # near the top and move down after each line.
    y = height - 80
    for text, size in lines:
        pdf.setFont("Helvetica", size)
        pdf.drawString(60, y, text)
        y -= 28
    pdf.save()


payslip = {
    "employer": "Karibu Traders Ltd",
    "employee": "Wanjiku Mwangi",
    "month": "March 2026",
    "gross": 55000,
    "deductions": {"PAYE": 6500, "NSSF": 1080, "SACCO deposit": 2420},
}

os.makedirs("data", exist_ok=True)

# A correct payslip, same as before.
make_payslip(payslip, "data/payslip_001.pdf")

# A faulty one: everything is right except the printed net pay.
# The true net pay is 45,000, but this one claims 48,000.
make_payslip(payslip, "data/payslip_002.pdf", printed_net=48000)

print("Created payslip_001.pdf (good) and payslip_002.pdf (net pay wrong on purpose)")