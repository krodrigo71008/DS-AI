import math

import cv2

from modeling.Modeling import Modeling
from modeling.constants import CAMERA_HEADING
from perception.Perception import Perception
from utility.Clock import ClockMock
from utility.Visualizer import Visualizer
from utility.utility import clamp2pi


def run_perception_modeling_single_frame(input_image_path):
    perception = Perception()
    modeling = Modeling()
    img = cv2.imread(input_image_path)
    # converting img from BGR to RGB
    img = img[:, :, ::-1]
    objects = perception.perceive(img)[0]
    modeling.update_model(objects)

def run_perception_modeling_multiple_frames(input_image_paths, expected_results=None):
    RECORDED_FPS = 30
    # input_image_paths needs to be ordered, first image is the first to be feeded as input
    input_image_paths.sort()
    initial_number = int(input_image_paths[0].split("\\")[-1][:-4])
    image_times = [(int(path.split("\\")[-1][:-4]) - initial_number)/RECORDED_FPS for path in input_image_paths]
    folder_name = input_image_paths[0].split("\\")[-2]
    # last character is just a number (e.g. down1)
    movement_direction = folder_name[:-1]
    if movement_direction == "down":
        local_angle = 0
    elif movement_direction == "left":
        local_angle = -math.pi/2
    elif movement_direction == "up":
        local_angle = math.pi
    elif movement_direction == "right":
        local_angle = math.pi/2
    else:
        raise Exception("Invalid movement direction!")
    # for now, this clamp should be unnecessary, but 
    global_angle = clamp2pi(local_angle + CAMERA_HEADING*math.pi/180)

    clock = ClockMock()
    clock.times_to_return = image_times
    perception = Perception()
    modeling = Modeling(clock=clock)
    modeling.player_model.direction = global_angle
    vis_screen = Visualizer()

    for image_path in input_image_paths:
        img = cv2.imread(image_path)
        vis_screen.update_image(img)
        # converting img from BGR to RGB
        img = img[:, :, ::-1]
        objects, classes, scores, boxes = perception.perceive(img)
        vis_screen.draw_detected_objects(classes, scores, boxes)
        modeling.update_model(objects)
        corners = (modeling.world_model.c1, modeling.world_model.c2, modeling.world_model.c3, modeling.world_model.c4)
        vis_screen.update_world_model(modeling.world_model.object_lists, modeling.player_model, 
                                        corners, modeling.world_model.origin_coordinates,
                                        modeling.world_model.recent_objects, modeling.world_model.estimation_pairs)
        image_name = image_path.split("\\")[-1]
        vis_screen.export_results(f"tests/test_results/test_perception_modeling/{folder_name}_{image_name}")

