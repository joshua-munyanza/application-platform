import os
from google import genai

# Read the key from the environment so it never appears in this file.
# Square brackets (not .get) make the program crash loudly if the key is
# missing, instead of failing in a confusing way later.
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# The API lists every model it offers, including ones that only make images
# or embeddings. We keep just the ones that can generate text, since that
# is the only kind we need right now.
for model in client.models.list():
    if "generateContent" in (model.supported_actions or []):
        print(model.name)