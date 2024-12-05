from PIL import Image
import pytesseract  # OCR library
import io
import base64
import streamlit as st
import google.generativeai as genai


# Function to perform OCR on the uploaded image
def extract_text_from_image(image_file):
    """Extracts text from the uploaded image using OCR."""
    image = Image.open(image_file)
    text = pytesseract.image_to_string(image)
    return text.strip()