from PIL import Image, ImageDraw, ImageFont

# The same payslip lines as before, typed again here so this file works
# on its own. This time they will be drawn as PIXELS, not stored as text.
lines = [
    "Karibu Traders Ltd",
    "Payslip for March 2026",
    "Employee: Wanjiku Mwangi",
    "Gross pay: KES 55,000",
    "PAYE: KES 6,500",
    "NSSF: KES 1,080",
    "SACCO deposit: KES 2,420",
    "Net pay: KES 45,000",
]

# A blank white page. 800 x 600 pixels is plenty for 8 short lines.
image = Image.new("RGB", (800, 600), "white")
draw = ImageDraw.Draw(image)

# The built-in font is tiny by default, so we ask for a bigger size
# to keep the picture easy to read.
font = ImageFont.load_default(size=28)

y = 40
for line in lines:
    draw.text((40, y), line, fill="black", font=font)
    y += 50

image.save("data/payslip_scan.png")

# A PDF made from a picture holds no real text, just like the PDF a
# scanner produces. That is exactly what we want to test our reader on.
image.save("data/payslip_scan.pdf")

print("Created data/payslip_scan.png and data/payslip_scan.pdf")