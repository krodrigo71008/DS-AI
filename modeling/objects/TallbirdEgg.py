from modeling.objects.PickableObjectModel import PickableObjectModel


class TallbirdEgg(PickableObjectModel):
    def __init__(self, position):
        super().__init__(position)

    def update(self, change):
        pass
