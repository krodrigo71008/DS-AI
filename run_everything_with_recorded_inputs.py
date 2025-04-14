import glob
import os

import numpy as np
import cv2

from modeling.Modeling import Modeling
from perception.Perception import Perception
from perception.SegmentationModel import SegmentationModel
from decisionMaking.DecisionMaking import DecisionMaking
from control.Control import Control
from utility.Clock import ClockMock


if __name__ == "__main__":
    folder_name = "new_records"
    os.makedirs(f"{folder_name}/output", exist_ok=True)

    perception = Perception()
    timestamp_files = glob.glob(f"{folder_name}/vision_times.npy")
    assert len(timestamp_files) == 1
    vision_timestamps = np.load(timestamp_files[0])
    vision_index = 0

    seg_model = SegmentationModel()
    timestamp_files = glob.glob(f"{folder_name}/segmentation_times.npy") 
    assert len(timestamp_files) == 1
    seg_timestamps = np.load(timestamp_files[0])
    seg_index = -1

    modeling_timestamp_files = glob.glob(f"{folder_name}/modeling_clock_times.npy")
    assert len(modeling_timestamp_files) == 1
    modeling_clock_timestamps = np.load(modeling_timestamp_files[0])
    modeling_clock = ClockMock(modeling_clock_timestamps)
    modeling = Modeling(clock=modeling_clock, debug=True)

    modeling_received_info_files = glob.glob(f"{folder_name}/modeling_received_infos.npy")
    assert len(modeling_received_info_files) == 1
    modeling_received_info_list = np.load(modeling_received_info_files[0])
    
    decision_making = DecisionMaking(debug=True)

    control_timestamp_files = glob.glob(f"{folder_name}/control_clock_times.npy")
    assert len(control_timestamp_files) == 1
    control_clock_timestamps = np.load(control_timestamp_files[0])
    control_clock = ClockMock(control_clock_timestamps)
    control = Control(clock=control_clock, debug=True)

    diff_averages = []

    aux = []
    aux_image = None
    for i in range(len(vision_timestamps)):
        img = np.load(f"{folder_name}/vision_{i+1}.npy")
        if aux_image is not None:
            aux.append(np.average(cv2.absdiff(img, aux_image)))
        aux_image = img


    while True:
        modeling_time_index = modeling_clock.current_time_index - 2
        print(f"{modeling_time_index}/{len(modeling_clock.times_to_return) - 2}")
        next_time = modeling_clock.next_time()
        if next_time is None:
            break

        vision_timestamp = modeling_received_info_list[modeling_time_index][0]
        received_new_vision_image = vision_timestamp != -1
        if not received_new_vision_image: # this mimics how modeling.handle_detected_objects_queue is structured
            detected_objects = modeling.latest_detected_objects
            modeling.received_yolo_info = False
        else:
            while vision_timestamps[vision_index] <= vision_timestamp:
                vision_screenshot = np.load(f"{folder_name}/vision_{vision_index}.npy")
                cv2.imwrite(f"{folder_name}/output/vision_{vision_index}.jpg", vision_screenshot)
                detected_objects, classes, scores, boxes, diff = perception.perceive(vision_screenshot)
                if diff is not None and modeling._record_image_diffs:
                    modeling.last_image_diffs.append(diff)
                vision_index += 1
            modeling.latest_yolo_timestamp = vision_timestamp
            if modeling.do_image_processing:
                modeling.received_yolo_info = True
                modeling.latest_detected_objects = detected_objects
            else:
                modeling.received_yolo_info = False

        seg_timestamp = modeling_received_info_list[modeling_time_index][1]
        received_new_segmentation_image = seg_timestamp != -1
        if not received_new_segmentation_image: # this mimics how modeling.handle_segmentation_queue is structured
            segmentation_results = modeling.latest_segmentation_info
            modeling.received_segmentation_info = False
        else:
            seg_index = np.nonzero(seg_timestamps == seg_timestamp)[0][0]
            seg_screenshot = np.load(f"{folder_name}/segmentation_{seg_index+1}.npy")
            cv2.imwrite(f"{folder_name}/output/segmentation_{seg_index}.jpg", vision_screenshot)
            segmentation_results = seg_model.perceive(seg_screenshot)
            modeling.latest_segmentation_timestamp = seg_timestamp
            if modeling.do_image_processing:
                modeling.received_segmentation_info = True
                modeling.latest_segmentation_info = segmentation_results
            else:
                modeling.received_segmentation_info = False
        
        modeling.update_model_using_info(detected_objects, segmentation_results)
        decision_making.decide(modeling)
        control.control(decision_making, modeling)

        
    print("Done")
