from modeling.objects.ObjectModel import ObjectModel
from utility.GameTime import GameTime
from utility.Point2d import Point2d


class Ashes(ObjectModel):
    def __init__(self, position : Point2d, latest_screen_position : Point2d, update_function : "function"):
        super().__init__(True, position, latest_screen_position)
        update_function("disappear", GameTime(seconds=20), self)

    def update(self, change):
        pass
