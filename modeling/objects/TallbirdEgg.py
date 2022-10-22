from modeling.objects.PickableObjectModel import PickableObjectModel


class TallbirdEgg(PickableObjectModel):
    def __init__(self, position, latest_screen_position):
        super().__init__(position, latest_screen_position, 2, "TallbirdEgg")

    def update(self, change):
        pass
