import time
from multiprocessing import Process, Queue, Value
import os
import math

import keyboard
import numpy as np

from action.Action import Action
from control.Control import Control
from decisionMaking.DecisionMaking import DecisionMaking
from modeling.Modeling import ModelingRecorder
from modeling.constants import BASE_CONTROL_DT
from perception.Perception import PerceptionRecorder
from perception.SegmentationModel import SegmentationRecorder
from utility.DebugScreen import DebugScreen
from utility.Clock import ClockRecorder
from utility.Point2d import Point2d

MAX_TIMEOUT_TIME = 600

def vision_main_recorder(detected_objects_queue: Queue, should_start: Value, should_stop: Value, 
                         folder_name : str, q: Queue = None):
    perception = PerceptionRecorder(debug=q is not None, queue=q)
    vision_timestamps = []
    print("Vision ready")
    while should_start.value == 0:
        pass
    start = time.time()
    while should_stop.value == 0 and time.time() - start < MAX_TIMEOUT_TIME:
        timestamp = time.time()
        vision_timestamps.append(timestamp)
        objects = perception.perceive()[0]
        try:
            detected_objects_queue.put((objects, timestamp))
        except ValueError:
            print("detected_objects_queue closed")
    np.save(f"{folder_name}/vision_times.npy", vision_timestamps, allow_pickle=False)
    for i, cap_img in enumerate(perception.all_captured_images):
        np.save(f"{folder_name}/vision_{i}.npy", cap_img, allow_pickle=False)

    detected_objects_queue.cancel_join_thread()
    if q is not None:
        q.cancel_join_thread()
    print("Vision done")
    

def segmentation_main_recorder(segmentation_results_queue: Queue, should_start: Value, should_stop: Value, 
                               folder_name: str, q: Queue = None):
    seg_model = SegmentationRecorder(debug=q is not None, queue=q)
    seg_timestamps = []
    print("Segmentation ready")
    while should_start.value == 0:
        pass
    start = time.time()
    while should_stop.value == 0 and time.time() - start < MAX_TIMEOUT_TIME:
        timestamp = time.time()
        seg_timestamps.append(timestamp)
        results = seg_model.perceive()
        try:
            segmentation_results_queue.put((results, timestamp))
        except ValueError:
            print("segmentation_results_queue closed")
    np.save(f"{folder_name}/segmentation_times.npy", seg_timestamps, allow_pickle=False)
    for i, cap_img in enumerate(seg_model.all_captured_images):
        np.save(f"{folder_name}/segmentation_{i}.npy", cap_img, allow_pickle=False)

    segmentation_results_queue.cancel_join_thread()
    if q is not None:
        q.cancel_join_thread()
    print("Segmentation done")

