import math

import cv2

from modeling.Modeling import Modeling
from perception.Perception import Perception
from decisionMaking.DecisionMaking import DecisionMaking
from utility.Visualizer import Visualizer


def run_perception_modeling_decision_making_single_frame(input_image_path):
    perception = Perception()
    modeling = Modeling()
    decision_making = DecisionMaking()
    vis_screen = Visualizer()

    img = cv2.imread(input_image_path)
    vis_screen.update_image(img)
    # converting img from BGR to RGB
    img = img[:, :, ::-1]
    objects = perception.perceive(img)[0]
    modeling.update_model(objects)
    vis_screen.update_world_model(modeling)
    decision_making.decide(modeling)
    last_part_name = input_image_path.split("\\")[-1]
    vis_screen.export_results(f"tests/test_results/test_perception_modeling_decision_making/single_{last_part_name}")
