# import base64
# from PIL import Image
# import io

 

 
# # Function to encode the image
# def encode_image(image_path):
#     image = Image.open(image_path)
#     buffered = io.BytesIO()
#     image_format = image.format if image.format else 'PNG'  # Default to PNG if format is None
#     image.save(buffered, format=image_format)
#     return base64.b64encode(buffered.getvalue()).decode('utf-8')

 
import google.generativeai as genai
import PIL.Image



def query_image(image_path, prompt):
    """
    Query an image using Gemini Pro Vision API

    Args:
        image_path (str): Path to the image file
        prompt (str): Question or prompt for the image

    Returns:
        str: Response from the Gemini API
    """
    # Load the image
    image = PIL.Image.open(image_path)

    # Create the model
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Generate response
    response = model.generate_content(
        contents=[prompt, image],
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=2000
        )
    )

    return response.text

    # image_path = r'C:\Users\aipro\OneDrive - Promptora AI Solutions Pvt Ltd\Desktop\Pics\crime.jpg'

    # # Example prompts
    # prompts = [
    #     "What objects do you see in this image?",
    #     "Describe the colors and composition of this image",
    #     "Can you extract any text from this image?"
    # ]

    # # Query the image with different prompts
    # for prompt in prompts:
    #     print(f"Prompt: {prompt}")
    #     result = query_image(image_path, prompt)
    #     print(f"Response: {result}\n")

# Note: Before running, install required libraries:
# pip install google-generativeai Pillow