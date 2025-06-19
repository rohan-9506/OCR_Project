import os
import io
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
from dotenv import load_dotenv
import requests
import json
import re

# Load environment variables
load_dotenv()

USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() == "true"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# OCR for image bytes
def image_to_text(image_bytes):
    print("[🔍] Performing OCR on image...")
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    text = pytesseract.image_to_string(image)
    print("[✅] OCR completed for image.")
    return text

# OCR for PDF pages (converted to images)
def pdf_to_text_via_ocr(pdf_bytes):
    print("[📄] Converting PDF to images for OCR...")
    images = convert_from_bytes(pdf_bytes)
    print(f"[🖼️] Converted {len(images)} pages.")
    full_text = ""
    for i, image in enumerate(images):
        print(f"[🔍] OCR on page {i + 1}...")
        text = pytesseract.image_to_string(image)
        full_text += f"\n--- Page {i + 1} ---\n{text}"
    print("[✅] OCR completed for PDF.")
    return full_text

# Basic text cleanup
def clean_text(text):
    print("[🧹] Cleaning extracted text...")
    cleaned = re.sub(r'[^\x20-\x7E\n]+', '', text).strip()
    print(f"[📏] Cleaned text length: {len(cleaned)} characters")
    return cleaned
def call_gemini_api(text):
    prompt = f"""
You are a smart document analysis assistant.

Given the following document text, perform the following tasks:
1. Identify the document type (e.g., Invoice, ID, Receipt, Form, Contract, etc.)
2. Extract only the most important fields relevant to this document (such as Name, Date of Birth, Email, Phone, Address, Amount, Invoice Number, etc.)
3. Generate a concise 2-3 line summary about the document.

Return the output in this JSON format:
{{
  "document_type": "<document type>",
  "fields": {{
    "<Field Name 1>": "<Value 1>",
    "<Field Name 2>": "<Value 2>"
  }},
  "summary": "<Brief summary here>"
}}

Document text:
{text}
"""

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    data = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        response = requests.post(GEMINI_URL, headers=headers, params=params, json=data)
        result = response.json()
        reply_text = result['candidates'][0]['content']['parts'][0]['text']
        print("🔍 Gemini response raw text:\n", reply_text)

        # Remove code block markers if present
        clean_json = re.sub(r"```json|```", "", reply_text).strip()
        return json.loads(clean_json)

    except Exception as e:
        print("❌ Gemini API error:", e)
        return {
            "document_type": "unknown",
            "fields": {},
            "summary": "Could not extract using Gemini.",
            "raw_text": text[:500]  # Show preview
        }

# Main extraction entry point
def extract_form_data(file_bytes):
    try:
        # Determine file type
        if file_bytes[:4] == b"%PDF":
            print("[📂] Detected PDF input.")
            raw_text = pdf_to_text_via_ocr(file_bytes)
        else:
            print("[🖼️] Detected image input.")
            raw_text = image_to_text(file_bytes)

        raw_text = clean_text(raw_text)

        # Print full extracted text for debugging
        print("\n[📜] Extracted Text:\n", raw_text)

        if USE_GEMINI and GEMINI_API_KEY:
            return call_gemini_api(raw_text)
        else:
            print("[⚠️] Gemini disabled. Returning raw text only.")
            return {
                "document_type": "unknown",
                "fields": {},
                "summary": "Gemini not used. Text extracted only.",
                "raw_text": raw_text
            }

    except Exception as e:
        print("❌ Error in extract_form_data:", e)
        return {
            "document_type": "unknown",
            "fields": {},
            "summary": "Error during extraction."
        }
