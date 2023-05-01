from random import shuffle
import glob
import os

import pandas as pd
from tqdm import tqdm

from perception.constants import TRAIN, VAL, TEST
from perception.YoloIdConverter import yolo_id_converter
from utility.generate_images import generate_image

if __name__ == "__main__":
    obj_info = pd.read_csv("utility/objects_info.csv")
    IMAGES_PER_OBJECT = 400
    IMPORTANT_OBJ_COUNT_PER_IMAGE = 8
    ANNOTATIONS_PER_OBJECT = IMPORTANT_OBJ_COUNT_PER_IMAGE*IMAGES_PER_OBJECT
    MAX_OBJECTS_PER_IMAGE = 20
    important_obj_sequence = []
    important_count = 0
    for i in range(obj_info.shape[0]):
        if i in yolo_id_converter.important_classes:
            important_obj_sequence.extend([i]*ANNOTATIONS_PER_OBJECT)
            important_count += 1
    shuffle(important_obj_sequence)
    num_images = len(important_obj_sequence)//IMPORTANT_OBJ_COUNT_PER_IMAGE

    # this calculates how many not important objects there will be 
    ANNOTATIONS_PER_NOT_IMPORTANT_OBJECT = int((MAX_OBJECTS_PER_IMAGE - IMPORTANT_OBJ_COUNT_PER_IMAGE)*num_images
            /(obj_info.shape[0] - important_count))
    not_important_obj_sequence = []
    for i in range(obj_info.shape[0]):
        if i not in yolo_id_converter.important_classes:
            not_important_obj_sequence.extend([i]*ANNOTATIONS_PER_NOT_IMPORTANT_OBJECT)
    shuffle(not_important_obj_sequence)
    NOT_IMPORTANT_OBJ_COUNT_PER_IMAGE = int(len(not_important_obj_sequence)/num_images)
    assert TRAIN + VAL + TEST == 100
    previous_generated_images = glob.glob("perception/generated_images/**/*.png", recursive=True)
    previous_generated_annotations = glob.glob("perception/generated_images/**/*.txt", recursive=True)
    for f in previous_generated_images:
        os.remove(f)
    for f in previous_generated_annotations:
        os.remove(f)
    for i in tqdm(range(num_images)):
        if i <= num_images*TRAIN/100:
            subset = "train"
        elif i <= num_images*(TRAIN+VAL)/100:
            subset = "val"
        else:
            subset = "test"
        generate_image(important_obj_sequence[i*IMPORTANT_OBJ_COUNT_PER_IMAGE:(i+1)*IMPORTANT_OBJ_COUNT_PER_IMAGE], 
                        not_important_obj_sequence[i*NOT_IMPORTANT_OBJ_COUNT_PER_IMAGE:(i+1)*NOT_IMPORTANT_OBJ_COUNT_PER_IMAGE],
                        obj_info, subset, f"{i}.png")