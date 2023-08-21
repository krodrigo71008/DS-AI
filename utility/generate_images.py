from random import randint, random, shuffle
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

def paste_object_into_image(dims: tuple[int, int], offsets: list[tuple[int, int]], paths: list[str], bg_image : Image.Image, 
        position : tuple[int, int] = None) -> list[list[int]]:
    """Pastes an object with dimensions dims, offsets, specified by paths, on the bg_image, in a random position unless
    specified by position

    :param dims: width and height
    :type dims: tuple[int, int]
    :param offsets: offsets to paste images with multiple sprites
    :type offsets: list[tuple[int, int]]
    :param paths: paths for the image to be pasted
    :type paths: list[str]
    :param bg_image: background image
    :type bg_image: Image.Image
    :param position: position, defaults to None
    :type position: tuple[int, int], optional
    :return: list with bounding boxes
    :rtype: list[list[int]]
    """
    width, height = dims
    # if position is None, select a position at random
    if position is None:
        # generate appropriate x and y
        # this lets 20% of the sprite to generate off the zone
        random_x = randint(int(-.2*width), int(SCREEN_SIZE["width"]-1-width*.8))
        random_y = randint(int(-.2*height), int(SCREEN_SIZE["height"]-1-height*.8))
    else:
        random_x = position[0]
        random_y = position[1]
    # while not check_validity((random_x, random_y), (width, height)):
    #     random_x = randint(int(-.2*width)+zone[0], int(zone[2]-1-width*.8))
    #     random_y = randint(int(-.2*height)+zone[1], int(zone[3]-1-height*.8))
    day_color = (255/255, 230/255, 158/255)
    dusk_color = (150/255, 150/255, 150/255)
    bb_list = []
    for i, chosen_img in enumerate(paths):
        with Image.open(chosen_img) as added_image:
            image_to_paste = added_image.resize((width, height))
            image_to_paste = np.array(image_to_paste)
            if randint(0, 1) == 0:
                image_to_paste[:, :, 0:3] = image_to_paste[:, :, 0:3] * np.array(day_color)
            else:
                image_to_paste[:, :, 0:3] = image_to_paste[:, :, 0:3] * np.array(dusk_color)
            image_to_paste = Image.fromarray(image_to_paste, mode="RGBA")
            # enhancer changes the bg_image's brightness
            enhancer = ImageEnhance.Brightness(image_to_paste)
            bg_image.paste(enhancer.enhance(random()*1.5+0.25), 
                (int(random_x+offsets[i][0]), int(random_y+offsets[i][1])), 
                image_to_paste)
            # random small offset error to introduce variance
            xy_error = (random()*image_to_paste.size[0]*0.06 - image_to_paste.size[0]*0.03, 
                        random()*image_to_paste.size[1]*0.06 - image_to_paste.size[1]*0.03)
            # random small scale error to introduce variance
            scale_error = (0.97+random()*0.06, 0.97+random()*0.06)

            x1 = int(random_x+offsets[i][0]+xy_error[0]+(1-scale_error[0])*image_to_paste.size[0]/2)
            y1 = int(random_y+offsets[i][1]+xy_error[1]+(1-scale_error[1])*image_to_paste.size[1]/2)
            x2 = int(random_x+offsets[i][0]+xy_error[0]+(scale_error[0]-1)*image_to_paste.size[0]/2) + image_to_paste.size[0]
            y2 = int(random_y+offsets[i][1]+xy_error[1]+(scale_error[1]-1)*image_to_paste.size[1]/2) + image_to_paste.size[1]
            bb_list.append([x1, y1, x2, y2])

    return bb_list

def get_dimensions_offsets_from_tuple(tupl: tuple[int, int, str], id_to_image_paths: dict) -> tuple[tuple[int, int], list[tuple[int, int]], int]:
    """Get (width, height) and offsets from object tuple

    :param tupl: tuple with image_id, index and image size
    :type tupl: tuple[int, int, str]
    :param id_to_image_paths: mapping from image_id to image paths
    :type id_to_image_paths: dict
    :return: (width, height) and offsets
    :rtype: tuple[tuple[int, int], list[tuple[int, int]]]
    """
    image_id, i, max_size_class = tupl
    width_list = []
    height_list = []
    path_str = id_to_image_paths[image_id][i]
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
    width = int(max(width_list)/scale_factor)
    height = int(max(height_list)/scale_factor)
    if len(paths) == 1:
        offsets = [(0, 0)]
    else:
        if paths[0].find("campfire") != -1:
            offsets = [((width_list[1]-width_list[0]+15)/2/scale_factor, (height_list[1] - height_list[0]*0.1-15)/scale_factor), (0, 0)]
        else:
            raise NotImplementedError("No offsets for everything that's not a campfire!")
    return (width, height), offsets

def decide_position_rejection(dims: tuple[int, int], pasted_positions: list[tuple[int, int, int, int]]) -> tuple[int, int, bool]:
    """Decide the position one object will be pasted in the image using rejection sampling

    :param dims: width and height of the sprite to be pasted
    :type dims: tuple[int, int]
    :param pasted_positions: x1, y1, x2, y2 of the leftuppermost and rightlowermost corners of previous pasted positions
    :type pasted_positions: list[tuple[int, int, int, int]]
    :return: position and whether the position is valid
    :rtype: tuple[int, int, bool]
    """
    MAX_NUM_ATTEMPTS = 10
    width, height = dims
    max_x = SCREEN_SIZE["width"] - width - 1
    max_y = SCREEN_SIZE["height"] - height - 1
    x = randint(0, max_x)
    y = randint(0, max_y)
    invalid_regions = [(pos[0] - width, pos[1] - height, pos[2], pos[3]) for pos in pasted_positions]
    attempt_number = 0
    def valid(x, y, invalid_regions) -> bool:
        return np.all(np.array([x < r[0] or y < r[1] or x > r[2] or y > r[3] for r in invalid_regions]))
    while not valid(x, y, invalid_regions) and attempt_number < MAX_NUM_ATTEMPTS:
        x = randint(0, max_x)
        y = randint(0, max_y)
        attempt_number += 1
    return x, y, attempt_number < MAX_NUM_ATTEMPTS


