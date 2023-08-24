import time
from multiprocessing import Process, Queue, Value
import queue

import keyboard

from action.Action import Action
from control.Control import Control
from decisionMaking.DecisionMaking import DecisionMaking
from modeling.Modeling import Modeling
from perception.Perception import Perception
from utility.TimeRecorder import TimeRecorder
from utility.DebugScreen import DebugScreen


def vision_main(detected_objects_queue: Queue, should_start: Value, should_stop: Value, q: Queue = None):
    perception = Perception(debug=q is not None, queue=q)
    while should_start.value == 0:
        pass
    start = time.time()
    while should_stop.value == 0 and time.time() - start < 60:
        timestamp = time.time()
        objects = perception.perceive()[0]
        detected_objects_queue.put((objects, timestamp))

def control_main(detected_objects_queue: Queue, should_start: Value, should_stop: Value, q: Queue = None):
    action = Action()
    control = Control(debug=q is not None)
    decision_making = DecisionMaking(debug=q is not None)
    modeling = Modeling(debug=q is not None)
    while should_start.value == 0:
        pass
    start = time.time()
    # wait for YOLO to initialize, only start doing stuff after we receive information
    while detected_objects_queue.empty():
        pass
    while should_stop.value == 0 and time.time() - start < 60:
        q1 = modeling.update_model(detected_objects_queue)
        q2 = decision_making.decide(modeling)
        q3 = control.control(decision_making, modeling)
        action.act(control)
        if q.empty():
            q.put(("control_info", q1, q2, q3))
    

if __name__ == "__main__":
    debug = True
    if debug:
        should_start = Value('b', 0)
        should_stop = Value('b', 0)
        detected_objects_queue = Queue()
        debug_screen = DebugScreen()
        vision_process = Process(target=vision_main, args=(detected_objects_queue, should_start, should_stop, debug_screen.vision_debug_queue))
        vision_process.start()
        control_process = Process(target=control_main, args=(detected_objects_queue, should_start, should_stop, debug_screen.control_debug_queue))
        control_process.start()
        start = time.time()
        while time.time() - start < 60:
            if keyboard.is_pressed("p"):
                should_start.value = 1
            elif keyboard.is_pressed("l"):
                should_stop.value = 1
            debug_screen.update()
    else:
        should_start = Value('b', 0)
        should_stop = Value('b', 0)
        detected_objects_queue = queue.Queue()
        vision_process = Process(target=vision_main, args=(detected_objects_queue, should_start, should_stop))
        vision_process.start()
        control_process = Process(target=control_main, args=(detected_objects_queue, should_start, should_stop))
        control_process.start()
        start = time.time()
        while time.time() - start < 60:
            if keyboard.is_pressed("p"):
                should_start.value = 1
            elif keyboard.is_pressed("l"):
                should_stop.value = 1
