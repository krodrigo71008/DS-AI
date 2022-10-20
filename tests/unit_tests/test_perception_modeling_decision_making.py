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
    corners = (modeling.world_model.c1, modeling.world_model.c2, modeling.world_model.c3, modeling.world_model.c4)
    vis_screen.update_world_model(modeling.world_model.object_lists, modeling.player_model, corners, modeling.world_model.origin_coordinates)
    decision_making.decide(modeling)
    vis_screen.export_results(f"tests/test_results/test_perception_modeling_decision_making/single_{input_image_path}")
