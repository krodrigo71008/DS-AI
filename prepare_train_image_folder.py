import glob
from pathlib import Path
import shutil
import random
from tqdm import tqdm
import os

from PIL import Image

from perception.constants import TRAIN, VAL, TEST

gen_path = Path("perception/generated_images/")
train_path = Path("perception/train_images/")

# in each folder, there should be 3 folders: train, val and test, in each one of these there should be two folders: images and labels
gen_files = glob.glob("perception/generated_images/**/*.png", recursive=True)
gen_files.extend(glob.glob("perception/generated_images/**/*.txt", recursive=True))

previous_train_images = glob.glob("perception/train_images/**/images/*.png", recursive=True)
previous_train_images.extend(glob.glob("perception/train_images/**/images/*.jpg", recursive=True))
previous_train_annotations = glob.glob("perception/train_images/**/labels/*.txt", recursive=True)
for f in previous_train_images:
    os.remove(f)
for f in previous_train_annotations:
    os.remove(f)

for file in tqdm(gen_files, desc="copying generated images"):
    file_copy = file.replace("generated_images", "train_images")
    file_copy = str(Path(file_copy).parent / f"gen{Path(file_copy).name}")
    shutil.copyfile(file, file_copy)

assert TRAIN + VAL + TEST == 100
train_images = glob.glob("perception/train_images/*.jpg")
random.shuffle(train_images)
for i, image_file in enumerate(tqdm(train_images, desc="copying train_image images and labels")):
    image = Image.open(image_file)
    image.resize((640, 640))
    text_file = image_file.replace(".jpg", ".txt")
    if i <= len(train_images)*TRAIN/100:
        subset = "train"
    elif i <= len(train_images)*(TRAIN+VAL)/100:
        subset = "val"
    else:
        subset = "test"
    img_destination = f"perception/train_images/{subset}/images/" + "nat" + Path(image_file).name
    txt_destination = f"perception/train_images/{subset}/labels/" + "nat" + Path(text_file).name
    image.save(img_destination)
    shutil.copyfile(text_file, txt_destination)
    os.remove(image_file)
    os.remove(text_file)
