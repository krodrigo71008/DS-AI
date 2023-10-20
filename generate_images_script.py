from random import shuffle
import glob
import os
import itertools
import time

import pandas as pd
import numpy as np

from perception.YoloIdConverter import yolo_id_converter
from utility.generate_images import generate_image

if __name__ == "__main__":
    obj_info = pd.read_csv("utility/objects_info.csv")
    MINIMUM_IMAGE_USAGE = 0.5 # should be between 0 and 1
    MINIMUM_ANNOTATIONS_PER_IMPORTANT_CLASS = 500
    NOT_IMPORTANT_OBJECTS_PER_IMAGE_RANGE = (0, 25)
    IMPORTANT_OBJECTS_PER_IMAGE_RANGE = (0, 10)

    important_max_image_count = -1
    not_important_max_image_count = -1
    id_to_image_paths = {} # image_id maps to an array with image_paths
    all_important_folders = []
    for i in range(obj_info.shape[0]):
        aux = []
        folders = [s.strip()[1:-1] for s in obj_info["image_paths"].iloc[i][1:-1].split(",")]
        for folder_str in folders:
            combo_aux = []
            for folder in folder_str.split("+"):
                if i in yolo_id_converter.important_classes:
                    all_important_folders.append(folder)
                imgs_path = f"perception/ds_sprites_processed/{folder}/Output/images"
                combo_aux.append([f"{imgs_path}/{file}" for file in os.listdir(imgs_path)])
            combos = list(itertools.product(*combo_aux))
            aux.extend(["+".join(tuple(str(item) for item in c)) for c in combos])
        # important_max_image_count is the max number of sprites (or sprite combos) associated with a single class
        if i in yolo_id_converter.important_classes:
            if important_max_image_count == -1 or len(aux) > important_max_image_count:
                important_max_image_count = len(aux)
        else:
            if not_important_max_image_count == -1 or len(aux) > not_important_max_image_count:
                not_important_max_image_count = len(aux)
        if len(aux) > 0:
            id_to_image_paths[i] = aux


    annotations_per_important_object = int(important_max_image_count*MINIMUM_IMAGE_USAGE)
    if annotations_per_important_object < MINIMUM_ANNOTATIONS_PER_IMPORTANT_CLASS:
        annotations_per_important_object = MINIMUM_ANNOTATIONS_PER_IMPORTANT_CLASS
    important_obj_sequence = []
    for i in range(obj_info.shape[0]):
        if i in yolo_id_converter.important_classes:
            values = np.arange(len(id_to_image_paths[i])) # array with values from 0 to the number of images
            # repeats the values and trims
            repeated_values = np.tile(values, int(np.ceil(annotations_per_important_object / len(id_to_image_paths[i]))))[:annotations_per_important_object] 
            important_obj_sequence.extend([(i, v, obj_info.iloc[i]['image_size']) for v in repeated_values]) # annotate id, image index and image size
    shuffle(important_obj_sequence)
    not_important_folders = [folder_str for folder_str in glob.glob("perception/ds_sprites_processed/*") 
                             if folder_str.split("\\")[-1] not in all_important_folders]
    # I have to add objects to object_info if I want to generate images with them since I need to know their size
    not_important_obj_list = []
    for i in range(obj_info.shape[0]):
        if i not in yolo_id_converter.important_classes:
            values = np.arange(len(id_to_image_paths[i])) # array with values from 0 to the number of images
            # repeats the values and trims
            repeated_values = np.tile(values, int(np.ceil(not_important_max_image_count / len(id_to_image_paths[i]))))[:not_important_max_image_count] 
            not_important_obj_list.extend([(i, v, obj_info.iloc[i]['image_size']) for v in repeated_values]) # annotate id, image index and image size
    shuffle(not_important_obj_list)
    previous_generated_images = glob.glob("perception/generated_images/**/*.png", recursive=True)
    previous_generated_annotations = glob.glob("perception/generated_images/**/*.txt", recursive=True)
    for f in previous_generated_images:
        os.remove(f)
    for f in previous_generated_annotations:
        os.remove(f)
    important_index = 0
    not_important_index = 0
    start = time.time()
    while important_index < len(important_obj_sequence):
        subset = "train"
        important_index, not_important_index = generate_image(important_obj_sequence, important_index, not_important_obj_list, not_important_index,
                                         id_to_image_paths, subset, f"{important_index}.png", IMPORTANT_OBJECTS_PER_IMAGE_RANGE, 
                                         NOT_IMPORTANT_OBJECTS_PER_IMAGE_RANGE)
        now = time.time()
        if important_index > 0:
            print(f"Progress: {important_index}/{len(important_obj_sequence)}, time: {now - start:.1f}/{(now - start)/important_index*len(important_obj_sequence):.1f}")
    print("Done!")