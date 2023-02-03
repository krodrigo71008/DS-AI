from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime
from utility.Point2d import Point2d


class SpiderNest(ObjectWithMultipleForms):
    def __init__(self, position : Point2d, latest_screen_position : Point2d, id_ : int, update_function : "function"):
        super().__init__(False, position, latest_screen_position, [35], id_, update_function)
        # I'll add the other states later

    def update(self, change):
        pass

    def handle_object_detected(self, state):
        pass

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state


