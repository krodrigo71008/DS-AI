import glob
import time
import os
from pathlib import Path

import cv2
import tqdm
from ultralytics import YOLO

from perception.Perception import Perception
from perception.classes import get_class_names
from utility.utility import draw_annotations, iou

def generate_detections_all_models(folder_path : str) -> None:
    """Use all models in perception/darknet/models to annotate the given folder and saves results to perception/test_results

    :param folder_path: path to input folder
    :type folder_path: str
    """
    filenames = glob.glob(folder_path + '/*.jpg', recursive=True)
    filenames.extend(glob.glob(folder_path + '/*.png', recursive=True))
    models = glob.glob("perception/darknet/models/*.pt")
    perception = Perception()
    class_names = get_class_names()
    previous_detections = glob.glob("perception/test_results/**/*.txt", recursive=True)
    for f in previous_detections:
        os.remove(f)
    for model in models:
        model_name = Path(model).stem
        perception.model = YOLO(model)
        result_folder = "perception/test_results/" + model_name
        if not os.path.exists(result_folder):
            os.makedirs(result_folder)
        for filename in tqdm.tqdm(filenames, desc=f"detections for {model_name}"):
            frame = cv2.imread(filename)
            # frame = frame[:, :, ::-1] # invert because opencv represents image in BGR, so we convert it to RGB
            classes, scores, boxes = perception.process_frame(frame)
            results = []
            for class_id, score, box in zip(classes, scores, boxes):
                results.append('%s %f %f %f %f %f\n' % (class_names[class_id], score, box[0] - box[2]//2, box[1] - box[3]//2, 
                                                        box[0] + box[2]//2, box[1] + box[3]//2))
            text_log_filename = Path(filename).stem + ".txt"
            with open(f"{result_folder}/{text_log_filename}", "w") as results_file:
                for result_str in results:
                    results_file.write(result_str)


def annotate_image_folder(folder_path : str) -> None:
    """Annotate every image in the folder

    :param folder_path: path to input folder
    :type folder_path: str
    """
    perception = Perception()
    filenames = glob.glob(folder_path + '/*.jpg')
    filenames.extend(glob.glob(folder_path + '/*.png', recursive=True))
    classes_list = []
    scores_list = []
    boxes_list = []
    time_begin = time.time()
    for filename in tqdm.tqdm(filenames):
        frame = cv2.imread(filename)
        # frame = frame[:, :, ::-1] # invert because opencv represents image in BGR, so we convert it to RGB
        classes, scores, boxes = perception.process_frame(frame)

        classes_list.append(classes)
        scores_list.append(scores)
        boxes_list.append(boxes)
    time_end = time.time()
    time_diff = time_end - time_begin
    time_per_image = time_diff / len(filenames)
    fps = 1.0 / time_per_image
    print("time spent: " + str(time_diff))
    print("fps: " + str(fps))

    for filename, classes, scores, boxes in zip(filenames, classes_list, scores_list, boxes_list):
        frame = cv2.imread(filename)
        image_result, _ = draw_annotations(frame, classes, scores, boxes)
        predictions_filename = filename.split('\\')[-1].split('.')[0] + '.jpg'
        cv2.imwrite('tests/test_results/test_perception/' + predictions_filename, image_result)


def annotate_image_folder_two_models(folder_path : str, model1_path : str, model2_path : str) -> None:
    """Annotate every image in the folder with two models: red indicates that only the first model detected it, green, only the second, blue, both detected it

    :param folder_path: path to input folder
    :type folder_path: str
    :param model1_path: path to first YOLO model
    :type model1_path: str
    :param model2_path: path to second YOLO model
    :type model2_path: str
    """
    perception1 = Perception()
    perception1.model = YOLO(model1_path)
    perception2 = Perception()
    perception2.model = YOLO(model2_path)
    filenames = glob.glob(folder_path + '/*.jpg')
    filenames.extend(glob.glob(folder_path + '/*.png', recursive=True))
    classes_list1 = []
    scores_list1 = []
    boxes_list1 = []
    classes_list2 = []
    scores_list2 = []
    boxes_list2 = []
    time_begin = time.time()
    for filename in tqdm.tqdm(filenames):
        frame = cv2.imread(filename)
        # frame = frame[:, :, ::-1] # invert because opencv represents image in BGR, so we convert it to RGB
        classes1, scores1, boxes1 = perception1.process_frame(frame)
        classes2, scores2, boxes2 = perception2.process_frame(frame)

        classes_list1.append(classes1)
        scores_list1.append(scores1)
        boxes_list1.append(boxes1)
        classes_list2.append(classes2)
        scores_list2.append(scores2)
        boxes_list2.append(boxes2)
    time_end = time.time()
    time_diff = time_end - time_begin
    time_per_image = time_diff / len(filenames) / 2
    fps = 1.0 / time_per_image
    print("time spent: " + str(time_diff))
    print("fps: " + str(fps))

    IOU_THRESHOLD = .8
    for filename, classes1, scores1, boxes1, classes2, scores2, boxes2 in zip(filenames, classes_list1, scores_list1, boxes_list1, classes_list2, scores_list2, boxes_list2):
        frame = cv2.imread(filename)
        accepted = []
        used1 = [False]*len(classes1)
        used2 = [False]*len(classes2)
        i1 = 0
        # getting all bbs that appear in both models detections
        for c1, b1, s1 in zip(classes1, boxes1, scores1):
            i2 = 0
            for c2, b2, s2 in zip(classes2, boxes2, scores2):
                iou_value = iou(b1, b2)
                if c1 == c2 and iou_value > IOU_THRESHOLD:
                    if s1 > s2:
                        best = (c1, b1, s1)
                    else:
                        best = (c2, b2, s2)
                    ignore = False
                    for item in accepted:
                        if iou(item[0][1], best[1]) > IOU_THRESHOLD:
                            ignore = True
                            break
                    if not ignore:
                        accepted.append((best, (255, 0, 0), "up"))
                        used1[i1] = True
                        used2[i2] = True
                        
                i2 += 1
            i1 += 1
        
        i1 = 0
        for c1, b1, s1 in zip(classes1, boxes1, scores1):
            if not used1[i1]:
                accepted.append(((c1, b1, s1), (0, 0, 255), "up"))
            i1 += 1
        
        i2 = 0
        for c2, b2, s2 in zip(classes2, boxes2, scores2):
            if not used2[i2]:
                accepted.append(((c2, b2, s2), (0, 255, 0), "down"))
            i2 += 1

        accepted_classes = []
        accepted_boxes = []
        accepted_scores = []
        accepted_colors = []
        accepted_positions = []
        for item in accepted:
            accepted_classes.append(item[0][0])
            accepted_boxes.append(item[0][1])
            accepted_scores.append(item[0][2])
            accepted_colors.append(item[1])
            accepted_positions.append(item[2])

        image_result, _ = draw_annotations(frame, accepted_classes, accepted_scores, accepted_boxes, accepted_colors, accepted_positions)
        predictions_filename = filename.split('\\')[-1].split('.')[0] + '.jpg'
        cv2.imwrite('tests/test_results/test_perception_two_models/' + predictions_filename, image_result)
