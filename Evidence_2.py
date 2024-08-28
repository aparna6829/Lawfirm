import base64
from PIL import Image
import io

 

 
# Function to encode the image
def encode_image(image_path):
    image = Image.open(image_path)
    buffered = io.BytesIO()
    image_format = image.format if image.format else 'PNG'  # Default to PNG if format is None
    image.save(buffered, format=image_format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

 
