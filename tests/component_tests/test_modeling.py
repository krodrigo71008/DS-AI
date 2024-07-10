import math
import random

import numpy as np
import pytest
from PIL import Image

from modeling.objects.Grass import GRASS_HARVESTED, GRASS_READY, Grass
from modeling.objects.Sapling import SAPLING_HARVESTED, SAPLING_READY, Sapling
from modeling.Modeling import Modeling
from modeling.PlayerModel import PlayerModel
from modeling.WorldModel import WorldModel
from modeling.constants import CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV, FOLLOW_HEIGHT
from modeling.constants import DISTANCE_FOR_SAME_OBJECT, CHUNK_SIZE, CYCLES_TO_ADMIT_OBJECT, DISTANCE_FOR_VALID_PLAYER_POSITION
from modeling.Scheduler import SchedulerMock
from modeling.utility import image_to_local_position
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
    modeling = Modeling()
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
        modeling.set_player_position(positions[i])
        local_pos = bush_positions[i]
        answer = answers[i]
        player_pos = player_positions[i]
        modeling.world_model.decide_player_position([player_pos])
        modeling.world_model.start_cycle(positions[i], 0, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
        for lp, ans in zip(local_pos, answer):
            res = modeling.world_model.local_to_global_position(
                lp,
                0,
                CAMERA_PITCH,
                CAMERA_DISTANCE,
                FOV,
                FOLLOW_HEIGHT
            )
            results.append(res.distance(ans))
            assert res.distance(ans) < 1
        # this isn't really necessary, but I'll leave it here just to illustrate how the world model should be used
        modeling.world_model.finish_cycle()
    print(f"avg distance: {np.array(results).mean()}")
    results = []
    for i in range(11):
        # this simulates not detecting the player for many cycles
        modeling.world_model.finish_cycle()
    for i in range(5):
        modeling.set_player_position(positions[i])
        local_pos = bush_positions[i]
        answer = answers[i]
        player_pos = player_positions[i]
        modeling.world_model.start_cycle(positions[i], 0, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
        for lp, ans in zip(local_pos, answer):
            res = modeling.world_model.local_to_global_position(
                lp,
                0,
                CAMERA_PITCH,
                CAMERA_DISTANCE,
                FOV,
                FOLLOW_HEIGHT
            )
            results.append(res.distance(ans))
            assert res.distance(ans) < 3
        # this isn't really necessary, but I'll leave it here just to illustrate how the world model should be used
        modeling.world_model.finish_cycle()
    print(f"avg distance without detecting player: {np.array(results).mean()}")

def test_transformation_rotated():
    """This tests the transformation function by using some images as reference. The basic idea was:
    - Record a video walking around two bushes on known world coordinates
    - Extract some frames from the video
    - Annotate manually in which pixels the bushes and player are
    - Transform those annotations to see if they match our known positions
    """
    modeling = Modeling()
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
        modeling.set_player_position(positions_rotated[i])
        local_pos = bush_positions[i]
        answer = answers_rotated[i]
        player_pos = player_positions[i]
        modeling.world_model.decide_player_position([player_pos])
        modeling.world_model.start_cycle(positions_rotated[i], CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
        for lp, ans in zip(local_pos, answer):
            res = modeling.world_model.local_to_global_position(
                lp,
                CAMERA_HEADING,
                CAMERA_PITCH,
                CAMERA_DISTANCE,
                FOV,
                FOLLOW_HEIGHT
            )
            results.append(res.distance(ans))
            assert res.distance(ans) < 1
        # this isn't really necessary, but I'll leave it here just to illustrate how the world model should be used
        modeling.world_model.finish_cycle()
    print(f"avg distance rotated: {np.array(results).mean()}")
    results = []
    for i in range(11):
        # this simulates not detecting the player for many cycles
        modeling.world_model.finish_cycle()
    for i in range(5):
        modeling.set_player_position(positions_rotated[i])
        local_pos = bush_positions[i]
        answer = answers_rotated[i]
        player_pos = player_positions[i]
        modeling.world_model.start_cycle(positions_rotated[i], 0, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
        for lp, ans in zip(local_pos, answer):
            res = modeling.world_model.local_to_global_position(
                lp,
                CAMERA_HEADING,
                CAMERA_PITCH,
                CAMERA_DISTANCE,
                FOV,
                FOLLOW_HEIGHT
            )
            results.append(res.distance(ans))
            assert res.distance(ans) < 3
    print(f"avg distance rotated: {np.array(results).mean()}")
        
def test_required_nearby_chunks():
    modeling = Modeling()
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
        res = modeling.world_model.required_nearby_chunks(test_case[0])
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
        modeling = Modeling()
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
        modeling = Modeling()
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
    modeling = Modeling()
    scheduler = SchedulerMock(Clock(), modeling.world_model)
    sap1 = Sapling(modeling, 0, Point2d(0, 0), SAPLING_READY, scheduler)
    sap2 = Sapling(modeling, 0, Point2d(0, 0), SAPLING_READY, scheduler)
    sap3 = Sapling(modeling, 0, Point2d(0, 0), SAPLING_READY, scheduler)
    sap4 = Sapling(modeling, 0, Point2d(0, 0), SAPLING_HARVESTED, scheduler)
    modeling.world_model.object_lists["Sapling"] = [sap1, sap2, sap3, sap4]
    gr1 = Grass(modeling, 0, Point2d(0, 0), GRASS_READY, scheduler)
    gr2 = Grass(modeling, 0, Point2d(0, 0), GRASS_READY, scheduler)
    gr3 = Grass(modeling, 0, Point2d(0, 0), GRASS_HARVESTED, scheduler)
    gr4 = Grass(modeling, 0, Point2d(0, 0), GRASS_HARVESTED, scheduler)
    modeling.world_model.object_lists["Grass"] = [gr1, gr2, gr3, gr4]
    results = modeling.world_model.get_all_of(["Grass", "Sapling"], "only_not_harvested")
    assert len(results["Grass"]) == 2
    assert len(results["Sapling"]) == 3

# def test_distance_for_same_object():
#     modeling = Modeling()
#     sapling_image = ImageObject(SAPLING_READY, 1, [SCREEN_SIZE["width"]//2, SCREEN_SIZE["height"]//2, SCREEN_SIZE["width"]*0.2, SCREEN_SIZE["height"]*0.2])
#     sapling = Sapling(modeling, 0, Point2d(0, 0), SAPLING_HARVESTED, modeling.world_model.scheduler)
#     modeling.world_model.add_object(sapling)

#     random.seed(727)
#     for _ in range(20):
#         angle = random.randint(0, 359)
#         pos = Point2d(DISTANCE_FOR_SAME_OBJECT, 0)
#         pos = pos.rotate_degrees(angle)
#         modeling.world_model.start_cycle()
#         modeling.world_model.handle_object_at_position(sapling_image, pos)
#         modeling.world_model.finish_cycle()
    
#     assert len(modeling.world_model.object_lists["Sapling"]) == 1
    
#     angle = random.randint(0, 359)
#     pos = Point2d(DISTANCE_FOR_SAME_OBJECT+0.1, 0)
#     pos = pos.rotate_degrees(angle)
#     for _ in range(CYCLES_TO_ADMIT_OBJECT):
#         modeling.world_model.start_cycle()
#         modeling.world_model.handle_object_at_position(sapling_image, pos)
#         modeling.world_model.finish_cycle()
    
#     assert len(modeling.world_model.object_lists["Sapling"]) == 2

def test_player_choice_algorithm():
    modeling = Modeling()

    random.seed(727)
    possible_positions = []
    for _ in range(20):
        angle = random.randint(0, 359)
        pos = Point2d(DISTANCE_FOR_VALID_PLAYER_POSITION+0.1, 0)
        pos = pos.rotate_degrees(angle) + Point2d(SCREEN_SIZE["width"]//2, SCREEN_SIZE["height"]//2)
        possible_positions.append(pos)

    modeling.world_model.decide_player_position(possible_positions)
    assert modeling.world_model.latest_detected_player_position is None
    
    modeling = Modeling()
    possible_positions = []
    best = None
    best_distance = None
    for _ in range(20):
        distance = random.random()*DISTANCE_FOR_VALID_PLAYER_POSITION
        angle = random.randint(0, 359)
        pos = Point2d(distance, 0)
        pos = pos.rotate_degrees(angle) + Point2d(SCREEN_SIZE["width"]//2, SCREEN_SIZE["height"]//2)
        if best_distance is None or distance < best_distance:
            best = pos
            best_distance = distance
        possible_positions.append(pos)
    
    modeling.world_model.decide_player_position(possible_positions)
    assert modeling.world_model.latest_detected_player_position == best

def try_out_warp_perspective(image_path: str):
    modeling = Modeling()
    world = modeling.world_model
    image = Image.open(image_path).resize((512, 512))
    res = world.warp_image_to_ground(np.asarray(image), CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
    Image.fromarray(res).save("warped_test.jpg")
    return res

def try_out_process_segmentation_image(segmentation_array: np.ndarray):
    modeling = Modeling()
    world = modeling.world_model
    world.process_segmentation_image(segmentation_array)


def test_jacobH():
    random.seed(727)
    for _ in range(20):
        x = random.random()*100 - 50
        z = random.random()*100 - 50
        aux_test_jacobH(x, z)

def aux_test_jacobH(x, z):
    modeling = Modeling()
    world = modeling.world_model
    m1 = world.jacobH(x, z)
    m2 = world.jacobH_numerical(x, z)
    assert abs(m1[0, 0] - m2[0, 0]) < 1e-6
    assert abs(m1[0, 1] - m2[0, 1]) < 1e-6
    assert abs(m1[1, 0] - m2[1, 0]) < 1e-6
    assert abs(m1[1, 1] - m2[1, 1]) < 1e-6
    
def test_inverseH():
    random.seed(727)
    for _ in range(20):
        u = random.random()*1920
        v = random.random()*1080
        aux_test_inverseH(u, v)

def aux_test_inverseH(u, v):
    modeling = Modeling()
    world = modeling.world_model
    eps = 1e-4
    xz1 = image_to_local_position(Point2d(u-eps, v))
    xz2 = image_to_local_position(Point2d(u+eps, v))
    xz3 = image_to_local_position(Point2d(u, v-eps))
    xz4 = image_to_local_position(Point2d(u, v+eps))
    x_u = (xz2.x1 - xz1.x1)/(2*eps)
    x_v = (xz4.x1 - xz3.x1)/(2*eps)
    z_u = (xz2.x2 - xz1.x2)/(2*eps)
    z_v = (xz4.x2 - xz3.x2)/(2*eps)
    m1 = np.array([
        [x_u, x_v],
        [z_u, z_v]
    ])
    m2 = world.jacob_inverseH(u, v)
    assert abs(m1[0, 0] - m2[0, 0]) < 1e-6
    assert abs(m1[0, 1] - m2[0, 1]) < 1e-6
    assert abs(m1[1, 0] - m2[1, 0]) < 1e-6
    assert abs(m1[1, 1] - m2[1, 1]) < 1e-6
    
def test_uv_model():
    modeling = Modeling()
    follow_height = modeling.world_model.FOLLOW_HEIGHT
    distance = CAMERA_DISTANCE
    fov = FOV
    heading = CAMERA_HEADING
    pitch = CAMERA_PITCH
    c_u = SCREEN_SIZE["width"]/2
    c_v = SCREEN_SIZE["height"]/2
    heading = heading*math.pi/180
    pitch = pitch*math.pi/180
    sin_heading = math.sin(heading)
    cos_heading = math.cos(heading)
    sin_pitch = math.sin(pitch)
    cos_pitch = math.cos(pitch)
    f = SCREEN_SIZE["height"]/(2*math.tan(fov/180*math.pi/2))
    random.seed(727)
    for _ in range(20):
        x = random.random()*100 - 50
        z = random.random()*100 - 50
        u, v = modeling.world_model.H_function(x, z)

        s = -cos_pitch*cos_heading*x-cos_pitch*sin_heading*z+distance+follow_height*sin_pitch
        m1 = np.array([[u, v, 1]]).T
        m2 = np.array([
            [f, 0, c_u],
            [0, f, c_v],
            [0, 0, 1]
        ])
        m3 = np.array([
            [-sin_heading, 0, cos_heading, 0],
            [sin_pitch*cos_heading, cos_pitch, sin_pitch*sin_heading, follow_height*cos_pitch],
            [-cos_pitch*cos_heading, sin_pitch, -cos_pitch*sin_heading, distance+follow_height*sin_pitch]
        ])
        m4 = np.array([[x, 0, z, 1]]).T
        eq1 = s*m1
        eq2 = m2 @ m3 @ m4

        diff = (eq1 - eq2)**2
        assert diff.sum() < 1e-6

def test_xy_model():
    follow_height = FOLLOW_HEIGHT
    distance = CAMERA_DISTANCE
    fov = FOV
    heading = CAMERA_HEADING
    pitch = CAMERA_PITCH
    c_u = SCREEN_SIZE["width"]/2
    c_v = SCREEN_SIZE["height"]/2
    heading = heading*math.pi/180
    pitch = pitch*math.pi/180
    sin_heading = math.sin(heading)
    cos_heading = math.cos(heading)
    sin_pitch = math.sin(pitch)
    cos_pitch = math.cos(pitch)
    f = SCREEN_SIZE["height"]/(2*math.tan(fov/180*math.pi/2))
    random.seed(727)
    for _ in range(20):
        u = int(random.random()*1920)
        v = int(random.random()*1080)
        xz_point = image_to_local_position(Point2d(u, v))
        x = xz_point.x1
        z = xz_point.x2

        s = f*(distance*sin_pitch + follow_height)/(cos_pitch*(v-c_v)+f*sin_pitch)
        m1 = np.array([[u, v, 1]]).T
        m2 = np.array([
            [f, 0, c_u],
            [0, f, c_v],
            [0, 0, 1]
        ])
        m3 = np.array([
            [-sin_heading, 0, cos_heading, 0],
            [sin_pitch*cos_heading, cos_pitch, sin_pitch*sin_heading, follow_height*cos_pitch],
            [-cos_pitch*cos_heading, sin_pitch, -cos_pitch*sin_heading, distance+follow_height*sin_pitch]
        ])
        m4 = np.array([[x, 0, z, 1]]).T
        eq1 = s*m1
        eq2 = m2 @ m3 @ m4

        diff = (eq1 - eq2)**2
        assert diff.sum() < 1e-6

def test_covariance_with_jacob_inverseH():
    random.seed(727)
    np.random.seed(727)
    temp = []
    for _ in range(20):
        u = random.random()*1920
        v = random.random()*1080
        mean_error = aux_test_covariance_with_jacob_inverseH(u, v)
        temp.append(mean_error)
    assert np.array(temp).mean() < 1e-1

def aux_test_covariance_with_jacob_inverseH(u, v):
    MAX_STD_U = 192
    MAX_STD_V = 108
    NUM_POINTS = 100000
    modeling = Modeling()
    world = modeling.world_model
    m = world.jacob_inverseH(u, v)
    # decide covariance in uv
    std_u = random.random()*MAX_STD_U
    std_v = random.random()*MAX_STD_V
    temp_list = [[], []]
    for _ in range(NUM_POINTS):
        # generate uv points with gaussian
        u_r = np.random.normal()*std_u + u
        v_r = np.random.normal()*std_v + v
        # convert them to xz
        xz = image_to_local_position(Point2d(u_r, v_r))
        x_r = xz.x1
        z_r = xz.x2
        temp_list[0].append(x_r)
        temp_list[1].append(z_r)
    # measure covariance on xz with numpy
    measured_cov = np.cov(temp_list)
    # compare it to the expected value using jacobian
    expected_cov = m @ np.diag([std_u**2, std_v**2]) @ m.T
    mean_error = np.abs((measured_cov - expected_cov)/expected_cov).mean()
    return mean_error


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
