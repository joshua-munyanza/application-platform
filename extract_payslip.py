import os
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


def extract(text):
    response = client.models.generate_content(
        model=MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            # We forbid calculating on purpose: models are unreliable at
            # arithmetic, and our own code does the sums in arithmetic_ok.
            system_instruction=(
                "You read payslip text and fill in the form. "
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


def arithmetic_ok(p):
    # None means "can't check", which is different from "checked and wrong".
    if p.gross_pay_kes is None or p.net_pay_kes is None:
        return None
    total_deductions = sum(d.amount_kes for d in p.deductions)
    return p.gross_pay_kes - total_deductions == p.net_pay_kes


# Everything above only defines tools. The lines below are the first
# ones that actually run, so every function already exists by then.
text = read_pdf_text("data/payslip_001.pdf")

if text is None:
    print("No text found: this looks like a scan, needs OCR")
else:
    payslip = extract(text)
    # JSON is just labelled boxes written as text. indent=2 makes it readable.
    print(payslip.model_dump_json(indent=2))

    ok = arithmetic_ok(payslip)
    if ok is None:
        print("-> Missing figures: sent to the human review queue")
    elif ok:
        print("-> Arithmetic checks out")
    else:
        print("-> Numbers do not add up: sent to the human review queue")