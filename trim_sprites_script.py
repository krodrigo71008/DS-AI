import glob

from utility.trim_sprites import trim_image

image_paths = glob.glob("perception\\ds_sprites/*/Output/images/*.png")

for path in image_paths:
    output_path = "/".join(["ds_sprites_processed" if path_part == "ds_sprites" else path_part for path_part in path.split("\\")])
    trim_image(path, output_path)