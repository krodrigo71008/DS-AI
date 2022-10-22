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
    dir_options = [(1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)]
    scales = [1, 1, 2, 2, 5, 5]

    # route_start should be in [0, 7] (closed)
    route_start = 0
    route = []
    route_index = route_start
    current_point = Point2d(0, 0)
    while len(route) < len(dir_options)*len(scales):
        dpoint = dir_options[route_index % len(dir_options)]
        dpoint = Point2d(dpoint[0], dpoint[1])
        # make dpoint have length 6*scale since character moves at 6/s
        dpoint = dpoint/dpoint.distance(Point2d(0, 0))*6*scales[route_index//len(dir_options)]
        route_index += 1
        current_point += dpoint
        route.append(current_point)

    BASE_SECONDS_PER_ROUTE_STEP = 1.5
    helper = []
    for s in scales:
        helper.extend([s]*len(dir_options))
    time_aux = 0
    time_to_index_aux = []
    for h in helper:
        time_aux += h*BASE_SECONDS_PER_ROUTE_STEP
        time_to_index_aux.append(time_aux)
    
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
    route_index = 0
    orders = []
    # press p again to end the program
    while not keyboard.is_pressed("p"):
        objects = perception.perceive()[0]
        modeling.update_model(objects)
        decision_making.decide(modeling)
        cur_time = time.time() - start_time
        if cur_time > time_to_index_aux[route_index]:
            route_index += 1
            if route_index >= len(time_to_index_aux):
                break
        decision_making.secondary_action = ("go_precisely_to", route[route_index])
        orders.append(("go_precisely_to", route[route_index]))
        control.control(decision_making, modeling)
        # print(f"{time.time() - start_time:.2f}: {modeling.player_model.position}, go_to {route[route_index]}, keys {control.key_action}")
        action.act(control)
    
    for i, cap_img in enumerate(perception.all_captured_images):
        img = Image.fromarray(cap_img, mode="RGB")
        img.save(f"records/start_{route_start}_{i}.jpg")
    
    with open(f"records/time_records_{route_start}.pkl", 'wb') as file:
        pickle.dump(clock_rec.time_records, file)
    
    with open(f"records/orders_{route_start}.pkl", 'wb') as file:
        pickle.dump(orders, file)
    print("end")