import PIL.Image

GOOGLE_APPLICATION_CREDENTIALS = "diesel-ally-408507-b62137162042.json"

def get_image(uploaded_image):
    img = PIL.Image.open(uploaded_image)
    return img
