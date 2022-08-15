from random import shuffle

import pandas as pd

from utility.generate_images import generate_image

if __name__ == "__main__":
    obj_info = pd.read_csv('utility/objects_info.csv')
    ANNOTATIONS_PER_OBJECT = 1000
    OBJ_COUNT_PER_IMAGE = 15
    obj_sequence = []
    for i in range(obj_info.shape[0]):
        obj_sequence.extend([i]*ANNOTATIONS_PER_OBJECT)
    shuffle(obj_sequence)
    train = []
    val = []
    for i in range(len(obj_sequence)//OBJ_COUNT_PER_IMAGE):
        generate_image(obj_sequence[i*OBJ_COUNT_PER_IMAGE:(i+1)*OBJ_COUNT_PER_IMAGE], obj_info, f"{i}.png")
        if i < 0.8*len(obj_sequence)//OBJ_COUNT_PER_IMAGE:
            train.append(f"data/img/{i}.png")
        else:
            val.append(f"data/img/{i}.png")
    if (len(obj_sequence)//OBJ_COUNT_PER_IMAGE)*OBJ_COUNT_PER_IMAGE < len(obj_sequence):
        generate_image(obj_sequence[(len(obj_sequence)//OBJ_COUNT_PER_IMAGE)*OBJ_COUNT_PER_IMAGE:], obj_info, "final.png")
        val.append(f"data/img/final.png")
    with open("perception/generated_images/train.txt", "w") as train_file:
        for t in train:
            train_file.write(f"{t}\n")
    with open("perception/generated_images/val.txt", "w") as val_file:
        for v in val:
            val_file.write(f"{v}\n")