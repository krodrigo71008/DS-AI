from modeling.objects.ObjectModel import ObjectModel


class PickableObjectModel(ObjectModel):
    def __init__(self, position, id_, name):
        super().__init__(True, position)
        self.id = id_
        self.name = name

    def update(self, change):
        pass
