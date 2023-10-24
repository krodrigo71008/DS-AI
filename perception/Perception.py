import time

import mss
import numpy as np
from PIL import Image
from ultralytics import YOLO

from perception.ImageObject import ImageObject
from perception.constants import SCREEN_SIZE, SCREEN_POS
from perception.YoloIdConverter import yolo_id_converter
from utility.utility import hide_huds_numpy, draw_annotations

mon = {"top": SCREEN_POS["top"], "left": SCREEN_POS["left"],
       "width": SCREEN_SIZE["width"], "height": SCREEN_SIZE["height"]}


class Perception:
    def __init__(self, debug=False, queue=None, measure_time=False):
        self.model = YOLO("perception/darknet/best.pt")
        self.CONFIDENCE_THRESHOLD = .5
        self.NMS_THRESHOLD = .7
        # net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        # net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
        self.sct = mss.mss()
        self.objects = []
        self.debug = debug
        if self.debug:
            self.queue = queue
        self.measure_time = measure_time
        if self.measure_time:
            self.time_records = []
            self.split_names = ["screenshot", "hide_huds", "process_frame", "create_objects", "put_in_debug_queue"]
        frame = self.get_screenshot()
        frame = Image.fromarray(frame, mode="RGB")
        frame = np.asarray(frame)
        self.process_frame(frame)
        self.process_frame(frame)

    def get_screenshot(self):
        img = np.asarray(self.sct.grab(mon)) # this is in BGRA
        no_alpha_img = img[:, :, :3]
        # no_alpha_img = no_alpha_img[:, :, ::-1]
        return no_alpha_img # this is in RGB

    def process_frame(self, frame : np.array):
        # box is (x, y, l, h)
        result = self.model.predict(frame, conf=self.CONFIDENCE_THRESHOLD, iou=self.NMS_THRESHOLD, verbose=False)[0].boxes
        classes = [int(res.cls) for res in result]
        scores = [res.conf.item() for res in result]
        boxes = [res.xywh.cpu().numpy().astype(int)[0] for res in result]
            
        return classes, scores, boxes

    def perceive(self, frame : np.array = None):
        if self.measure_time:
            t1 = time.time_ns()

        if frame is None:
            frame = self.get_screenshot() # takes like 30 ms avg

        if self.measure_time:
            t2 = time.time_ns()

        frame = hide_huds_numpy(frame)

        if self.measure_time:
            t3 = time.time_ns()
            
        classes, scores, boxes = self.process_frame(frame) # takes like 50 ms avg

        if self.measure_time:
            t4 = time.time_ns()
            
        new_classes = [yolo_id_converter.yolo_to_actual_id(id_) for id_ in classes]
        self.objects = []
        for class_id, score, box in zip(new_classes, scores, boxes):
            obj = ImageObject(class_id, score, box)
            self.objects.append(obj)

        if self.measure_time:
            t5 = time.time_ns()
            
        if self.debug:
            try:
                self.queue.put(("detected_objects", draw_annotations(frame, classes, scores, boxes)[0])) # takes like 20 ms avg
            except ValueError:
                print("perception debug_queue closed")

        if self.measure_time:
            t6 = time.time_ns()
            self.time_records.append([t2-t1, t3-t2, t4-t3, t5-t4, t6-t5])
            
        return self.objects, classes, scores, boxes

class PerceptionRecorder(Perception):
    def __init__(self, debug=False, queue=None):
        self.all_captured_images : list[np.array] = []
        super().__init__(debug, queue)

    def get_screenshot(self):
        ans = super().get_screenshot()
        self.all_captured_images.append(ans)
        return ans
