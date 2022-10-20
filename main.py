import time
import threading

import keyboard

from action.Action import Action
from control.Control import Control
from decisionMaking.DecisionMaking import DecisionMaking
from modeling.Modeling import Modeling
from perception.Perception import Perception
from utility.TimeRecorder import TimeRecorder
from utility.DebugScreen import DebugScreen


def main(q=None):
    # press p to start the AI
    while not keyboard.is_pressed("p"):
        pass
    tr = TimeRecorder("results", ["perception", "modeling", "decision making", "control", "action"])
    action = Action()
    control = Control(debug=q is not None, queue=q)
    decision_making = DecisionMaking(debug=q is not None, queue=q)
    modeling = Modeling(debug=q is not None, queue=q)
    perception = Perception(debug=q is not None, queue=q)
    time.sleep(0.1)
    # press p again to end the program
    while not keyboard.is_pressed("p"):
        tr.start()
        objects = perception.perceive()[0]
        tr.split()
        modeling.update_model(objects)
        tr.split()
        decision_making.decide(modeling)
        tr.split()
        control.control(decision_making, modeling)
        tr.split()
        action.act(control)
        tr.end()
        time.sleep(0.3)
    print("end")

if __name__ == "__main__":
    debug = True
    if debug:
        debug_screen = DebugScreen()
        main_thread = threading.Thread(target=main, args=(debug_screen.q,), daemon=True)
        main_thread.start()
        while True:
            debug_screen.update()
            time.sleep(0.05)
    else:
       main()
