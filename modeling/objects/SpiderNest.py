from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime


class SpiderNest(ObjectWithMultipleForms):
    def __init__(self, position, id_, update_function):
        super().__init__(False, position, [35], id_, update_function)
        # I'll add the other states later

    def update(self, change):
        pass

    def handle_object_detected(self, state):
        pass

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state


