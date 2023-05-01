import os

import tqdm
from PIL import Image

from utility.utility import hide_player

# (65, 190), (65, 890) closed crafting tabs
# (420, 1010), (1500, 1010) inventory
# (900, 460), (1015, 615) character
# (1680, 0), (1920, 290) status
# (1780, 950), (1920, 1080) map icons

if __name__ == "__main__":
    imgs_path = "perception/bg_images"
    all_images = os.listdir(imgs_path)
    for image_path in tqdm.tqdm(all_images):
        full_path = f"{imgs_path}/{image_path}"
        with Image.open(full_path) as image:
            image = hide_player(image)
            image.save(f"perception/processed_bg_images/{image_path}")




