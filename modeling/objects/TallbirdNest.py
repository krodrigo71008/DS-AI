from modeling.objects.ObjectWithSingleForm import ObjectWithSingleForm
from utility.Point2d import Point2d


class TallbirdNest(ObjectWithSingleForm):
    def __init__(self, position : Point2d, latest_screen_position :  Point2d):
        super().__init__(False, position, latest_screen_position)
        self.has_egg = False

    def update(self, change : str):
        pass

    def set_has_egg(self, has_egg):
        self.has_egg = has_egg