def generate_image(important_obj_list: list[tuple[int, int, str]], important_index: int,
            not_important_obj_list: list[tuple[int, int, str]], not_important_index: int, id_to_image_paths: dict, subset: str, img_name: str,
            important_objects_range: tuple[int, int], not_important_objects_range: tuple[int, int]) -> int:
    """Generates an image with obj_count objects

    :param important_obj_list: list with tuples identifying an image_path of an important object in id_to_image_paths and its size
    :type important_obj_list: list[tuple[int, int, str]
    :param important_index: current start index for important_obj_list
    :type important_index: int
    :param not_important_obj_list: list with tuples identifying an image_path of a not important object in id_to_image_paths and its size
    :type not_important_obj_list: list[tuple[int, int, str]]
    :param not_important_index: current start index for not_important_obj_list
    :type not_important_index: int
    :type not_important_obj_list: list[tuple[int, int, str]]
    :param id_to_image_paths: mapping from image_id to image paths
    :type id_to_image_paths: dict
    :param subset: image subset, either "train", "val" or "test"
    :type subset: str
    :param img_name: name of the output file
    :type img_name: str
    :param important_objects_range: range of important objects to put in a image
    :type important_objects_range: tuple[int, int]
    :param not_important_objects_range: range of non important objects to put in a image
    :type not_important_objects_range: tuple[int, int]
    :return: important_index and not_important_index for next iteration
    :rtype: tuple[int, int]
    """
    MAX_NOt_IMPORTANT_SCREEN_COVERAGE = 0.4
    bg_imgs_path = "perception/processed_bg_images"
    all_bg_images = os.listdir(bg_imgs_path)
    with Image.open(f"{bg_imgs_path}/{choose_random_in_array(all_bg_images)}") as image:
        positions = []
        not_important_object_count = randint(*not_important_objects_range)
        not_important_coverage = 0
        for i in range(not_important_object_count):
            dims, offsets = get_dimensions_offsets_from_tuple(not_important_obj_list[not_important_index], id_to_image_paths)
            image_id, index, _ = not_important_obj_list[not_important_index]
            path_str = id_to_image_paths[image_id][index]
            paths = path_str.split("+")
            paste_object_into_image(dims, offsets, paths, image)
            not_important_index = (not_important_index + 1) % len(not_important_obj_list)
            if not_important_index == 0:
                shuffle(not_important_obj_list)
            not_important_coverage += dims[0]*dims[1]/(SCREEN_SIZE["width"]*SCREEN_SIZE["height"])
            if not_important_coverage >= MAX_NOt_IMPORTANT_SCREEN_COVERAGE:
                break
        max_important_object_count = randint(*important_objects_range)
        important_object_count = 0
        pasted_positions = []
        while important_object_count < max_important_object_count:
            dims, offsets = get_dimensions_offsets_from_tuple(important_obj_list[important_index+important_object_count], id_to_image_paths)
            image_id, index, _ = important_obj_list[important_index+important_object_count]
            path_str = id_to_image_paths[image_id][index]
            paths = path_str.split("+")
            x, y, valid = decide_position_rejection(dims, pasted_positions)
            if valid:
                bb_list =  paste_object_into_image(dims, offsets, paths, image, (x, y))
            else:
                break
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
            pasted_positions.append(bb_final)
            positions.append(((bb_final[0]+bb_final[2])//2, (bb_final[1]+bb_final[3])//2, bb_final[2]-bb_final[0], bb_final[3]-bb_final[1]))
            important_object_count += 1
            if important_index+important_object_count >= len(important_obj_list):
                break
        
        # resizing to reduce size in disk
        image = image.resize((640, 640))
        image.save(f"perception/generated_images/{subset}/images/{img_name}")
        with open(f"perception/generated_images/{subset}/labels/{img_name.split('.')[0]}.txt", "w") as text_file:
            for tupl, p in zip(important_obj_list[important_index : important_index + important_object_count], positions):
                yolo_id = yolo_id_converter.actual_to_yolo_id(tupl[0])
                assert p[0]/SCREEN_SIZE['width'] >= 0 and p[0]/SCREEN_SIZE['width'] <= 1
                assert p[1]/SCREEN_SIZE['height'] >= 0 and p[1]/SCREEN_SIZE['height'] <= 1
                assert p[0]/SCREEN_SIZE['width']+p[2]/SCREEN_SIZE['width']/2 >= 0 and p[0]/SCREEN_SIZE['width']+p[2]/SCREEN_SIZE['width']/2 <= 1
                assert p[1]/SCREEN_SIZE['height']+p[3]/SCREEN_SIZE['height']/2 >= 0 and p[1]/SCREEN_SIZE['height']+p[3]/SCREEN_SIZE['height']/2 <= 1
                text_file.write(f"{yolo_id} {p[0]/SCREEN_SIZE['width']} {p[1]/SCREEN_SIZE['height']} {p[2]/SCREEN_SIZE['width']} {p[3]/SCREEN_SIZE['height']}\n")
    
    return important_index + important_object_count, not_important_index


