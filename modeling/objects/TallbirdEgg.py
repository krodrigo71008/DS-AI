from modeling.objects.PickableObjectModel import PickableObjectModel


class TallbirdEgg(PickableObjectModel):
    def __init__(self, position):
        super().__init__(position, 2, "TallbirdEgg")

    def update(self, change):
        pass
