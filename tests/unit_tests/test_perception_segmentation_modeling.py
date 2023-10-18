import os

from PIL import Image
import numpy as np

from modeling.Modeling import Modeling
from perception.SegmentationModel import SegmentationModel
from perception.Perception import Perception


# def run_perception_segmentation_modeling_single_frame(input_image_path):
#     debug_output_path = "tests/test_results/test_perception_segmentation_modeling/"
#     os.makedirs(debug_output_path, exist_ok=True)
#     perception = Perception()
#     segmentation = SegmentationModel()
#     modeling = Modeling()
#     img = np.asarray(Image.open(input_image_path)).copy()
#     objects = perception.perceive(img)[0]
#     seg_info = segmentation.process_frame(img)
#     modeling.received_yolo_info = True
#     modeling.received_segmentation_info = True
#     modeling.update_model_using_info(objects, seg_info, debug_output_path)
#     print("Done")