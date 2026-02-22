import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lu_backend.settings')
django.setup()

import google.generativeai as genai

GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found!")
genai.configure(api_key=GEMINI_API_KEY)

print("Available models:")
models = genai.list_models()
for model in models:
    print(f"- {model.name}: {model.supported_generation_methods}")
