from modeling.objects.ObjectModel import ObjectModel


class TallbirdNest(ObjectModel):
    def __init__(self, position, latest_screen_position):
        super().__init__(False, position, latest_screen_position)
        self.has_egg = False

    def update(self, change):
        pass

    def set_has_egg(self, has_egg):
        self.has_egg = has_egg
