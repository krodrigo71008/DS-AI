import mss
import numpy as np
from PIL import Image
from ultralytics import YOLO

from perception.ImageObject import ImageObject
from perception.constants import SCREEN_SIZE, SCREEN_POS
from perception.YoloIdConverter import yolo_id_converter
from utility.utility import hide_huds, draw_annotations

mon = {"top": SCREEN_POS["top"], "left": SCREEN_POS["left"],
       "width": SCREEN_SIZE["width"], "height": SCREEN_SIZE["height"]}


class Perception:
    def __init__(self, debug=False, queue=None):
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
        frame = self.get_screenshot()
        frame = Image.fromarray(frame, mode="RGB")
        frame = np.asarray(frame)
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
