from pypdf import PdfReader

reader = PdfReader("data/payslip_001.pdf")

# A payslip is one page. Later we'll loop over pages for longer documents.
text = reader.pages[0].extract_text()

# A scanned document is only a picture, so extract_text returns nothing.
# Catching that here stops us sending an empty string to the model,
# which could answer with a confident, made-up payslip.
if not text or not text.strip():
    print("No text found: this looks like a scan and needs OCR (a later lesson)")
else:
    print(text)