from random import randint, random
import os

import pandas as pd
import numpy as np
from PIL import Image, ImageEnhance

from perception.YoloIdConverter import yolo_id_converter
from perception.constants import SCREEN_SIZE

def choose_random_in_array(arr : list):
    num = randint(0, len(arr)-1)
    return arr[num]

def rectangles_intersect(ret1: tuple[int, int, int, int], ret2: tuple[int, int, int, int]) -> bool:
    """Checks if two rectangles intersect

    :param ret1: x and y coordinates of top left corner and bottom right corner
    :type ret1: tuple[int, int, int, int]
    :param ret2: x and y coordinates of top left corner and bottom right corner
    :type ret2: tuple[int, int, int, int]
    :return: True if the rectangles intersect, False otherwise
    :rtype: bool
    """
    l1 = (ret1[0], ret1[1])
    r1 = (ret1[2], ret1[3])
    l2 = (ret2[0], ret2[1])
    r2 = (ret2[2], ret2[3])

    if l1[0] == r1[0] or l1[1] == r1[1] or l2[0] == r2[0] or l2[1] == r2[1]:
        return False
    
    if l1[0] > r2[0] or l2[0] > r1[0]:
        return False
    
    if r1[1] < l2[1] or r2[1] < l1[1]:
        return False
    
    return True

def check_validity(xy: tuple[int, int], size: tuple[int, int]) -> bool:
    """Checks whether a spot is valid to put an object

    :param xy: x and y coords of top left corner
    :type xy: tuple[int, int]
    :param size: size of the bounding box
    :type size: tuple[int, int]
    :return: True if position is valid, False otherwise
    :rtype: bool
    """
    limits = [(0, 190, 65, 890), (420, 1010, 1500, 1080), (850, 410, 1065, 665), (1680, 0, 1920, 290), (1780, 950, 1920, 1080)]
    # check if the given bb intersects with any of the forbidden areas
    for bb in limits:
        if rectangles_intersect((xy[0], xy[1], xy[0]+size[0], xy[1]+size[1]), bb):
            return False
    return True

def paste_object_into_image(tupl : tuple[int, int, str], image : Image.Image, 
        id_to_image_paths : dict, zone : tuple[int, int, int, int] = (0, 0, SCREEN_SIZE["width"], SCREEN_SIZE["height"])) -> list[list[int]]:
    """Pastes an object with tupl into image in a random location unless specified by the zone argument

    :param tupl: tuple with image_id, index and image size
    :type tupl: tuple[int, int, str]
    :param image: image to paste the object image
    :type image: Image.Image
    :param id_to_image_paths: mapping from image_id to image paths
    :type id_to_image_paths: dict
    :param zone: bounding box in which to put the object
    :type zone: tuple[int, int, int, int]
    :return: list with bounding boxes
    :rtype: list[list[int]]
    """
    image_id, i, max_size_class = tupl
    path_str = id_to_image_paths[image_id][i]
    width_list = []
    height_list = []
    paths = path_str.split("+")
    for path in paths:
        with Image.open(path) as new_image:
            width_list.append(new_image.size[0])
            height_list.append(new_image.size[1])
    if max_size_class == "SMALL":
        max_size = randint(50, 150)
    elif max_size_class == "MEDIUM":
        max_size = randint(75, 300)
    else:
        # LARGE
        max_size = randint(200, 400)
    scale_factor = max(max(width_list), max(height_list))/max_size
    if scale_factor < 1:
        width = max(width_list)
        height = max(height_list)
    else:
        width = int(max(width_list)/scale_factor)
        height = int(max(height_list)/scale_factor)
    # generate appropriate x and y
    # this lets 20% of the sprite to generate off the zone
    random_x = randint(int(-.2*width)+zone[0], int(zone[2]-1-width*.8))
    random_y = randint(int(-.2*height)+zone[1], int(zone[3]-1-height*.8))
    # while not check_validity((random_x, random_y), (width, height)):
    #     random_x = randint(int(-.2*width)+zone[0], int(zone[2]-1-width*.8))
    #     random_y = randint(int(-.2*height)+zone[1], int(zone[3]-1-height*.8))
    if len(paths) == 1:
        offsets = [(0, 0)]
    else:
        if paths[0].find("campfire") != -1:
            offsets = [((width_list[1]-width_list[0]+15)/2/scale_factor, (height_list[1] - height_list[0]*0.1-15)/scale_factor), (0, 0)]
        else:
            raise NotImplementedError("No offsets for everything that's not a campfire!")
    day_color = (255/255, 230/255, 158/255)
    dusk_color = (150/255, 150/255, 150/255)
    bb_list = []
    for i, chosen_img in enumerate(paths):
        with Image.open(chosen_img) as added_image:
            image_to_paste = added_image.resize((int(added_image.size[0]/scale_factor), int(added_image.size[1]/scale_factor)))
            image_to_paste = np.array(image_to_paste)
            if randint(0, 1) == 0:
                image_to_paste[:, :, 0:3] = image_to_paste[:, :, 0:3] * np.array(day_color)
            else:
                image_to_paste[:, :, 0:3] = image_to_paste[:, :, 0:3] * np.array(dusk_color)
            image_to_paste = Image.fromarray(image_to_paste, mode="RGBA")
            # enhancer changes the image's brightness
            enhancer = ImageEnhance.Brightness(image_to_paste)
            image.paste(enhancer.enhance(random()*1.5+0.25), 
                (int(random_x+offsets[i][0]), int(random_y+offsets[i][1])), 
                image_to_paste)
            bb_list.append([int(random_x+offsets[i][0]), 
                            int(random_y+offsets[i][1]), 
                            int(random_x+offsets[i][0]) + image_to_paste.size[0], 
                            int(random_y+offsets[i][1]) + image_to_paste.size[1]])
    return bb_list