def control_main_recorder(detected_objects_queue: Queue, segmentation_queue: Queue, should_start: Value, 
                          should_stop: Value, folder_name : str, trajectory: list[Point2d], q: Queue = None):
    clock = ClockRecorder()
    action = Action(debug=q is not None)
    control = Control(debug=q is not None)
    decision_making = DecisionMaking(debug=q is not None)
    modeling = ModelingRecorder(debug=q is not None, clock=clock) # we want to record modeling's clock times to be able to reproduce them later
    walking_segment_start = None
    direction_index = 0
    just_changed = False
    last_time = None
    player_position_gt_list = []
    player_position_gt = np.array([[2, 2]], dtype=np.float32).T
    player_position_gt_list.append([player_position_gt[0, 0], player_position_gt[1, 0]])
    times_ = []
    modeling_clock_times = []
    directions = []
    turn_times = []
    for i in range(len(trajectory)):
        if i == 0:
            continue
        directions.append((trajectory[i] - trajectory[i-1]).angle())
        turn_times.append(trajectory[i].distance(trajectory[i-1])/modeling.DEFAULT_SPEED)
    assert len(directions) == len(turn_times)
    print("Control ready")
    while should_start.value == 0:
        pass
    start = time.time()
    clock.start()
    # wait for YOLO to initialize, only start doing stuff after we receive information
    while detected_objects_queue.empty():
        pass
    i = 0
    while should_stop.value == 0 and time.time() - start < MAX_TIMEOUT_TIME:
        time_start = time.time_ns()
        q1 = modeling.update_model(detected_objects_queue, segmentation_queue)
        q2 = decision_making.decide(modeling)
        if (walking_segment_start is not None) and (time.time() - walking_segment_start >= turn_times[direction_index]):
            direction_index += 1
            just_changed = True
            if direction_index >= len(directions):
                should_stop.value = 1
                print("Stopping")
                control.key_action = None
                action.act(control)
                break
        decision_making.secondary_action = ("run", directions[direction_index])
        q2 = (decision_making.primary_action, decision_making.secondary_action)
        q3 = control.control(decision_making, modeling)
        action.act(control)
        if just_changed:
            direction = directions[direction_index-1]
        else:
            direction = directions[direction_index]

        if last_time is not None:
            u = np.array([[modeling.DEFAULT_SPEED*math.cos(direction), modeling.DEFAULT_SPEED*math.sin(direction)]]).T
            t_ = time.time() - last_time
            player_position_gt += u*t_
            times_.append(t_)
            modeling_clock_times.append(modeling.clock.dt())
            player_position_gt_list.append([player_position_gt[0, 0], player_position_gt[1, 0]])
        last_time = time.time()

        if walking_segment_start is None or just_changed:
            walking_segment_start = time.time()
            just_changed = False

        if q is not None and q.empty():
            try:
                q.put(("control_info", q1, q2, q3))
            except ValueError:
                print("control debug_queue closed")

        time_end = time.time_ns()
        dt_ = time_end - time_start
        sleep_amount = BASE_CONTROL_DT - dt_/1e9
        if sleep_amount > 0:
            time.sleep(sleep_amount)

        if i >= len(trajectory):
            should_stop.value = 1
            print("Stopping")
            break

    np.save(f"{folder_name}/modeling_clock_times.npy", clock.time_records, allow_pickle=False)
    np.save(f"{folder_name}/modeling_direction_changes.npy", 
            modeling.all_direction_changes)
    np.save(f"{folder_name}/modeling_direction_changes_timestamps.npy", 
            modeling.all_direction_changes_timestamps, allow_pickle=False)
    
    detected_objects_queue.cancel_join_thread()
    segmentation_queue.cancel_join_thread()
    if q is not None:
        q.cancel_join_thread()
    print("Control done")
    

if __name__ == "__main__":
    trajectory = [
        Point2d(2, 2),
        Point2d(32, 2),
        Point2d(32, 32),
        Point2d(2, 32),
        Point2d(2, 2),
        Point2d(32, 2),
        Point2d(32, 32),
        Point2d(2, 32),
        Point2d(2, 2),
    ]
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
    folder_name = "slam_records"
    # i is just used to create different names for folders with same trajectory
    os.makedirs(folder_name, exist_ok=True)
    debug = True
    if debug:
        should_start = Value('b', 0)
        should_stop = Value('b', 0)
        detected_objects_queue = Queue()
        segmentation_queue = Queue()
        debug_screen = DebugScreen()
        vision_process = Process(target=vision_main_recorder, 
                                 args=(detected_objects_queue, should_start, should_stop, 
                                       folder_name, debug_screen.vision_debug_queue))
        vision_process.start()
        segmentation_process = Process(target=segmentation_main_recorder, 
                                       args=(segmentation_queue, should_start, should_stop, 
                                             folder_name, debug_screen.segmentation_debug_queue))
        segmentation_process.start()
        control_process = Process(target=control_main_recorder, 
                                  args=(detected_objects_queue, segmentation_queue, should_start, should_stop, 
                                        folder_name, trajectory, debug_screen.control_debug_queue))
        control_process.start()
        start = time.time()
        while time.time() - start < MAX_TIMEOUT_TIME and should_stop.value == 0:
            if keyboard.is_pressed("p"):
                should_start.value = 1
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
        vision_process = Process(target=vision_main_recorder, args=(detected_objects_queue, should_start, should_stop, 
                                                                    folder_name))
        vision_process.start()
        segmentation_process = Process(target=segmentation_main_recorder, 
                                       args=(segmentation_queue, should_start, should_stop, 
                                             folder_name))
        segmentation_process.start()
        control_process = Process(target=control_main_recorder, args=(detected_objects_queue, segmentation_queue, should_start, should_stop, 
                                                                      folder_name, trajectory))
        control_process.start()
        start = time.time()
        while time.time() - start < MAX_TIMEOUT_TIME and should_stop.value == 0:
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
