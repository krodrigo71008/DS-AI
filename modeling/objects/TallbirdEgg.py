from modeling.objects.PickableObjectModel import PickableObjectModel
from utility.Point2d import Point2d


class TallbirdEgg(PickableObjectModel):
    def __init__(self, position : Point2d, latest_screen_position : Point2d):
        super().__init__(position, latest_screen_position, 2, "TallbirdEgg")

    def update(self, change : str):
        pass
