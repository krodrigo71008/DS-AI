import math

import numpy as np
import pytest
from PIL import Image

from modeling.objects.Grass import GRASS_HARVESTED, GRASS_READY, Grass
from modeling.objects.Sapling import SAPLING_HARVESTED, SAPLING_READY, Sapling
from modeling.Modeling import Modeling
from modeling.PlayerModel import PlayerModel
from modeling.WorldModel import WorldModel
from modeling.constants import CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV, DISTANCE_FOR_SAME_OBJECT, CHUNK_SIZE
from modeling.Scheduler import SchedulerMock
from perception.constants import SCREEN_SIZE
from perception.YoloIdConverter import yolo_id_converter
from perception.ImageObject import ImageObject
from utility.Clock import Clock
from utility.Point2d import Point2d

def test_transformation():
    """This tests the transformation function by using some images as reference. The basic idea was:
    - Record a video walking around two bushes on known world coordinates
    - Extract some frames from the video
    - Annotate manually in which pixels the bushes and player are
    - Transform those annotations to see if they match our known positions
    """
    clock = Clock()
    player = PlayerModel(clock)
    world = WorldModel(player, clock)
    positions = [Point2d(0, 8.6), Point2d(0, 13.8), Point2d(6.4, 6.5), Point2d(16.0, 6.5), Point2d(-8.9, 6.5)]
    bush_positions = [
        [Point2d(558, 600), Point2d(1854, 600)],
        [Point2d(107, 600), Point2d(1394, 600)],
        [Point2d(630, 428), Point2d(1783, 428)],
        [Point2d(687, 175), Point2d(1645, 175)],
        [Point2d(512, 950)]
    ]
    player_positions = [
        Point2d(1043, 600),
        Point2d(868, 600),
        Point2d(960, 671),
        Point2d(960, 671),
        Point2d(960, 550)
    ]
    answers = [
        [Point2d(0, 0), Point2d(0, 23.2)],
        [Point2d(0, 0), Point2d(0, 23.2)],
        [Point2d(0, 0), Point2d(0, 23.2)],
        [Point2d(0, 0), Point2d(0, 23.2)],
        [Point2d(0, 0)]
    ]
    results = []
    for i in range(5):
        player.position = positions[i]
        local_pos = bush_positions[i]
        answer = answers[i]
        player_pos = player_positions[i]
        world.decide_player_position([player_pos])
        world.start_cycle(0, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
        for lp, ans in zip(local_pos, answer):
            res = world.local_to_global_position(
                lp,
                0,
                CAMERA_PITCH,
                CAMERA_DISTANCE,
                FOV
            )
            results.append(res.distance(ans))
            assert res.distance(ans) < 1
        # this isn't really necessary, but I'll leave it here just to illustrate how the world model should be used
        world.finish_cycle()
    print(f"avg distance: {np.array(results).mean()}")
    results = []
    for i in range(11):
        # this simulates not detecting the player for many cycles
        world.finish_cycle()
    for i in range(5):
        player.position = positions[i]
        local_pos = bush_positions[i]
        answer = answers[i]
        player_pos = player_positions[i]
        world.start_cycle(0, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
        for lp, ans in zip(local_pos, answer):
            res = world.local_to_global_position(
                lp,
                0,
                CAMERA_PITCH,
                CAMERA_DISTANCE,
                FOV
            )
            results.append(res.distance(ans))
            assert res.distance(ans) < 3
    print(f"avg distance: {np.array(results).mean()}")

def test_transformation_rotated():
    """This tests the transformation function by using some images as reference. The basic idea was:
    - Record a video walking around two bushes on known world coordinates
    - Extract some frames from the video
    - Annotate manually in which pixels the bushes and player are
    - Transform those annotations to see if they match our known positions
    """
    clock = Clock()
    player = PlayerModel(clock)
    world = WorldModel(player, clock)
    positions_old = [Point2d(0, 8.6), Point2d(0, 13.8), Point2d(6.4, 6.5), Point2d(16.0, 6.5), Point2d(-8.9, 6.5)]
    positions_rotated = [Point2d(p.x1*math.sin(math.pi/4)-p.x2*math.sin(math.pi/4),
                                    p.x1*math.sin(math.pi/4)+p.x2*math.sin(math.pi/4)) for p in positions_old]
    bush_positions = [
        [Point2d(558, 600), Point2d(1854, 600)],
        [Point2d(107, 600), Point2d(1394, 600)],
        [Point2d(630, 428), Point2d(1783, 428)],
        [Point2d(687, 175), Point2d(1645, 175)],
        [Point2d(512, 950)]
    ]
    player_positions = [
        Point2d(1043, 600),
        Point2d(868, 600),
        Point2d(960, 671),
        Point2d(960, 671),
        Point2d(960, 550)
    ]
    answers_old = [
        [Point2d(0, 0), Point2d(0, 23.2)],
        [Point2d(0, 0), Point2d(0, 23.2)],
        [Point2d(0, 0), Point2d(0, 23.2)],
        [Point2d(0, 0), Point2d(0, 23.2)],
        [Point2d(0, 0)]
    ]
    answers_rotated = []
    for aux_ in answers_old:
        aux_rotated = [Point2d(p.x1*math.sin(math.pi/4)-p.x2*math.sin(math.pi/4),
                                    p.x1*math.sin(math.pi/4)+p.x2*math.sin(math.pi/4)) for p in aux_]
        answers_rotated.append(aux_rotated)
    results = []
    for i in range(5):
        player.position = positions_rotated[i]
        local_pos = bush_positions[i]
        answer = answers_rotated[i]
        player_pos = player_positions[i]
        world.decide_player_position([player_pos])
        world.start_cycle(CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
        for lp, ans in zip(local_pos, answer):
            res = world.local_to_global_position(
                lp,
                CAMERA_HEADING,
                CAMERA_PITCH,
                CAMERA_DISTANCE,
                FOV
            )
            results.append(res.distance(ans))
            assert res.distance(ans) < 1
        # this isn't really necessary, but I'll leave it here just to illustrate how the world model should be used
        world.finish_cycle()
    print(f"avg distance rotated: {np.array(results).mean()}")
    results = []
    for i in range(11):
        # this simulates not detecting the player for many cycles
        world.finish_cycle()
    for i in range(5):
        player.position = positions_rotated[i]
        local_pos = bush_positions[i]
        answer = answers_rotated[i]
        player_pos = player_positions[i]
        world.start_cycle(0, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
        for lp, ans in zip(local_pos, answer):
            res = world.local_to_global_position(
                lp,
                CAMERA_HEADING,
                CAMERA_PITCH,
                CAMERA_DISTANCE,
                FOV
            )
            results.append(res.distance(ans))
            assert res.distance(ans) < 3
    print(f"avg distance rotated: {np.array(results).mean()}")
        
def test_required_nearby_chunks():
    clock = Clock()
    player = PlayerModel(clock)
    world = WorldModel(player, clock)
    test_cases = [
        (Point2d(0, 0), [(-1, -1), (-1, 0), (0, -1)]),
        (Point2d(CHUNK_SIZE, 0), [(0, -1), (0, 0), (1, -1)]),
        (Point2d(CHUNK_SIZE-0.01, 0), [(1, -1), (1, 0), (0, -1)]),
        (Point2d(CHUNK_SIZE-DISTANCE_FOR_SAME_OBJECT*0.9, DISTANCE_FOR_SAME_OBJECT*0.9), [(1, 0), (0, -1)]),
        (Point2d(CHUNK_SIZE-DISTANCE_FOR_SAME_OBJECT*0.7, DISTANCE_FOR_SAME_OBJECT*0.7), [(1, -1), (1, 0), (0, -1)]),
        (Point2d(DISTANCE_FOR_SAME_OBJECT*0.7, DISTANCE_FOR_SAME_OBJECT*0.7), [(-1, -1), (-1, 0), (0, -1)]),
        (Point2d(CHUNK_SIZE*10 + DISTANCE_FOR_SAME_OBJECT*0.7, DISTANCE_FOR_SAME_OBJECT*0.7), [(9, -1), (9, 0), (10, -1)]),
        (Point2d(DISTANCE_FOR_SAME_OBJECT*0.7, DISTANCE_FOR_SAME_OBJECT*0.7 - CHUNK_SIZE*6), [(-1, -7), (-1, -6), (0, -7)]),
        (Point2d(3*CHUNK_SIZE-DISTANCE_FOR_SAME_OBJECT*0.9, 2*CHUNK_SIZE - DISTANCE_FOR_SAME_OBJECT*0.9), [(3, 1), (2, 2)]),
        (Point2d(3*CHUNK_SIZE-DISTANCE_FOR_SAME_OBJECT*0.9, 2*CHUNK_SIZE - DISTANCE_FOR_SAME_OBJECT*0.1), [(3, 1), (2, 2), (3, 2)]),
    ]
    for test_case in test_cases:
        res = world.required_nearby_chunks(test_case[0])
        expected = test_case[1]
        assert sorted(res) == sorted(expected)

object_input_filter_test_cases = [
    ((1, 1, 1), True), 
    ((1, 1, 1, 1, 1, 1), True), 
    ((1, 1, 0), False), 
    ((1, 1, 0, 1, 1), False), 
    ((1, 0, 1, 1, 1), True), 
    ((1, 0, 1, 1, 0, 1, 1), False), 
    ((0, 1, 1, 1), True), 
    ((0, 0, 1, 1, 1), True), 
    ((0, 0, 1, 1, 1, 1, 1), True), 
    ((0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1), False), 
    ((0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0), False), 
]

@pytest.mark.parametrize("test_case", object_input_filter_test_cases)
def test_modeling_object_input_filtering(test_case):
    assert aux_modeling_object_input_filtering(test_case)

def aux_modeling_object_input_filtering(test_case):
    width = SCREEN_SIZE["width"]
    height = SCREEN_SIZE["height"]
    # reminder: bbs are center x, center y, width, height
    bounding_boxes = [(width*0.05, height*0.05, width*0.1, height*0.1), 
                        (width*0.3, height*0.15, width*0.1, height*0.1),
                        (width*0.15, height*0.3, width*0.1, height*0.2),
                        (width*0.45, height*0.5, width*0.7, height*0.6),
                        (width*0.1, height*0.35, width*0.2, height*0.5)]
    with open("perception/darknet/obj.names") as file:
        lines = [line.strip() for line in file.readlines()]
        grass_id = lines.index("grass")
        grass_id = yolo_id_converter.yolo_to_actual_id(grass_id)
    score = 1.0
    objects = [ImageObject(grass_id, score, bb) for bb in bounding_boxes]

    input_sequence, expected = test_case
    for obj in objects:
        modeling = Modeling(clock=Clock())
        for input_ in input_sequence:
            if input_ == 1:
                modeling.received_yolo_info = True
                modeling.received_segmentation_info = False
                modeling.update_model_using_info([obj], None)
            else:
                modeling.received_yolo_info = True
                modeling.received_segmentation_info = False
                modeling.update_model_using_info([], None)
        if len(modeling.world_model.object_lists) > 0 and not expected:
            return False
        elif len(modeling.world_model.object_lists) == 0 and expected:
            return False
    return True

object_deletion_test_cases = [
    ((0, 0, 0, 0, 0), False), 
    ((0, 0, 0, 0), True), 
    ((0, 0, 0, 1, 0, 0, 0), True), 
    ((0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0), True), 
    ((0, 0, 1, 0, 0, 0, 0, 0), False), 
    ((0, 0, 0, 0, 0, 0, 0, 0, 0), False), 
    ((0, 1, 0, 0, 0, 0, 0), False), 
    ((0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0), True), 
    ((0, 0, 1, 0, 0, 0, 0, 0), False), 
    ((0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0), True)
]

@pytest.mark.parametrize("test_case", object_deletion_test_cases)
def test_modeling_object_deletion(test_case):
    assert aux_modeling_object_deletion(test_case)

def aux_modeling_object_deletion(test_case):
    width = SCREEN_SIZE["width"]
    height = SCREEN_SIZE["height"]
    # reminder: bbs are center x, center y, width, height
    bounding_boxes = [(width*0.05, height*0.05, width*0.1, height*0.1), 
                        (width*0.3, height*0.15, width*0.1, height*0.1),
                        (width*0.15, height*0.3, width*0.1, height*0.2),
                        (width*0.45, height*0.5, width*0.7, height*0.6),
                        (width*0.1, height*0.35, width*0.2, height*0.5)]
    with open("perception/darknet/obj.names") as file:
        lines = [line.strip() for line in file.readlines()]
        grass_id = lines.index("grass")
        grass_id = yolo_id_converter.yolo_to_actual_id(grass_id)
    score = 1.0
    objects = [ImageObject(grass_id, score, bb) for bb in bounding_boxes]

    input_sequence, expected = test_case
    for i, obj in enumerate(objects):
        modeling = Modeling(clock=Clock())
        modeling.received_yolo_info = True
        modeling.received_segmentation_info = False
        # these three detections server to admit the object to the world model
        modeling.update_model_using_info([obj], None)
        modeling.update_model_using_info([obj], None)
        modeling.update_model_using_info([obj], None)
        for input_ in input_sequence:
            if input_ == 1:
                modeling.received_yolo_info = True
                modeling.received_segmentation_info = False
                modeling.update_model_using_info([obj], None)
            else:
                modeling.received_yolo_info = True
                modeling.received_segmentation_info = False
                modeling.update_model_using_info([], None)
        total_obj_list_len = 0
        for _, obj_list in modeling.world_model.object_lists.items():
            total_obj_list_len += len(obj_list)
        total_objs_by_chunk_len = 0
        for _, obj_list in modeling.world_model.objects_by_chunks.items():
            total_objs_by_chunk_len += len(obj_list)
        # i = 0 is the only case with the object too close to the edge of the screen 
        if i == 0:
            if total_obj_list_len == 0:
                return False
            if total_objs_by_chunk_len == 0:
                return False
        else:
            if total_obj_list_len > 0 and not expected:
                return False
            elif total_obj_list_len == 0 and expected:
                return False
            if total_objs_by_chunk_len > 0 and not expected:
                return False
            elif total_objs_by_chunk_len == 0 and expected:
                return False
    return True

def test_world_model_filtering():
    world_model = WorldModel(PlayerModel(Clock()), Clock())
    scheduler = SchedulerMock(Clock(), world_model)
    sap1 = Sapling(Point2d(0, 0), Point2d(0, 0), SAPLING_READY, scheduler)
    sap2 = Sapling(Point2d(0, 0), Point2d(0, 0), SAPLING_READY, scheduler)
    sap3 = Sapling(Point2d(0, 0), Point2d(0, 0), SAPLING_READY, scheduler)
    sap4 = Sapling(Point2d(0, 0), Point2d(0, 0), SAPLING_HARVESTED, scheduler)
    world_model.object_lists["Sapling"] = [sap1, sap2, sap3, sap4]
    gr1 = Grass(Point2d(0, 0), Point2d(0, 0), GRASS_READY, scheduler)
    gr2 = Grass(Point2d(0, 0), Point2d(0, 0), GRASS_READY, scheduler)
    gr3 = Grass(Point2d(0, 0), Point2d(0, 0), GRASS_HARVESTED, scheduler)
    gr4 = Grass(Point2d(0, 0), Point2d(0, 0), GRASS_HARVESTED, scheduler)
    world_model.object_lists["Grass"] = [gr1, gr2, gr3, gr4]
    results = world_model.get_all_of(["Grass", "Sapling"], "only_not_harvested")
    assert len(results["Grass"]) == 2
    assert len(results["Sapling"]) == 3

# start 32
# im1 = 119 -> 8.6 from left
# start back 294
# im2 = 388 -> 9.4 from right (13.8 from left)
# stop 461 -> 16.7 from right (6.5 from left)
# start down 461
# im3 525 -> 6.4 down
# im4 621 -> 16.0 down
# stop 621
# start up 623
# im5 872 -> 24.9 up from down -> 8.9 up
# 
# heading = 0 -> down +x  left +z
# bush1 -> 0,0
# bush2 -> 0,-23.2
# start -> 0,0
# im1 -> 0,-8.6
# im2 -> 0,-13.8
# im3 -> 6.4,-6.5
# im4 -> 16.0,-6.5
# im5 -> -8.9,-6.5
# bush_positions:
# im1 -> (558, 600), (1854, 600)
# im2 -> (107, 600), (1394, 600)
# im3 -> (630, 428), (1783, 428)
# im4 -> (687, 175), (1645, 175)
# im5 -> (512, 950)
# player_position:
# im1 -> (1043, 600)
# im2 -> (868, 600)
# im3 -> (960, 671)
# im4 -> (960, 671)
# im5 -> (960, 550)

def try_out_warp_perspective(image_path: str):
    clock = Clock()
    player = PlayerModel(clock)
    world = WorldModel(player, clock)
    image = Image.open(image_path).resize((512, 512))
    res = world.warp_image_to_ground(np.asarray(image), CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
    Image.fromarray(res).save("warped_test.jpg")
    return res

def try_out_process_segmentation_image(segmentation_array: np.array):
    clock = Clock()
    player = PlayerModel(clock)
    world = WorldModel(player, clock)
    world.process_segmentation_image(segmentation_array)
