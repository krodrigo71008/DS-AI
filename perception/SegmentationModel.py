import time

import mss
import numpy as np
import torch

from perception.constants import SCREEN_SIZE, SCREEN_POS
from utility.utility import hide_huds_numpy

mon = {"top": SCREEN_POS["top"], "left": SCREEN_POS["left"],
       "width": SCREEN_SIZE["width"], "height": SCREEN_SIZE["height"]}


class SegmentationModel:
    def __init__(self, debug=False, queue=None):
        self.model = torch.jit.load("perception/segmentation/model_scripted.pt")
        self.model.to("cuda")
        self.model.eval()
        self.CONFIDENCE_THRESHOLD = .5
        self.sct = mss.mss()
        self.debug = debug
        if self.debug:
            self.queue = queue

        self.mean = np.array([0.485, 0.456, 0.406])
        self.std = np.array([0.229, 0.224, 0.225])
        self.input_range = [0, 1]

    def preprocess_input(self, x):
        if x.max() > 1 and self.input_range[1] == 1:
            x = x / 255.0
        x = x - self.mean
        x = x / self.std

        return x

    def get_screenshot(self):
        img = np.asarray(self.sct.grab(mon)) # this is in BGRA
        no_alpha_img = img[:, :, :3]
        no_alpha_img = no_alpha_img[:, :, ::-1]
        return no_alpha_img # this is in RGB

    def process_frame(self, frame : np.array):
        with torch.no_grad():
            frame = self.preprocess_input(frame)
            frame = np.transpose(frame, (2, 0, 1))
            image = torch.from_numpy(frame.copy()).unsqueeze(0)
            image = torch.nn.functional.interpolate(image, (512, 512)).to("cuda")
            image = image.float()
            result = self.model.forward(image)
        prediction = result.squeeze().cpu().numpy().round()
        prediction = np.transpose(prediction, axes=(1, 2, 0))
        prediction = prediction > self.CONFIDENCE_THRESHOLD
        
        return prediction

    def perceive(self, frame : np.array = None):
        # t1 = time.time()
        if frame is None:
            frame = self.get_screenshot() # takes like 30 ms avg
        # t2 = time.time()
        prediction = self.process_frame(frame) # takes like 30 ms avg
        # t3 = time.time()

        if self.debug:
            self.queue.put(("segmentation_results", prediction)) # takes like 20 ms avg
        # t4 = time.time()
        # print(f"{t2-t1} {t3-t2} {t4-t3}")
        return prediction

class SegmentationRecorder(SegmentationModel):
    def __init__(self, debug=False, queue=None):
        super().__init__(debug, queue)
        self.all_captured_images : list[np.array] = []

    def get_screenshot(self):
        ans = super().get_screenshot()
        self.all_captured_images.append(ans)
        return ans