def generate_image(important_obj_list: list[tuple[int, int]],
            not_important_obj_list: list[tuple[int, int]], id_to_image_paths: dict, subset: str, img_name: str) -> None:
    """Generates an image with obj_count objects

    :param important_obj_list: list with tuples identifying an image_path of an important object in id_to_image_paths and its size
    :type important_obj_list: list[tuple[int, int, str]
    :param not_important_obj_list: list with tuples identifying an image_path of a not important object in id_to_image_paths and its size
    :type not_important_obj_list: list[tuple[int, int, str]]
    :param id_to_image_paths: mapping from image_id to image paths
    :type id_to_image_paths: dict
    :param subset: image subset, either "train", "val" or "test"
    :type subset: str
    :param img_name: name of the output file
    :type img_name: str
    """
    bg_imgs_path = "perception/processed_bg_images"
    all_bg_images = os.listdir(bg_imgs_path)
    with Image.open(f"{bg_imgs_path}/{choose_random_in_array(all_bg_images)}") as image:
        positions = []
        for tupl in not_important_obj_list:
            paste_object_into_image(tupl, image, id_to_image_paths)
        
        # I need to change this if IMPORTANT_OBJ_COUNT_PER_IMAGE is ever not 8
        zone_width = SCREEN_SIZE["width"]//4
        zone_height = SCREEN_SIZE["height"]//2
        assert len(important_obj_list) == 8
        for i, tupl in enumerate(important_obj_list):
            bb_list = paste_object_into_image(tupl, 
                image, 
                id_to_image_paths, 
                ((i%4)*zone_width, (i//4)*zone_height, (i%4 + 1)*zone_width, (i//4 + 1)*zone_height))
            if len(bb_list) == 1:
                bb_final = bb_list[0]
            else:
                bb_final = [min([x[0] for x in bb_list]),
                            min([x[1] for x in bb_list]),
                            max([x[2] for x in bb_list]),
                            max([x[3] for x in bb_list])]
            if bb_final[0] < 0:
                bb_final[0] = 0
            if bb_final[1] < 0:
                bb_final[1] = 0
            if bb_final[2] > SCREEN_SIZE["width"]-1:
                bb_final[2] = SCREEN_SIZE["width"]-1
            if bb_final[3] > SCREEN_SIZE["height"]-1:
                bb_final[3] = SCREEN_SIZE["height"]-1
            positions.append(((bb_final[0]+bb_final[2])//2, (bb_final[1]+bb_final[3])//2, bb_final[2]-bb_final[0], bb_final[3]-bb_final[1]))
        
        # resizing to reduce size in disk
        image = image.resize((640, 640))
        image.save(f"perception/generated_images/{subset}/images/{img_name}")
        with open(f"perception/generated_images/{subset}/labels/{img_name.split('.')[0]}.txt", "w") as text_file:
            for tupl, p in zip(important_obj_list, positions):
                yolo_id = yolo_id_converter.actual_to_yolo_id(tupl[0])
                assert p[0]/SCREEN_SIZE['width'] >= 0 and p[0]/SCREEN_SIZE['width'] <= 1
                assert p[1]/SCREEN_SIZE['height'] >= 0 and p[1]/SCREEN_SIZE['height'] <= 1
                assert p[0]/SCREEN_SIZE['width']+p[2]/SCREEN_SIZE['width']/2 >= 0 and p[0]/SCREEN_SIZE['width']+p[2]/SCREEN_SIZE['width']/2 <= 1
                assert p[1]/SCREEN_SIZE['height']+p[3]/SCREEN_SIZE['height']/2 >= 0 and p[1]/SCREEN_SIZE['height']+p[3]/SCREEN_SIZE['height']/2 <= 1
                text_file.write(f"{yolo_id} {p[0]/SCREEN_SIZE['width']} {p[1]/SCREEN_SIZE['height']} {p[2]/SCREEN_SIZE['width']} {p[3]/SCREEN_SIZE['height']}\n")



