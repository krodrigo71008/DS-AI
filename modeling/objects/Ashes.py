from modeling.objects.ObjectModel import ObjectModel
from utility.GameTime import GameTime


class Ashes(ObjectModel):
    def __init__(self, position, latest_screen_position, update_function):
        super().__init__(True, position, latest_screen_position)
        update_function("disappear", GameTime(seconds=20), self)

    def update(self, change):
        pass
