from random import shuffle

import pandas as pd
from tqdm import tqdm

from perception.YoloIdConverter import yolo_id_converter
from utility.generate_images import generate_image

if __name__ == "__main__":
    obj_info = pd.read_csv('utility/objects_info.csv')
    IMAGES_PER_OBJECT = 800
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
    train = []
    val = []
    for i in tqdm(range(num_images)):
        generate_image(important_obj_sequence[i*IMPORTANT_OBJ_COUNT_PER_IMAGE:(i+1)*IMPORTANT_OBJ_COUNT_PER_IMAGE], 
                        not_important_obj_sequence[i*NOT_IMPORTANT_OBJ_COUNT_PER_IMAGE:(i+1)*NOT_IMPORTANT_OBJ_COUNT_PER_IMAGE],
                        obj_info, f"{i}.png")
        if i < 0.8*num_images:
            train.append(f"data/img/{i}.png")
        else:
            val.append(f"data/img/{i}.png")
    with open("perception/generated_images/train.txt", "w") as train_file:
        for t in train:
            train_file.write(f"{t}\n")
    with open("perception/generated_images/val.txt", "w") as val_file:
        for v in val:
            val_file.write(f"{v}\n")
    print(f'train len: {len(train)}')
    print(f'val len: {len(val)}')