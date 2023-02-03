from modeling.objects.ObjectModel import ObjectModel
from utility.Point2d import Point2d


class ObjectWithMultipleForms(ObjectModel):
    # object_ids should be an array like this: [id1, id2]
    # update_function should be a lambda that calls schedule_update from the world model with the change
    # and a time delta as arguments
    def __init__(self, pickable : bool, position : Point2d, latest_screen_position : Point2d, 
                 object_ids : list[int], initial_state : int, update_function : "function"):
        if len(object_ids) == 0:
            raise Exception("Invalid empty list of object ids!")
        if type(object_ids) is not list:
            raise Exception("Invalid constructor arguments!")
        super().__init__(pickable, position, latest_screen_position)
        self.object_ids = object_ids
        self._state = initial_state
        self.update_function = update_function

    def update(self, change):
        raise NotImplementedError()

    def handle_object_detected(self, state):
        raise NotImplementedError()
