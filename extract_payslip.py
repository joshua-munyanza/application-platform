import os
import sys
from typing import Optional

from google import genai
from google.genai import types
from pydantic import BaseModel
from pypdf import PdfReader

MODEL = "gemini-3.5-flash-lite"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# One row of the deductions table, like "PAYE: 6,500".
class Deduction(BaseModel):
    name: str
    amount_kes: int


# The whole form. Every single value is Optional so the model has an
# honest way to say "not on the document" instead of inventing a number.
class Payslip(BaseModel):
    employer: Optional[str]
    employee_name: Optional[str]
    month: Optional[str]
    gross_pay_kes: Optional[int]
    # A list, because payslips have a different number of deduction lines.
    deductions: list[Deduction]
    net_pay_kes: Optional[int]


def read_pdf_text(path):
    reader = PdfReader(path)
    text = reader.pages[0].extract_text()
    # A scan has no text. Stopping here beats sending an empty string
    # to the model, which might answer with a made-up payslip.
    if not text or not text.strip():
        return None
    return text


def extract(contents):
    # "contents" can be plain text OR a list holding a picture plus an
    # instruction, so one function serves both routes.
    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            # We forbid calculating on purpose: models are unreliable at
            # arithmetic, and our own code does the sums in arithmetic_ok.
            system_instruction=(
                "You read a payslip, given as text or as an image, "
                "and fill in the form. "
                "Copy values exactly as written. "
                "If a value is missing or unreadable, use null. "
                "Never calculate, guess or invent a number. "
                "List every deduction line separately. "
                "Write amounts as whole numbers without commas."
            ),
            response_mime_type="application/json",
            response_schema=Payslip,
            temperature=0,
        ),
    )
    return response.parsed


def load_payslip(path):
    # Pictures go straight to the model. Text PDFs go through our own
    # reader first, because reading real text is cheaper and more exact
    # than asking a model to look at pixels.
    if path.lower().endswith(".png"):
        # "rb" means read raw bytes: an image is not text.
        with open(path, "rb") as f:
            image_bytes = f.read()
        picture = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        return extract([picture, "This image is a payslip. Fill in the form."])

    text = read_pdf_text(path)
    if text is None:
        return None
    return extract(text)


def arithmetic_ok(p):
    # None means "can't check", which is different from "checked and wrong".
    if p.gross_pay_kes is None or p.net_pay_kes is None:
        return None
    total_deductions = sum(d.amount_kes for d in p.deductions)
    return p.gross_pay_kes - total_deductions == p.net_pay_kes


# Everything above only defines tools. The lines below are the first
# ones that actually run, so every function already exists by then.
# sys.argv holds the words typed after "python", so we can pick the file.
path = sys.argv[1] if len(sys.argv) > 1 else "data/payslip_001.pdf"
payslip = load_payslip(path)

if payslip is None:
    print("No text found: this looks like a scan, needs OCR")
else:
    # JSON is just labelled boxes written as text. indent=2 makes it readable.
    print(payslip.model_dump_json(indent=2))

    ok = arithmetic_ok(payslip)
    if ok is None:
        print("-> Missing figures: sent to the human review queue")
    elif ok:
        print("-> Arithmetic checks out")
    else:
        print("-> Numbers do not add up: sent to the human review queue")