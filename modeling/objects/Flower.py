from modeling.objects.ObjectModel import ObjectModel


class Flower(ObjectModel):
    def __init__(self, position, latest_screen_position):
        super().__init__(False, position, latest_screen_position)

    def update(self, change):
        pass
