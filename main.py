import time
from multiprocessing import Process, Queue, Value
import os

import keyboard
import pandas as pd
import numpy as np

from action.Action import Action, ActionTimer
from control.Control import Control, ControlTimer
from decisionMaking.DecisionMaking import DecisionMaking, DecisionMakingTimer
from modeling.Modeling import Modeling, ModelingTimer
from modeling.constants import BASE_CONTROL_DT
from perception.Perception import PerceptionRecorder, PerceptionTimer
from perception.SegmentationModel import SegmentationRecorder, SegmentationTimer
from utility.DebugScreen import DebugScreen
from utility.Clock import ClockRecorder


MAX_TIMEOUT_TIME = 120

def vision_main(detected_objects_queue: Queue, should_start, should_stop, 
                q: Queue = None, should_record_times : bool = False):
    if should_record_times:
        perception = PerceptionTimer(debug=q is not None, queue=q)
    else:
        perception = PerceptionRecorder(debug=q is not None, queue=q)
    print("Perception ready")
    while should_start.value == 0:
        pass
    vision_timestamps = []
    start = time.time()
    while should_stop.value == 0 and time.time() - start < MAX_TIMEOUT_TIME:
        timestamp = time.time()
        vision_timestamps.append(timestamp)
        objects, _, _, _, diff = perception.perceive()
        try:
            detected_objects_queue.put((objects, diff, timestamp))
        except ValueError:
            print("detected_objects_queue closed")

    if should_record_times:
        # save perception time records
        perception_df = pd.DataFrame(perception.time_records, columns=perception.split_names)
        perception_df.to_csv("times/perception.csv", index=False)

    if q is not None and not should_record_times:
        np.save("new_records/vision_times.npy", vision_timestamps, allow_pickle=False)
        for i, cap_img in enumerate(perception.all_captured_images):
            np.save(f"new_records/vision_{i}.npy", cap_img, allow_pickle=False)

    detected_objects_queue.cancel_join_thread()
    if q is not None:
        q.cancel_join_thread()
    print("Perception done")

def segmentation_main(segmentation_results_queue: Queue, should_start, should_stop, 
                      q: Queue = None, should_record_times : bool = False):
    if should_record_times:
        seg_model = SegmentationTimer(debug=q is not None, queue=q)
    else:
        seg_model = SegmentationRecorder(debug=q is not None, queue=q)
    print("Segmentation ready")
    while should_start.value == 0:
        pass
    segmentation_timestamps = []
    start = time.time()
    while should_stop.value == 0 and time.time() - start < MAX_TIMEOUT_TIME:
        timestamp = time.time()
        segmentation_timestamps.append(timestamp)
        results = seg_model.perceive()
        try:
            segmentation_results_queue.put((results, timestamp))
        except ValueError:
            print("segmentation_results_queue closed")

    if should_record_times:
        # save segmentation time records
        segmentation_df = pd.DataFrame(seg_model.time_records, columns=seg_model.split_names)
        segmentation_df.to_csv("times/segmentation.csv", index=False)

    if q is not None and not should_record_times:
        np.save("new_records/segmentation_times.npy", segmentation_timestamps, allow_pickle=False)
        for i, cap_img in enumerate(seg_model.all_captured_images):
            np.save(f"new_records/segmentation_{i}.npy", cap_img, allow_pickle=False)

    segmentation_results_queue.cancel_join_thread()
    if q is not None:
        q.cancel_join_thread()
    print("Segmentation done")

