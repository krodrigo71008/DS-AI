import os
from PIL import Image

def trim_image(image_path : str, output_path : str):
    with Image.open(image_path) as image:
        processed_image = image.crop(image.getbbox())
        output_dir = "/".join(output_path.split("/")[:-1])
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        processed_image.save(output_path)
        print(f"{image_path} to {output_path}")