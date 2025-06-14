import os
import secrets
from PIL import Image
from flask import current_app

def save_profile_pic(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static', 'profile_pic', picture_fn) # Use os.path.join correctly

    # Resize image to 125x125
    output_size = (125, 125)
    i = Image.open(form_picture) # Open the image using PIL
    i.thumbnail(output_size)     # Resize it
    i.save(picture_path)         # Save the RESIZED image

    # Add a print statement to confirm the path and filename
    print(f"DEBUG: Saved profile picture to: {picture_path}")

    return picture_fn