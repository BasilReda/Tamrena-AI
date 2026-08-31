import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

from app.core.llm import GoogleGenAIChat

model_name = os.getenv("GEMINI_MODEL") or os.getenv("MODEL_NAME") or "gemini-3.5-flash-lite"
print(f"Testing Nutrition LLM with model: '{model_name}'")

llm = GoogleGenAIChat(model_id=model_name, temperature=0.7)
response = llm.invoke("What is a healthy high-protein Egyptian breakfast?")

print("\n=== Success Response ===")
print(response.content)
