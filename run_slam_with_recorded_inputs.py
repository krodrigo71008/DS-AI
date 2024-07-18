import os

import numpy as np
import pandas as pd

from modeling.Modeling import Modeling, ModelingTimer
from modeling.ObjectsInfo import objects_info
from perception.Perception import Perception, PerceptionTimer
from perception.SegmentationModel import SegmentationModel, SegmentationTimer
from utility.Clock import ClockMock
from utility.Visualizer import Visualizer
from utility.Point2d import Point2d


def calculate_expected_observations(landmarks : list[Point2d], player_position : Point2d, modeling : Modeling):
    expected_z = []
    expected_conv_z = []
    for landmark in landmarks:
        relative_pos = landmark - player_position
        observation = modeling.world_model.H_function(relative_pos.x1, relative_pos.x2)
        expected_z.append(Point2d(observation[0], observation[1]))
        expected_conv_z.append(Point2d(relative_pos.x1, relative_pos.x2))
    return (expected_z, expected_conv_z)

if __name__ == "__main__":
    folder_name = f"slam_records"
    should_measure_time = False
    should_export_images = False
    os.makedirs(f"{folder_name}/output", exist_ok=True)

    # player initial position -52, -292
    landmarks = [
        Point2d(2, -8), # -52 -302 sapling
        Point2d(14, 2), # -40 -292 sapling
        Point2d(22, 22), # -32 -272 sapling
        Point2d(1, 42), # -53 -252 sapling
        Point2d(7, 32), # -47 -262 sapling
        Point2d(-1, -1), # -55 -295 grass
        Point2d(16, 4), # -38 -290 grass
        Point2d(12, 15), # -42 -279 grass
        Point2d(32, -18), # -22 -312 grass
        Point2d(28, 31), # -26 -261 grass
    ]

    if should_measure_time:
        perception = PerceptionTimer()
    else:
        perception = Perception()
    vision_timestamps = np.load(f"{folder_name}/vision_times.npy")
    vision_index = -1

    if should_measure_time:
        seg_model = SegmentationTimer()
    else:
        seg_model = SegmentationModel()
    seg_timestamps = np.load(f"{folder_name}/segmentation_times.npy")
    seg_index = -1

    direction_changes = np.load(f"{folder_name}/modeling_direction_changes.npy", allow_pickle=True)
    direction_changes_timestamps = np.load(f"{folder_name}/modeling_direction_changes_timestamps.npy")
    direction_index = 0

    clock_timestamps = np.load(f"{folder_name}/modeling_clock_times.npy")
    clock = ClockMock(clock_timestamps)

    if should_measure_time:
        modeling = ModelingTimer(clock=clock, debug=True)
    else:
        modeling = Modeling(clock=clock, debug=True)

    vis_screen = Visualizer()

    all_max_min_z_dists = []
    all_max_min_conv_z_dists = []

    while True:
        print(f"{clock.current_time_index}/{len(clock.times_to_return)}")
        next_time = clock.next_time()
        if next_time is None:
            break

        has_new_vision_image = False
        while vision_index + 1 < len(vision_timestamps) and vision_timestamps[vision_index+1] < next_time:
            vision_index += 1
            has_new_vision_image = True
        detected_objects = None
        if has_new_vision_image:
            vision_timestamp = vision_timestamps[vision_index]
            vision_screenshot = np.load(f"{folder_name}/vision_{vision_index}.npy")
            detected_objects, classes, scores, boxes = perception.perceive(vision_screenshot)
            if should_export_images:
                vis_screen.update_yolo_image(vision_screenshot)
                vis_screen.draw_detected_objects(classes, scores, boxes)
        else:
            if should_export_images:
                vis_screen.redraw_detected_objects()
        
        modeling.received_yolo_info = has_new_vision_image
        if has_new_vision_image:
            modeling.latest_detected_objects = detected_objects
            modeling.latest_yolo_timestamp = vision_timestamp

        has_new_segmentation_image = False
        while seg_index + 1 < len(seg_timestamps) and seg_timestamps[seg_index+1] < next_time:
            seg_index += 1
            has_new_segmentation_image = True
        segmentation_results = None
        if has_new_segmentation_image:
            seg_timestamp = seg_timestamps[seg_index]
            seg_screenshot = np.load(f"{folder_name}/segmentation_{seg_index}.npy")
            segmentation_results = seg_model.perceive(seg_screenshot)
            if should_export_images:
                vis_screen.update_segmentation_image(seg_screenshot)
                vis_screen.draw_segmentation_results(segmentation_results)
        else:
            if should_export_images:
                vis_screen.redraw_segmentation_results()
        
        modeling.received_segmentation_info = has_new_segmentation_image
        if has_new_segmentation_image:
            modeling.latest_segmentation_info = segmentation_results
            modeling.latest_segmentation_timestamp = seg_timestamp
        
        modeling.update_model_using_info(detected_objects, segmentation_results)

        # compare expected observations with observations
        expected_z, expected_conv_z = calculate_expected_observations(landmarks, modeling.player_position(), modeling)
        observed_z = modeling.latest_observations
        observed_conv_z = modeling.latest_conv_observations
        max_min_dist = None
        for i in range(len(observed_z)//2):
            obs_z = Point2d(observed_z[i*2], observed_z[i*2+1])
            min_dist = None
            nearest_point = None
            for expected_point in expected_z:
                dist = obs_z.distance(expected_point)
                if min_dist is None or dist < min_dist:
                    min_dist = dist
                    nearest_point = expected_point
            if max_min_dist is None or min_dist > max_min_dist:
                max_min_dist = min_dist
        all_max_min_z_dists.append(max_min_dist)
        
        max_min_dist = None
        for i in range(len(observed_conv_z)//2):
            obs_conv_z = Point2d(observed_conv_z[i*2], observed_conv_z[i*2+1])
            min_dist = None
            nearest_point = None
            for expected_point in expected_conv_z:
                dist = obs_conv_z.distance(expected_point)
                if min_dist is None or dist < min_dist:
                    min_dist = dist
                    nearest_point = expected_point
            if max_min_dist is None or min_dist > max_min_dist:
                max_min_dist = min_dist
        all_max_min_conv_z_dists.append(max_min_dist)

        if detected_objects is not None:
            for obj in detected_objects:
                assert obj in modeling.latest_image_objs or objects_info.get_item_info(image_id=obj.id, info="object_type") != "OBJECT"

        new_obj_count = len(modeling.latest_new_objects)
        for i, (image_object, slam_state_index, lm_id) in enumerate(modeling.latest_new_objects):
            assert slam_state_index == 2+lm_id*2
            assert slam_state_index == modeling.xEst_size_at_time_of_new_object_creation - new_obj_count*2 + i*2


        # first float is timestamp, second is direction
        while direction_index < len(direction_changes_timestamps) and clock.raw_timestamp() == direction_changes_timestamps[direction_index]:
            print(f"Direction: {modeling._direction} to {direction_changes[direction_index]}")
            modeling.set_direction(direction_changes[direction_index])
            direction_index += 1

        if should_export_images:
            if has_new_segmentation_image:
                vis_screen.draw_world_model_image(modeling.world_model.latest_debug_image)
            else:
                vis_screen.redraw_world_model_image()

            vis_screen.update_world_model(modeling)
            vis_screen.draw_time(clock.time())

            if has_new_vision_image or has_new_segmentation_image:
                vis_screen.export_results(f"{folder_name}/output/{clock.current_time_index - 2}.jpg")
            else:
                vis_screen.reset()

    if should_measure_time:
        # save perception time records
        perception_df = pd.DataFrame(perception.time_records, columns=perception.split_names)
        perception_df.to_csv("times/perception.csv", index=False)

        # save segmentation time records
        segmentation_df = pd.DataFrame(seg_model.time_records, columns=seg_model.split_names)
        segmentation_df.to_csv("times/segmentation.csv", index=False)

        # save modeling time records
        modeling_df = pd.DataFrame(modeling.time_records, columns=modeling.split_names)
        modeling_df.to_csv("times/modeling.csv", index=False)

        # save player model time records
        player_model_df = pd.DataFrame({'update': modeling.player_model.time_records})
        player_model_df.to_csv("times/player_model.csv", index=False)

        # save world model time records
        types = [p[0] for p in modeling.world_model.time_records_list]
        times = [p[1] for p in modeling.world_model.time_records_list]
        world_model_df = pd.DataFrame({'type': types, 'time': times})
        world_model_df.to_csv("times/world_model.csv", index=False)
        
    print("Done")
