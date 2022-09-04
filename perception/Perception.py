import mss
import numpy as np
import cv2
from PIL import Image

from perception.ImageObject import ImageObject
from perception.screen import SCREEN_SIZE, SCREEN_POS
from utility.Point2d import Point2d
from utility.utility import hide_huds

mon = {"top": SCREEN_POS["top"], "left": SCREEN_POS["left"],
       "width": SCREEN_SIZE["width"], "height": SCREEN_SIZE["height"]}


class Perception:
    def __init__(self):
        with open("perception/darknet/obj.names", "r") as f:
            self.class_names = [cname.strip() for cname in f.readlines()]
        self.CONFIDENCE_THRESHOLD = 0.01
        self.NMS_THRESHOLD = 0.45
        net = cv2.dnn.readNet("perception/darknet/yolov4-tiny-custom_best.weights", "perception/darknet/yolov4-tiny-custom.cfg")
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        self.model = cv2.dnn_DetectionModel(net)
        self.model.setInputParams(size=(416, 416), scale=1 / 255)
        self.objects = []
        # last player position in opencv coordinates
        self.last_player_position = Point2d(0, 0)

    @staticmethod
    def get_screenshot():
        sct = mss.mss()
        img = np.asarray(sct.grab(mon))
        no_alpha_img = img[:, :, :3]
        return no_alpha_img

    def perceive(self, debug=False):
        frame = self.get_screenshot()
        frame = Image.fromarray(frame, mode="RGB")
        frame = hide_huds(frame)
        frame = np.asarray(frame)
        # box is (x, y, l, h)
        classes, scores, boxes = self.model.detect(frame, self.CONFIDENCE_THRESHOLD, self.NMS_THRESHOLD)
        objects = []
        for class_id, score, box in zip(classes, scores, boxes):
            if class_id == 0:
                self.last_player_position = Point2d(box[0] + box[2]//2, box[1] + box[3]//2)
        for class_id, score, box in zip(classes, scores, boxes):
            obj = ImageObject(class_id, score, box)
            objects.append(obj)
        if debug:
            return objects, frame
        else:
            return objects
