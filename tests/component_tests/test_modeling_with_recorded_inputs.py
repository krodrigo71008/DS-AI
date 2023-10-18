import time
import pickle
import glob

import numpy as np
from PIL import Image

from control.Control import Control
from decisionMaking.DecisionMaking import DecisionMaking
from modeling.Modeling import Modeling
from perception.Perception import Perception
from utility.Visualizer import Visualizer
from utility.Clock import ClockMock


def try_out_modeling_with_recorded_inputs():
    LIMIT_IMAGES = 5000
    route_start = 0
    with open(f"records/time_records_{route_start}.pkl", 'rb') as file:
        time_records = pickle.load(file)
    
    with open(f"records/orders_{route_start}.pkl", 'rb') as file:
        orders = pickle.load(file)

    clock_mock = ClockMock(initial_last_time=time_records[0])
    clock_mock.times_to_return = time_records
    control = Control(clock=clock_mock)
    decision_making = DecisionMaking()
    modeling = Modeling(clock=clock_mock)
    perception = Perception()
    vis_screen = Visualizer()
    
    files = glob.glob('records/start_*.jpg')
    files_sort_aux = []
    for f in files:
        files_sort_aux.append((int(f.split("\\")[-1].split("_")[-1].split(".")[0]), f))
    files_sort_aux.sort()
    sorted_files = [f[1] for f in files_sort_aux]
    
    i = 0
    for file, order in zip(sorted_files, orders):
        with Image.open(file) as raw_image:
            img = np.asarray(raw_image)
            objects, classes, scores, boxes = perception.perceive(np.asarray(img))
            vis_screen.update_yolo_image(img[:, :, ::-1])
            vis_screen.draw_detected_objects(classes, scores, boxes)
            modeling.update_model(objects)
            vis_screen.update_world_model(modeling)
            vis_screen.draw_estimation_errors(modeling.world_model.estimation_errors)
            decision_making.decide(modeling)
            decision_making.secondary_action = order
            control.control(decision_making, modeling)
            file_path_final = file.split('\\')[-1]
            vis_screen.export_results(f"tests/test_results/test_modeling_with_recorded/{file_path_final}")
            # print(f"{time.time() - start_time:.2f}: {modeling.player_model.position}, go_to {route[route_index]}, keys {control.key_action}")
        i += 1
        if i == LIMIT_IMAGES:
            break

    print("end")