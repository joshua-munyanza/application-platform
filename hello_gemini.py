import os
from google import genai

# Pinned to one exact model so results stay repeatable. "-latest" names
# change silently underneath you, which would break our tests later.
MODEL = "gemini-3.5-flash"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model=MODEL,
    contents="In one sentence, what does a loan officer do?",
)

# The reply object carries extra details too; .text is just the words.
print(response.text)