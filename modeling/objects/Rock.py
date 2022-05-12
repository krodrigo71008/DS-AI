from modeling.objects.ObjectModel import ObjectModel


class Rock(ObjectModel):
    def __init__(self, position):
        super().__init__(False, position)

    def update(self, change):
        pass
