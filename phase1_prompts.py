import os
import time
from typing import Literal

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

# Pinned to one exact model so results stay repeatable. This Lite model
# has a free daily allowance of 500 requests, versus 20 for the bigger one.
MODEL = "gemini-3.5-flash-lite"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# This class is the form. Literal limits "recommendation" to exactly
# three allowed words, so our code never has to guess what the model meant.
class Assessment(BaseModel):
    applicant_name: str
    net_pay_kes: int
    recommendation: Literal["approve", "reject", "review"]
    reason: str


def assess(payslip_text):
    # One function around the model call gives us a single place to add
    # error handling, instead of repeating it wherever we ask the model.
    response = client.models.generate_content(
        model=MODEL,
        contents=payslip_text,
        config=types.GenerateContentConfig(
            # The briefing lives here, separate from the payslip, so the same
            # rules apply to every document without us repeating them.
            system_instruction=(
                "You are a careful loan-application assistant at a Kenyan SACCO. "
                "You never make the final lending decision; a human does. "
                "Keep the reason to one plain-English sentence."
            ),
            # Without these two lines the model may still answer in prose.
            # Together they make it fill in the form above instead.
            response_mime_type="application/json",
            response_schema=Assessment,
            # Zero asks for the most predictable answer. Our tests in
            # Phase 8 compare runs, so random variation would look like errors.
            temperature=0,
        ),
    )
    # .parsed hands back a real Python object, so we read named fields
    # instead of digging through raw text.
    return response.parsed


# Only these two errors fix themselves with time: 429 (slow down) and
# 503 (busy). Anything else, like a wrong model name, will fail the same
# way every time, so retrying it would just waste the user's time.
RETRYABLE = {429, 503}


def assess_with_retry(payslip_text, max_attempts=4):
    wait = 2
    for attempt in range(1, max_attempts + 1):
        try:
            return assess(payslip_text)
        except errors.APIError as err:
            # On the last attempt we stop hiding the error, so a real
            # outage is visible instead of looping forever.
            if err.code not in RETRYABLE or attempt == max_attempts:
                raise
            print(f"Busy (error {err.code}), waiting {wait}s before try {attempt + 1}...")
            time.sleep(wait)
            # Doubling the wait gives a struggling server room to recover,
            # instead of everyone hammering it at the same speed.
            wait *= 2


result = assess_with_retry(
    "Payslip: Wanjiku Mwangi, net pay KES 45,000. Should we lend her money?"
)

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