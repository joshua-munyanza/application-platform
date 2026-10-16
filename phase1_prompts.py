import os
from google import genai
from google.genai import types
import time
from google.genai import errors

MODEL = "gemini-3.5-flash-lite"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Deliberately vague: no briefing, no format, no rules. We want to see
# what the model does when nobody tells it how to behave, so the fix
# in the next piece has something to be compared against.
# The briefing lives in system_instruction, separate from the payslip,
# so the same rules apply to every document without us repeating them
# and so a document's own text can't easily rewrite them.
from typing import Literal
from pydantic import BaseModel

# This class is the form. Literal limits "recommendation" to exactly
# three allowed words, so our code never has to guess what the model meant.
class Assessment(BaseModel):
    applicant_name: str
    net_pay_kes: int
    recommendation: Literal["approve", "reject", "review"]
    reason: str

response = client.models.generate_content(
    model=MODEL,
    contents="Payslip: Wanjiku Mwangi, net pay KES 45,000. Should we lend her money?",
    config=types.GenerateContentConfig(
        system_instruction=(
            "You are a careful loan-application assistant at a Kenyan SACCO. "
            "You never make the final lending decision; a human does. "
            "Reply in at most two sentences, in plain English."
        ),
                # Without these two lines the model may still answer in prose.
        # Together they make it fill in the form above instead.
        response_mime_type="application/json",
        response_schema=Assessment,
    ),
)



# .parsed hands back a real Python object, so we read named fields
# instead of digging through raw text.
result = response.parsed
print(result.applicant_name)
print(result.net_pay_kes)
print(result.recommendation)
print(result.reason)

# The model only suggests; our own code decides what happens next.
# Literal guarantees exactly three possible values, so this check can
# never be fooled by a creative spelling like "maybe approve".
if result.recommendation == "review":
    print("-> Sent to the human review queue")
else:
    print("-> Recommendation recorded:", result.recommendation)