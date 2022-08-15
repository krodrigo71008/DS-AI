import os

from PIL import Image, ImageDraw

# (65, 190), (65, 890) closed crafting tabs
# (420, 1010), (1500, 1010) inventory
# (900, 460), (1015, 615) character
# (1680, 0), (1920, 290) status
# (1780, 950), (1920, 1080) map icons

if __name__ == "__main__":
    limits = [(0, 190, 65, 890), (420, 1010, 1500, 1080), (850, 410, 1065, 665), (1680, 0, 1920, 290), (1780, 950, 1920, 1080)]
    imgs_path = "perception/bg_images"
    all_images = os.listdir(imgs_path)
    for image_path in all_images:
        full_path = f"{imgs_path}/{image_path}"
        with Image.open(full_path) as image:
            draw = ImageDraw.Draw(image)
            for limit in limits:
                draw.rectangle(limit, fill=0)
            del draw
            image.save(f"perception/processed_bg_images/{image_path}")




