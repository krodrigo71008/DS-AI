import mss
import numpy as np
import cv2
from PIL import Image

from perception.ImageObject import ImageObject
from perception.screen import SCREEN_SIZE, SCREEN_POS
from perception.YoloIdConverter import yolo_id_converter
from utility.utility import hide_huds, draw_annotations

mon = {"top": SCREEN_POS["top"], "left": SCREEN_POS["left"],
       "width": SCREEN_SIZE["width"], "height": SCREEN_SIZE["height"]}


class Perception:
    def __init__(self, debug=False, queue=None):
        with open("perception/darknet/obj.names", "r") as f:
            self.class_names = [cname.strip() for cname in f.readlines()]
        self.CONFIDENCE_THRESHOLD = 0.01
        self.NMS_THRESHOLD = 0.45
        net = cv2.dnn.readNet("perception/darknet/yolov4-tiny-custom_final.weights", "perception/darknet/yolov4-tiny-custom.cfg")
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        self.model = cv2.dnn_DetectionModel(net)
        self.model.setInputParams(size=(416, 416), scale=1 / 255)
        self.sct = mss.mss()
        self.objects = []
        self.debug = debug
        if self.debug:
            self.queue = queue

    def get_screenshot(self):
        img = np.asarray(self.sct.grab(mon))
        no_alpha_img = img[:, :, :3]
        no_alpha_img = no_alpha_img[:, :, ::-1]
        return no_alpha_img

    def process_frame(self, frame : np.array):
        # box is (x, y, l, h)
        classes, scores, boxes = self.model.detect(frame, self.CONFIDENCE_THRESHOLD, self.NMS_THRESHOLD)
        return classes, scores, boxes

    def perceive(self, frame : np.array = None):
        if frame is None:
            frame = self.get_screenshot()
        frame = Image.fromarray(frame, mode="RGB")
        frame = hide_huds(frame)
        frame = np.asarray(frame)
        classes, scores, boxes = self.process_frame(frame)
        new_classes = [yolo_id_converter.yolo_to_actual_id(id_) for id_ in classes]
        objects = []
        for class_id, score, box in zip(new_classes, scores, boxes):
            obj = ImageObject(class_id, score, box)
            objects.append(obj)
        if self.debug:
            self.queue.put(("detected_objects", draw_annotations(frame, classes, scores, boxes)[0]))
        return objects, classes, scores, boxes

class PerceptionRecorder(Perception):
    def __init__(self, debug=False, queue=None):
        super().__init__(debug, queue)
        self.all_captured_images : list[np.array] = []

    def get_screenshot(self):
        ans = super().get_screenshot()
        self.all_captured_images.append(ans)
        return ans
