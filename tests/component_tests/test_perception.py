import glob
import time

import cv2
import tqdm

from perception.Perception import Perception
from utility.utility import draw_annotations


def annotate_image_folder(folder_path : str) -> None:
    """Annotate every image in the folder

    :param video_path: path to input video
    :type video_path: str
    :param output_path: path to output video
    :type output_path: str
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
