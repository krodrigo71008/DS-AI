import time
from multiprocessing import Process, Queue, Value
import os

import keyboard
import numpy as np

from action.Action import Action
from control.Control import Control
from decisionMaking.DecisionMaking import DecisionMaking
from modeling.Modeling import Modeling
from utility.DebugScreen import DebugScreen
from utility.Clock import Clock
from utility.Point2d import Point2d

MAX_TIMEOUT_TIME = 600

def control_main_recorder(detected_objects_queue: Queue, segmentation_queue: Queue, should_start: Value, 
                          should_stop: Value, trajectory: dict[str, list[Point2d]], q: Queue = None):
    clock = Clock()
    action = Action(debug=q is not None)
    control = Control(debug=q is not None)
    decision_making = DecisionMaking(debug=q is not None)
    modeling = Modeling(debug=q is not None, clock=clock)
    print("Control ready")
    while should_start.value == 0:
        pass
    start = time.time()
    clock.start()
    i = 0
    idle_start = None
    while should_stop.value == 0 and time.time() - start < MAX_TIMEOUT_TIME:
        q1 = modeling.update_model(detected_objects_queue, segmentation_queue)
        q2 = decision_making.decide(modeling)
        decision_making.secondary_action = ("go_precisely_to", trajectory[i])
        q2 = (decision_making.primary_action, decision_making.secondary_action)
        q3 = control.control(decision_making, modeling)
        if control.key_action is None:
            if idle_start is None:
                idle_start = time.time()
            else:
                if time.time() - idle_start > 2.0: # if we've been idle for more than 2 seconds, go to next step
                    print(f"estimated player position: {modeling.player_position()}")
                    i += 1
                    idle_start = None
        else:
            idle_start = None
        action.act(control)
        if q is not None and q.empty():
            try:
                q.put(("control_info", q1, q2, q3))
            except ValueError:
                print("control debug_queue closed")
        if i >= len(trajectory):
            should_stop.value = 1
            print("Stopping")
            break
    
    detected_objects_queue.cancel_join_thread()
    segmentation_queue.cancel_join_thread()
    if q is not None:
        q.cancel_join_thread()
    print("Control done")
    

if __name__ == "__main__":
    all_trajectories = {}
    with open("records/trajectories.csv", "r") as trajectory_file:
        lines = trajectory_file.readlines()
        for i, line in enumerate(lines):
            if i == 0:
                continue
            parts = [t.strip() for t in line.split(";")]
            name = parts[0]
            trajectory = parts[1]
            assert trajectory[0] == '[' and trajectory[-1] == ']'
            trajectory = trajectory[1:-1].split("|")
            for p in trajectory:
                assert p[0] == '(' and p[-1] == ')'
                assert len(p.split(",")) == 2
            trajectory = [p[1:-1].split(",") for p in trajectory]
            trajectory = [Point2d(int(p[0].strip()), int(p[1].strip())) for p in trajectory]
            all_trajectories[name] = trajectory
    trajectory_choice = "zigzag"
    trajectory = all_trajectories[trajectory_choice]
    debug = True
    if debug:
        should_start = Value('b', 0)
        should_stop = Value('b', 0)
        detected_objects_queue = Queue()
        segmentation_queue = Queue()
        debug_screen = DebugScreen()
        control_process = Process(target=control_main_recorder, 
                                  args=(detected_objects_queue, segmentation_queue, should_start, should_stop, 
                                        trajectory, debug_screen.control_debug_queue))
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
        control_process = Process(target=control_main_recorder, args=(detected_objects_queue, segmentation_queue, should_start, should_stop, 
                                                                      trajectory))
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

    control_process.join()


# import time
# import pickle

# import keyboard
# from PIL import Image

# from action.Action import Action
# from control.Control import Control
# from decisionMaking.DecisionMaking import DecisionMaking
# from modeling.Modeling import Modeling
# from perception.Perception import PerceptionRecorder
# from utility.Clock import ClockRecorder
# from utility.Point2d import Point2d


# if __name__ == '__main__':
#     dir_options = [(1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)]
#     scales = [1, 1, 2, 2, 5, 5]

#     # route_start should be in [0, 7] (closed)
#     route_start = 0
#     route = []
#     route_index = route_start
#     current_point = Point2d(0, 0)
#     while len(route) < len(dir_options)*len(scales):
#         dpoint = dir_options[route_index % len(dir_options)]
#         dpoint = Point2d(dpoint[0], dpoint[1])
#         # make dpoint have length 6*scale since character moves at 6/s
#         dpoint = dpoint/dpoint.distance(Point2d(0, 0))*6*scales[route_index//len(dir_options)]
#         route_index += 1
#         current_point += dpoint
#         route.append(current_point)

#     BASE_SECONDS_PER_ROUTE_STEP = 1.5
#     helper = []
#     for s in scales:
#         helper.extend([s]*len(dir_options))
#     time_aux = 0
#     time_to_index_aux = []
#     for h in helper:
#         time_aux += h*BASE_SECONDS_PER_ROUTE_STEP
#         time_to_index_aux.append(time_aux)
    
#     while not keyboard.is_pressed("p"):
#         pass
#     clock_rec = ClockRecorder()
#     action = Action()
#     control = Control(clock=clock_rec)
#     decision_making = DecisionMaking()
#     modeling = Modeling(clock=clock_rec)
#     perception = PerceptionRecorder()
#     time.sleep(0.1)
#     start_time = time.time()
#     route_index = 0
#     orders = []
#     # press p again to end the program
#     while not keyboard.is_pressed("p"):
#         objects = perception.perceive()[0]
#         modeling.update_model(objects)
#         decision_making.decide(modeling)
#         cur_time = time.time() - start_time
#         if cur_time > time_to_index_aux[route_index]:
#             route_index += 1
#             if route_index >= len(time_to_index_aux):
#                 break
#         decision_making.secondary_action = ("go_precisely_to", route[route_index])
#         orders.append(("go_precisely_to", route[route_index]))
#         control.control(decision_making, modeling)
#         # print(f"{time.time() - start_time:.2f}: {modeling.player_position()}, go_to {route[route_index]}, keys {control.key_action}")
#         action.act(control)
    
#     for i, cap_img in enumerate(perception.all_captured_images):
#         img = Image.fromarray(cap_img, mode="RGB")
#         img.save(f"records/start_{route_start}_{i}.jpg")
    
#     with open(f"records/time_records_{route_start}.pkl", 'wb') as file:
#         pickle.dump(clock_rec.time_records, file)
    
#     with open(f"records/orders_{route_start}.pkl", 'wb') as file:
#         pickle.dump(orders, file)
#     print("end")