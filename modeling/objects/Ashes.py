from modeling.objects.ObjectModel import ObjectModel
from utility.GameTime import GameTime


class Ashes(ObjectModel):
    def __init__(self, position, update_function):
        super().__init__(True, position)
        update_function("disappear", GameTime(seconds=20))

    def update(self, change):
        pass
