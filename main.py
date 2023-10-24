import time
from multiprocessing import Process, Queue, Value

import keyboard
import pandas as pd

from action.Action import Action
from control.Control import Control
from decisionMaking.DecisionMaking import DecisionMaking
from modeling.Modeling import Modeling
from perception.Perception import Perception
from perception.SegmentationModel import SegmentationModel
from utility.DebugScreen import DebugScreen


MAX_TIMEOUT_TIME = 60

def vision_main(detected_objects_queue: Queue, should_start: Value, should_stop: Value, 
                q: Queue = None, should_record_times : bool = False):
    perception = Perception(debug=q is not None, queue=q, measure_time=should_record_times)
    print("Perception ready")
    while should_start.value == 0:
        pass
    start = time.time()
    while should_stop.value == 0 and time.time() - start < MAX_TIMEOUT_TIME:
        timestamp = time.time()
        objects = perception.perceive()[0]
        try:
            detected_objects_queue.put((objects, timestamp))
        except ValueError:
            print("detected_objects_queue closed")

    if should_record_times:
        # save perception time records
        perception_df = pd.DataFrame(perception.time_records, columns=perception.split_names)
        perception_df.to_csv("times/perception.csv", index=False)

    detected_objects_queue.cancel_join_thread()
    if q is not None:
        q.cancel_join_thread()
    print("Perception done")

def segmentation_main(segmentation_results_queue: Queue, should_start: Value, should_stop: Value, 
                      q: Queue = None, should_record_times : bool = False):
    seg_model = SegmentationModel(debug=q is not None, queue=q, measure_time=should_record_times)
    print("Segmentation ready")
    while should_start.value == 0:
        pass
    start = time.time()
    while should_stop.value == 0 and time.time() - start < MAX_TIMEOUT_TIME:
        timestamp = time.time()
        results = seg_model.perceive()
        try:
            segmentation_results_queue.put((results, timestamp))
        except ValueError:
            print("segmentation_results_queue closed")

    if should_record_times:
        # save segmentation time records
        segmentation_df = pd.DataFrame(seg_model.time_records, columns=seg_model.split_names)
        segmentation_df.to_csv("times/segmentation.csv", index=False)

    segmentation_results_queue.cancel_join_thread()
    if q is not None:
        q.cancel_join_thread()
    print("Segmentation done")

def control_main(detected_objects_queue: Queue, segmentation_queue: Queue, should_start: Value, should_stop: Value, 
                 q: Queue = None, should_record_times : bool = False):
    action = Action(debug=q is not None, measure_time=should_record_times)
    control = Control(debug=q is not None, measure_time=should_record_times)
    decision_making = DecisionMaking(debug=q is not None, measure_time=should_record_times)
    modeling = Modeling(debug=q is not None, measure_time=should_record_times)
    print("Control ready")
    while should_start.value == 0:
        pass
    start = time.time()
    modeling.clock.start()
    control.clock.start()
    # wait for YOLO to initialize, only start doing stuff after we receive information
    while detected_objects_queue.empty():
        pass
    while should_stop.value == 0 and time.time() - start < MAX_TIMEOUT_TIME:
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

    if should_record_times:
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
    if q is not None:
        q.cancel_join_thread()
    print("Control done")
    

if __name__ == "__main__":
    debug = True
    should_record_times = True
    if debug:
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
