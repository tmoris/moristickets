import os
import secrets
from PIL import Image
from flask import current_app, flash


def image_saver(image, folder):
    try:
        img_name_base = secrets.token_hex(8)
        _, file_ext = os.path.splitext(image.filename)
        image_name = img_name_base + file_ext
        image_path = os.path.join(
            current_app.root_path, "static/img/" + folder, image_name
        )

        # Image resizing
        img_size = (400, 400)
        i = Image.open(image)
        i.thumbnail(img_size)
        i.save(image_path, quality=95)
        return image_name
    except Exception as e:
        flash(f"An error occurred while saving the image: {e}")
