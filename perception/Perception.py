import time

import mss
import numpy as np
from PIL import Image
from ultralytics import YOLO
import cv2

from perception.ImageObject import ImageObject
from perception.constants import SCREEN_SIZE, SCREEN_POS
from perception.YoloIdConverter import yolo_id_converter
from utility.utility import hide_huds_numpy, draw_annotations

mon = {"top": SCREEN_POS["top"], "left": SCREEN_POS["left"],
       "width": SCREEN_SIZE["width"], "height": SCREEN_SIZE["height"]}


class Perception:
    def __init__(self, debug=False, queue=None):
        self.model = YOLO("perception/darknet/best.pt")
        self.CONFIDENCE_THRESHOLD = .5
        self.NMS_THRESHOLD = .7
        self.sct = mss.mss()
        self.objects = []
        self.last_screenshot = None
        self.debug = debug
        if self.debug:
            self.queue = queue
        frame = self.get_screenshot()
        frame = Image.fromarray(frame, mode="RGB")
        frame = np.asarray(frame)
        self.process_frame(frame)
        self.process_frame(frame)

    def get_screenshot(self, frame : np.ndarray = None) -> np.ndarray:
        if frame is not None:
            return frame
        img = np.asarray(self.sct.grab(mon)) # this is in BGRA
        no_alpha_img = img[:, :, :3]
        # no_alpha_img = no_alpha_img[:, :, ::-1]
        return no_alpha_img # this is in RGB

    def process_frame(self, frame : np.ndarray):
        # box is (x, y, l, h)
        result = self.model.predict(frame, conf=self.CONFIDENCE_THRESHOLD, iou=self.NMS_THRESHOLD, verbose=False)[0].boxes
        classes = [int(res.cls) for res in result]
        scores = [res.conf.item() for res in result]
        boxes = [res.xywh.cpu().numpy().astype(int)[0] for res in result]
            
        return classes, scores, boxes

    def hide_huds(self, frame : np.ndarray) -> np.ndarray:
        return hide_huds_numpy(frame)

    def create_objects(self, classes, scores, boxes) -> None:
        new_classes = [yolo_id_converter.yolo_to_actual_id(id_) for id_ in classes]
        self.objects = []
        for class_id, score, box in zip(new_classes, scores, boxes):
            obj = ImageObject(class_id, score, box)
            self.objects.append(obj)

    def put_in_queue(self, frame, classes, scores, boxes):
        if self.debug:
            if self.queue is not None and self.queue.empty():
                try:
                    self.queue.put(("detected_objects", draw_annotations(frame, classes, scores, boxes)[0])) # takes like 20 ms avg
                except ValueError:
                    print("perception debug_queue closed")


    def perceive(self, frame : np.ndarray = None):
        frame = self.get_screenshot(frame) # takes like 30 ms avg
        if self.last_screenshot is not None:
            diff = np.average(cv2.absdiff(self.last_screenshot, frame))
        else:
            diff = None
        self.last_screenshot = frame.copy()
        frame = self.hide_huds(frame)
        classes, scores, boxes = self.process_frame(frame) # takes like 50 ms avg
        self.create_objects(classes, scores, boxes)
        self.put_in_queue(frame, classes, scores, boxes)
        return self.objects, classes, scores, boxes, diff

class PerceptionRecorder(Perception):
    def __init__(self, debug=False, queue=None):
        self.all_captured_images : list[np.ndarray] = []
        super().__init__(debug, queue)

    def get_screenshot(self, frame: np.ndarray = None) -> np.ndarray:
        ans = super().get_screenshot(frame)
        self.all_captured_images.append(ans)
        return ans

class PerceptionTimer(Perception):
    def __init__(self, debug=False, queue=None):
        self.time_records = []
        self.split_names = ["screenshot", "hide_huds", "process_frame", "create_objects", "put_in_debug_queue"]
        self.current_time_list = []
        super().__init__(debug, queue)

    def get_screenshot(self, frame: np.ndarray = None) -> np.ndarray:
        t1 = time.time_ns()
        return_value = super().get_screenshot(frame)
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)
        return return_value

    def hide_huds(self, frame: np.ndarray) -> np.ndarray:
        t1 = time.time_ns()
        return_value = super().hide_huds(frame)
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)
        return return_value
    
    def process_frame(self, frame: np.ndarray):
        t1 = time.time_ns()
        return_value = super().process_frame(frame)
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)
        return return_value
    
    def create_objects(self, classes, scores, boxes) -> None:
        t1 = time.time_ns()
        super().create_objects(classes, scores, boxes)
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)
    
    def put_in_queue(self, frame, classes, scores, boxes):
        t1 = time.time_ns()
        super().put_in_queue(frame, classes, scores, boxes)
        t2  = time.time_ns()
        self.current_time_list.append(t2-t1)

    def perceive(self, frame: np.ndarray = None):
        self.current_time_list = []
        return_value = super().perceive(frame)
        self.time_records.append(self.current_time_list.copy())
        return return_value
