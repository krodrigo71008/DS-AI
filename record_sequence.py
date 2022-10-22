import time
import pickle

import keyboard
from PIL import Image

from action.Action import Action
from control.Control import Control
from decisionMaking.DecisionMaking import DecisionMaking
from modeling.Modeling import Modeling
from perception.Perception import PerceptionRecorder
from utility.Clock import ClockRecorder
from utility.Point2d import Point2d


if __name__ == '__main__':
    while not keyboard.is_pressed("p"):
        pass
    clock_rec = ClockRecorder()
    action = Action()
    control = Control(clock=clock_rec)
    decision_making = DecisionMaking()
    modeling = Modeling(clock=clock_rec)
    perception = PerceptionRecorder()
    time.sleep(0.1)
    start_time = time.time()
    orders = []
    # press p again to end the program
    while not keyboard.is_pressed("p"):
        objects = perception.perceive()[0]
        modeling.update_model(objects)
        decision_making.decide(modeling)
        orders.append(decision_making.secondary_action)
        control.control(decision_making, modeling)
        print(f"{time.time() - start_time:.2f}: {modeling.player_model.position}, {decision_making.secondary_action}, keys {control.key_action}")
        action.act(control)
    
    for i, cap_img in enumerate(perception.all_captured_images):
        img = Image.fromarray(cap_img, mode="RGB")
        img.save(f"records/start_{i}.jpg")
    
    with open("records/time_records.pkl", 'wb') as file:
        pickle.dump(clock_rec.time_records, file)
    
    with open("records/orders.pkl", 'wb') as file:
        pickle.dump(orders, file)
    print("end")