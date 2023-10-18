import time
import glob
import os

import numpy as np

from modeling.Modeling import Modeling
from perception.Perception import Perception
from perception.SegmentationModel import SegmentationRecorder
from utility.Clock import ClockMock
from utility.Visualizer import Visualizer


if __name__ == "__main__":
    folder_name = f"records/trajectory_2__3"
    os.makedirs(f"{folder_name}/output", exist_ok=True)

    perception = Perception()
    timestamp_files = glob.glob(f"{folder_name}/*_vision_times.npy")
    assert len(timestamp_files) == 1
    vision_timestamps = np.load(timestamp_files[0])
    vision_index = -1

    seg_model = SegmentationRecorder()
    timestamp_files = glob.glob(f"{folder_name}/*_segmentation_times.npy")
    assert len(timestamp_files) == 1
    seg_timestamps = np.load(timestamp_files[0])
    seg_index = -1

    direction_files = glob.glob(f"{folder_name}/*_modeling_direction_changes.npy")
    assert len(direction_files) == 1
    direction_timestamps_files = glob.glob(f"{folder_name}/*_modeling_direction_changes_timestamps.npy")
    assert len(direction_timestamps_files) == 1
    direction_changes = np.load(direction_files[0], allow_pickle=True)
    direction_changes_timestamps = np.load(direction_timestamps_files[0])
    direction_index = 0

    timestamp_files = glob.glob(f"{folder_name}/*_modeling_clock_times.npy")
    assert len(timestamp_files) == 1
    clock_timestamps = np.load(timestamp_files[0])
    clock = ClockMock(clock_timestamps)
    modeling = Modeling(clock=clock, debug=True)

    vis_screen = Visualizer()

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
            vis_screen.update_yolo_image(vision_screenshot)
            vis_screen.draw_detected_objects(classes, scores, boxes)
        else:
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
            vis_screen.update_segmentation_image(seg_screenshot)
            vis_screen.draw_segmentation_results(segmentation_results)
        else:
            vis_screen.redraw_segmentation_results()
        
        modeling.received_segmentation_info = has_new_segmentation_image
        if has_new_segmentation_image:
            modeling.latest_segmentation_info = segmentation_results
            modeling.latest_segmentation_timestamp = seg_timestamp
        
        modeling.update_model_using_info(detected_objects, segmentation_results)
        # first float is timestamp, second is direction
        while direction_index < len(direction_changes_timestamps) and clock.raw_timestamp() == direction_changes_timestamps[direction_index]:
            print(f"Direction: {modeling.player_model.direction} to {direction_changes[direction_index]}")
            modeling.player_model.set_direction(direction_changes[direction_index])
            direction_index += 1

        if has_new_segmentation_image:
            vis_screen.draw_world_model_image(modeling.world_model.latest_debug_image)
        else:
            vis_screen.redraw_world_model_image()

        vis_screen.update_world_model(modeling)
        vis_screen.draw_estimation_errors(modeling.world_model.estimation_errors)
        vis_screen.draw_time(clock.time())
        vis_screen.export_results(f"{folder_name}/output/{clock.current_time_index - 2}.jpg")
        
print("Done")

# import time
# import pickle
# import glob

# import numpy as np
# from PIL import Image

# from control.Control import Control
# from decisionMaking.DecisionMaking import DecisionMaking
# from modeling.Modeling import Modeling
# from perception.Perception import Perception
# from utility.Visualizer import Visualizer
# from utility.Clock import ClockMock


# def try_out_modeling_with_recorded_inputs():
#     LIMIT_IMAGES = 5000
#     route_start = 0
#     with open(f"records/time_records_{route_start}.pkl", 'rb') as file:
#         time_records = pickle.load(file)
    
#     with open(f"records/orders_{route_start}.pkl", 'rb') as file:
#         orders = pickle.load(file)

#     clock_mock = ClockMock(initial_last_time=time_records[0])
#     clock_mock.times_to_return = time_records
#     control = Control(clock=clock_mock)
#     decision_making = DecisionMaking()
#     modeling = Modeling(clock=clock_mock)
#     perception = Perception()
#     vis_screen = Visualizer()
    
#     files = glob.glob('records/start_*.jpg')
#     files_sort_aux = []
#     for f in files:
#         files_sort_aux.append((int(f.split("\\")[-1].split("_")[-1].split(".")[0]), f))
#     files_sort_aux.sort()
#     sorted_files = [f[1] for f in files_sort_aux]
    
#     i = 0
#     for file, order in zip(sorted_files, orders):
#         with Image.open(file) as raw_image:
#             img = np.asarray(raw_image)
#             objects, classes, scores, boxes = perception.perceive(np.asarray(img))
#             vis_screen.update_image(img[:, :, ::-1])
#             vis_screen.draw_detected_objects(classes, scores, boxes)
#             modeling.update_model(objects)
#             vis_screen.update_world_model(modeling)
#             vis_screen.draw_estimation_errors(modeling.world_model.estimation_errors)
#             decision_making.decide(modeling)
#             decision_making.secondary_action = order
#             control.control(decision_making, modeling)
#             file_path_final = file.split('\\')[-1]
#             vis_screen.export_results(f"tests/test_results/test_modeling_with_recorded/{file_path_final}")
#             # print(f"{time.time() - start_time:.2f}: {modeling.player_model.position}, go_to {route[route_index]}, keys {control.key_action}")
#         i += 1
#         if i == LIMIT_IMAGES:
#             break

#     print("end")