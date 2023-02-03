from modeling.objects.ObjectModel import ObjectModel
from utility.Point2d import Point2d


class PickableObjectModel(ObjectModel):
    def __init__(self, position : Point2d, latest_screen_position : Point2d, id_ : int, name : str):
        super().__init__(True, position, latest_screen_position)
        self.id = id_
        self.name = name

    def update(self, change):
        pass
