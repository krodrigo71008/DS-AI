import time
from multiprocessing import Process, Queue, Value
import os
import pickle
import math

import keyboard
import numpy as np

from action.Action import Action
from control.Control import Control
from decisionMaking.DecisionMaking import DecisionMaking
from modeling.Modeling import Modeling
from modeling.constants import BASE_CONTROL_DT
from perception.Perception import Perception
from perception.SegmentationModel import SegmentationModel
from utility.DebugScreen import DebugScreen
from utility.Clock import ClockRecorder
from utility.Point2d import Point2d

MAX_TIMEOUT_TIME = 600

def vision_main_recorder(detected_objects_queue: Queue, should_start: Value, should_stop: Value, 
                         q: Queue = None):
    perception = Perception(debug=q is not None, queue=q)
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
    detected_objects_queue.cancel_join_thread()
    if q is not None:
        q.cancel_join_thread()
    print("Vision done")
    

def segmentation_main_recorder(segmentation_results_queue: Queue, should_start: Value, should_stop: Value, 
                               q: Queue = None):
    seg_model = SegmentationModel(debug=q is not None, queue=q)
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

    segmentation_results_queue.cancel_join_thread()
    if q is not None:
        q.cancel_join_thread()
    print("Segmentation done")

def control_main_recorder(detected_objects_queue: Queue, segmentation_queue: Queue, should_start: Value, 
                          should_stop: Value, trajectory: list[Point2d], output_folder : str,
                          landmarks: list[Point2d], q: Queue = None):
    clock = ClockRecorder()
    action = Action(debug=q is not None)
    control = Control(debug=q is not None)
    decision_making = DecisionMaking(debug=q is not None)
    modeling = Modeling(debug=q is not None, clock=clock)
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
    xEst_list = []
    PEst_list = []
    player_position_gt_list = []
    # this isn't really gt, but we'll pretend it is
    player_position_gt = np.array([[2, 2]], dtype=np.float32).T
    player_position_gt_list.append([player_position_gt[0, 0], player_position_gt[1, 0]])
    walking_segment_start = None
    direction_index = 0
    just_changed = False
    last_time = None
    times_ = []
    modeling_clock_times = []
    times_for_performance = []
    while should_stop.value == 0 and time.time() - start < MAX_TIMEOUT_TIME:
        time_start = time.time_ns()
        t1 = time.time_ns()
        q1 = modeling.update_model(detected_objects_queue, segmentation_queue)
        t2 = time.time_ns()
        q2 = decision_making.decide(modeling)
        t3 = time.time_ns()
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
        t4 = time.time_ns()
        action.act(control)
        t5 = time.time_ns()

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
        
        # save xEst and PEst
        xEst_list.append(modeling.xEst.copy())
        PEst_list.append(modeling.PEst.copy())

        if q is not None and q.empty():
            try:
                q.put(("control_info", q1, q2, q3))
            except ValueError:
                print("control debug_queue closed")

        t6 = time.time_ns()
        times_for_performance.append([t2-t1, t3-t2, t4-t3, t5-t4, t6-t5])

        time_end = time.time_ns()
        dt_ = time_end - time_start
        sleep_amount = BASE_CONTROL_DT - dt_/1e9
        if sleep_amount > 0:
            time.sleep(sleep_amount)
    
    detected_objects_queue.cancel_join_thread()
    segmentation_queue.cancel_join_thread()
    if q is not None:
        q.cancel_join_thread()

    is_debug = q is not None
    if is_debug:
        slam_predict_times = modeling.dt_record
        np.save(f"{output_folder}/slam_predict_times__{str(modeling.slam.Q[0, 0])}__{str(modeling.slam.Q[1, 1])}__{str(is_debug)}.npy", slam_predict_times)
        np.save(f"{output_folder}/all_split_times__{str(modeling.slam.Q[0, 0])}__{str(modeling.slam.Q[1, 1])}__{str(is_debug)}.npy", times_for_performance)

    with open(f"{output_folder}/state_estimate__{str(modeling.slam.Q[0, 0])}__{str(modeling.slam.Q[1, 1])}__{str(is_debug)}.pkl", "wb") as file:
        pickle.dump(xEst_list, file)
    with open(f"{output_folder}/covariance_estimate__{str(modeling.slam.Q[0, 0])}__{str(modeling.slam.Q[1, 1])}__{str(is_debug)}.pkl", "wb") as file:
        pickle.dump(PEst_list, file)
    np.save(f"{output_folder}/landmark_positions.npy", np.array([[p.x1, p.x2] for p in landmarks]))
    np.save(f"{output_folder}/player_positions_gt__{str(modeling.slam.Q[0, 0])}__{str(modeling.slam.Q[1, 1])}__{str(is_debug)}.npy", player_position_gt_list)
    np.save(f"{output_folder}/control_thread_times__{str(modeling.slam.Q[0, 0])}__{str(modeling.slam.Q[1, 1])}__{str(is_debug)}.npy", times_)
    np.save(f"{output_folder}/modeling_clock_times__{str(modeling.slam.Q[0, 0])}__{str(modeling.slam.Q[1, 1])}__{str(is_debug)}.npy", modeling_clock_times)

    print(f"Average time per control loop: {np.array(times_).mean():.3f}")

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
    output_folder = "slam_calibration"
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
    os.makedirs(output_folder, exist_ok=True)
    debug = True
    if debug:
        should_start = Value('b', 0)
        should_stop = Value('b', 0)
        detected_objects_queue = Queue()
        segmentation_queue = Queue()
        debug_screen = DebugScreen()
        vision_process = Process(target=vision_main_recorder, 
                                 args=(detected_objects_queue, should_start, should_stop, 
                                       debug_screen.vision_debug_queue))
        vision_process.start()
        segmentation_process = Process(target=segmentation_main_recorder, 
                                       args=(segmentation_queue, should_start, should_stop, 
                                             debug_screen.segmentation_debug_queue))
        segmentation_process.start()
        control_process = Process(target=control_main_recorder, 
                                  args=(detected_objects_queue, segmentation_queue, should_start, should_stop, 
                                        trajectory, output_folder, landmarks, debug_screen.control_debug_queue))
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
        vision_process = Process(target=vision_main_recorder, args=(detected_objects_queue, should_start, should_stop))
        vision_process.start()
        segmentation_process = Process(target=segmentation_main_recorder, 
                                       args=(segmentation_queue, should_start, should_stop))
        segmentation_process.start()
        control_process = Process(target=control_main_recorder, args=(detected_objects_queue, segmentation_queue, should_start, should_stop, 
                                                                      trajectory, output_folder, landmarks))
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
