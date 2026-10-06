import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
    contents="What is the refund policy of my company?",
)

print(response.text)
print(response.usage_metadata)