def control_main(detected_objects_queue: Queue, segmentation_queue: Queue, should_start, should_stop, 
                 q: Queue = None, should_record_times : bool = False):
    if should_record_times:
        action = ActionTimer(debug=q is not None)
        control = ControlTimer(debug=q is not None)
        decision_making = DecisionMakingTimer(debug=q is not None)
        modeling = ModelingTimer(debug=q is not None)
    else:
        action = Action(debug=q is not None)
        control_clock = ClockRecorder()
        control = Control(debug=q is not None, clock=control_clock)
        decision_making = DecisionMaking(debug=q is not None)
        modeling_clock = ClockRecorder()
        modeling = Modeling(debug=q is not None, clock=modeling_clock)
    print("Control ready")
    while should_start.value == 0:
        pass
    start = time.time()
    modeling.clock.start()
    control.clock.start()
    dts = []
    # wait for YOLO to initialize, only start doing stuff after we receive information
    while detected_objects_queue.empty():
        pass
    while should_stop.value == 0 and time.time() - start < MAX_TIMEOUT_TIME:
        time_start = time.time_ns()
        q1 = modeling.update_model(detected_objects_queue, segmentation_queue)
        q2 = decision_making.decide(modeling)
        q3 = control.control(decision_making, modeling)
        action.act(control)
        # we only put new info in the debug queue if the previous one was processed
        if q is not None and q.empty():
            try:
                q.put(("control_info", q1, q2, q3))
            except ValueError:
                print("control debug_queue closed")
        time_end = time.time_ns()
        dt_ = time_end - time_start
        dts.append(dt_)
        sleep_amount = BASE_CONTROL_DT - dt_/1e9
        if sleep_amount > 0:
            time.sleep(sleep_amount)

    if should_record_times:
        # save modeling time records
        modeling_df = pd.DataFrame(modeling.time_records, columns=modeling.split_names)
        modeling_df.to_csv("times/modeling.csv", index=False)

        # save modeling slam time records
        modeling_slam_df = pd.DataFrame(modeling.slam_dts, columns=["slam_dt"])
        modeling_slam_df.to_csv("times/modeling_slam_dts.csv", index=False)

        # save player model time records
        player_model_df = pd.DataFrame({'update': modeling.player_model.time_records})
        player_model_df.to_csv("times/player_model.csv", index=False)

        # save world model time records
        types = [p[0] for p in modeling.world_model.time_records_list]
        times = [p[1] for p in modeling.world_model.time_records_list]
        world_model_df = pd.DataFrame({'type': types, 'time': times})
        world_model_df.to_csv("times/world_model.csv", index=False)

        # save decision_making time records
        decision_making_df = pd.DataFrame(decision_making.time_records, columns=decision_making.split_names)
        decision_making_df.to_csv("times/decision_making.csv", index=False)

        # save control time records
        types = [p[0] for p in control.time_records_list]
        times = [p[1] for p in control.time_records_list]
        control_df = pd.DataFrame({'type': types, 'time': times})
        control_df.to_csv("times/control.csv", index=False)

        # save action time records
        action_df = pd.DataFrame({'act': action.time_records})
        action_df.to_csv("times/action.csv", index=False)
    
    detected_objects_queue.cancel_join_thread()
    segmentation_queue.cancel_join_thread()
    if q is not None and not should_record_times:
        q.cancel_join_thread()
        assert len(modeling_clock.time_records) == len(modeling.which_info_was_received_list) + 2
        np.save(f"new_records/modeling_clock_times.npy", modeling_clock.time_records, allow_pickle=False)
        np.save(f"new_records/modeling_received_infos.npy", modeling.which_info_was_received_list, allow_pickle=False)
        np.save(f"new_records/control_clock_times.npy", control_clock.time_records, allow_pickle=False)

    # save action time records
    dt_df = pd.DataFrame({'dt': dts})
    dt_df.to_csv("times/control_thread.csv", index=False)

    # with open("pests/results.pkl", "wb") as pest_file:
    #     pickle.dump(modeling.pests, pest_file)

    print("Control done")
    

if __name__ == "__main__":
    debug = True
    should_record_times = False
    if debug:
        os.makedirs("new_records", exist_ok=True)
        should_start = Value('b', 0)
        should_stop = Value('b', 0)
        detected_objects_queue = Queue()
        segmentation_queue = Queue()
        debug_screen = DebugScreen()
        vision_process = Process(target=vision_main, 
                                 args=(detected_objects_queue, should_start, should_stop, 
                                       debug_screen.vision_debug_queue, should_record_times))
        vision_process.start()
        segmentation_process = Process(target=segmentation_main, 
                                       args=(segmentation_queue, should_start, should_stop, 
                                             debug_screen.segmentation_debug_queue, should_record_times))
        segmentation_process.start()
        control_process = Process(target=control_main, 
                                  args=(detected_objects_queue, segmentation_queue, should_start, should_stop, 
                                        debug_screen.control_debug_queue, should_record_times))
        control_process.start()
        start = time.time()
        while time.time() - start < MAX_TIMEOUT_TIME:
            if keyboard.is_pressed("p"):
                should_start.value = 1
                start = time.time()
            elif keyboard.is_pressed("l"):
                should_stop.value = 1
            debug_screen.update()
        should_stop.value = 1
        debug_screen.close()
        detected_objects_queue.close()
        segmentation_queue.close()
    else:
        should_start = Value('b', 0)
        should_stop = Value('b', 0)
        detected_objects_queue = Queue()
        segmentation_queue = Queue()
        vision_process = Process(target=vision_main, args=(detected_objects_queue, should_start, should_stop, 
                                                           None, should_record_times))
        vision_process.start()
        segmentation_process = Process(target=segmentation_main, 
                                       args=(segmentation_queue, should_start, should_stop, 
                                             None, should_record_times))
        segmentation_process.start()
        control_process = Process(target=control_main, args=(detected_objects_queue, segmentation_queue, should_start, should_stop, 
                                                             None, should_record_times))
        control_process.start()
        start = time.time()
        while time.time() - start < MAX_TIMEOUT_TIME:
            if keyboard.is_pressed("p"):
                should_start.value = 1
            elif keyboard.is_pressed("l"):
                should_stop.value = 1
        should_stop.value = 1

        detected_objects_queue.close()
        segmentation_queue.close()
    
    vision_process.join()
    segmentation_process.join()
    control_process.join()
