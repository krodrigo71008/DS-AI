from modeling.objects.ObjectModel import ObjectModel
from utility.Point2d import Point2d


class Flower(ObjectModel):
    def __init__(self, position : Point2d, latest_screen_position : Point2d):
        super().__init__(False, position, latest_screen_position)

    def update(self, change):
        pass
