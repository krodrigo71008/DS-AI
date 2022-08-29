from perception.screen import SCREEN_SIZE
from utility.Point2d import Point2d


class ImageObject:
    def __init__(self, class_id, score, box):
        self.id = class_id
        self.score = score
        self.box = box
