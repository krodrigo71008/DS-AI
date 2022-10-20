from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime

SAPLING_READY = 23
SAPLING_HARVESTED = 24


class Sapling(ObjectWithMultipleForms):
    def __init__(self, position, id_, update_function):
        super().__init__(False, position, [SAPLING_READY, SAPLING_HARVESTED], id_, update_function)
        if id_ == SAPLING_HARVESTED:
            self.update_function("grow", GameTime(non_winter_days=4), self)

    def update(self, change):
        if change == "grow":
            self._state = SAPLING_READY

    def handle_object_detected(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        if state == self._state:
            return
        # update state and schedule growth if it was just picked
        if state == SAPLING_READY:
            self.set_state(SAPLING_READY)
        else:
            self.set_state(SAPLING_HARVESTED)

    def harvest(self):
        if self._state == SAPLING_HARVESTED:
            raise Exception("Cannot harvest: already harvested!")
        self.handle_object_detected(SAPLING_HARVESTED)

    def is_harvested(self) -> bool:
        return self._state == SAPLING_HARVESTED

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state


