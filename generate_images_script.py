from random import shuffle
import glob
import os
import itertools

import pandas as pd
import numpy as np
from tqdm import tqdm

from perception.YoloIdConverter import yolo_id_converter
from utility.generate_images import generate_image

if __name__ == "__main__":
    obj_info = pd.read_csv("utility/objects_info.csv")
    MINIMUM_IMAGE_USAGE = 0.6 # should be between 0 and 1
    MINIMUM_ANNOTATIONS_PER_IMPORTANT_CLASS = 500
    IMPORTANT_OBJ_COUNT_PER_IMAGE = 8
    MAX_OBJECTS_PER_IMAGE = 20

    max_image_count = -1
    id_to_image_paths = {} # image_id maps to an array with image_paths
    for i in range(obj_info.shape[0]):
        id_to_image_paths[i] = []
        folders = [s.strip()[1:-1] for s in obj_info["image_paths"].iloc[i][1:-1].split(",")]
        for folder_str in folders:
            combo_aux = []
            for folder in folder_str.split("+"):
                imgs_path = f"perception/ds_sprites_processed/{folder}/Output/images"
                combo_aux.append([f"{imgs_path}/{file}" for file in os.listdir(imgs_path)])
            combos = list(itertools.product(*combo_aux))
            id_to_image_paths[i].extend(["+".join(tuple(str(item) for item in c)) for c in combos])
        if max_image_count == -1 or len(id_to_image_paths[i]) > max_image_count:
            max_image_count = len(id_to_image_paths[i])

    annotations_per_important_object = int(max_image_count*MINIMUM_IMAGE_USAGE)
    if annotations_per_important_object < MINIMUM_ANNOTATIONS_PER_IMPORTANT_CLASS:
        annotations_per_important_object = MINIMUM_ANNOTATIONS_PER_IMPORTANT_CLASS
    important_obj_sequence = []
    for i in range(obj_info.shape[0]):
        if i in yolo_id_converter.important_classes:
            values = np.arange(len(id_to_image_paths[i])) # array with values from 0 to the number of images
            # repeats the values and trim
            repeated_values = np.tile(values, int(np.ceil(annotations_per_important_object / len(id_to_image_paths[i]))))[:annotations_per_important_object] 
            important_obj_sequence.extend([(i, v, obj_info.iloc[i]['image_size']) for v in repeated_values]) # annotate id and image index
    shuffle(important_obj_sequence)
    num_images = int(len(important_obj_sequence)/IMPORTANT_OBJ_COUNT_PER_IMAGE)
    total_not_important_annotations = (MAX_OBJECTS_PER_IMAGE - IMPORTANT_OBJ_COUNT_PER_IMAGE)*num_images
    # this calculates how many not important objects there will be 
    annotations_per_not_important_object = int(np.ceil(total_not_important_annotations/(obj_info.shape[0] - len(yolo_id_converter.important_classes))))
    not_important_obj_sequence = []
    for i in range(obj_info.shape[0]):
        if i not in yolo_id_converter.important_classes:
            values = np.arange(len(id_to_image_paths[i])) # array with values from 0 to the number of images
            # repeats the values and trim
            repeated_values = np.tile(
                values, int(np.ceil(annotations_per_not_important_object / len(id_to_image_paths[i])))
            )[:annotations_per_not_important_object] 
            not_important_obj_sequence.extend([(i, v, obj_info.iloc[i]['image_size']) for v in repeated_values]) # annotate id and image index
        not_important_object_count_per_image = MAX_OBJECTS_PER_IMAGE - IMPORTANT_OBJ_COUNT_PER_IMAGE
    shuffle(not_important_obj_sequence)
    previous_generated_images = glob.glob("perception/generated_images/**/*.png", recursive=True)
    previous_generated_annotations = glob.glob("perception/generated_images/**/*.txt", recursive=True)
    for f in previous_generated_images:
        os.remove(f)
    for f in previous_generated_annotations:
        os.remove(f)
    for i in tqdm(range(num_images)):
        subset = "train"
        generate_image(important_obj_sequence[i*IMPORTANT_OBJ_COUNT_PER_IMAGE:(i+1)*IMPORTANT_OBJ_COUNT_PER_IMAGE], 
                        not_important_obj_sequence[i*not_important_object_count_per_image:(i+1)*not_important_object_count_per_image],
                        id_to_image_paths, subset, f"{i}.png")