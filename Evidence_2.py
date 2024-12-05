# import base64
# from PIL import Image
# import io
# import google.generativeai as genai
# import streamlit as st


 
# # Function to encode the image
# def encode_image(image_path):
#     image = Image.open(image_path)
#     buffered = io.BytesIO()
#     image_format = image.format if image.format else 'PNG'  # Default to PNG if format is None
#     image.save(buffered, format=image_format)
#     return base64.b64encode(buffered.getvalue()).decode('utf-8')

 
import streamlit as st
import openai
import base64
import io



def encode_image_to_base64(image):
    """Convert PIL Image to Base64 encoded string."""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def analyze_image(image):
    """Analyze the image using OpenAI."""
    encoded_image = encode_image_to_base64(image)
    try:
        response = openai.Image.create(
            purpose="analyze",  # Adjust this purpose as per your API capability
            image=encoded_image,
            n=1
        )
        return response
    except Exception as e:
        return {"error": str(e)}