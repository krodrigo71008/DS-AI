from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime

EVERGREEN_SMALL = 31
EVERGREEN_MEDIUM = 32
EVERGREEN_BIG = 33
EVERGREEN_DEAD = 58


class TreeEvergreen(ObjectWithMultipleForms):
    def __init__(self, position, latest_screen_position, id_, update_function):
        super().__init__(False, position, latest_screen_position,
                         [EVERGREEN_SMALL, EVERGREEN_MEDIUM, EVERGREEN_BIG, EVERGREEN_DEAD], id_, update_function)
        # times are random, 1*5-2*5, 3*5-7*5, 3*5-7*5 and 0.5*5-1.5*5, but I'm using the maximum value
        if id_ == EVERGREEN_SMALL:
            self.update_function("growToMedium", GameTime(minutes=2*5), self)
        elif id_ == EVERGREEN_MEDIUM:
            self.update_function("growToBig", GameTime(minutes=7*5), self)
        elif id_ == EVERGREEN_BIG:
            self.update_function("growToDead", GameTime(minutes=7*5), self)
        else:
            self.update_function("growToSmall", GameTime(minutes=1.5*5), self)

    def update(self, change):
        if change == "growToSmall":
            self._state = EVERGREEN_SMALL
        if change == "growToMedium":
            self._state = EVERGREEN_MEDIUM
        if change == "growToBig":
            self._state = EVERGREEN_BIG
        if change == "growToDead":
            self._state = EVERGREEN_DEAD

    def handle_object_detected(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        if state == self._state:
            return
        # update state and schedule growth if it was just picked
        if state == EVERGREEN_SMALL:
            self.set_state(EVERGREEN_SMALL)
            # self.update_function("growToMedium", GameTime(minutes=2*5), self)
        elif state == EVERGREEN_MEDIUM:
            self.set_state(EVERGREEN_MEDIUM)
            # self.update_function("growToBig", GameTime(minutes=7*5), self)
        elif state == EVERGREEN_BIG:
            self.set_state(EVERGREEN_BIG)
            # self.update_function("growToDead", GameTime(minutes=7*5), self)
        else:
            self.set_state(EVERGREEN_DEAD)
            # self.update_function("growToSmall", GameTime(minutes=1.5*5), self)

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state


