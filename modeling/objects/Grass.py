from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime

GRASS_READY = 21
GRASS_HARVESTED = 22


class Grass(ObjectWithMultipleForms):
    def __init__(self, position, id_, update_function):
        super().__init__(False, position, [GRASS_READY, GRASS_HARVESTED], id_, update_function)
        if id_ == GRASS_HARVESTED:
            self.update_function("grow", GameTime(non_winter_days=3), self)

    def update(self, change):
        if change == "grow":
            self._state = GRASS_READY

    def handle_object_detected(self, state) -> None:
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        if state == self._state:
            return
        # update state and schedule growth if it was just picked
        if state == GRASS_READY:
            self.set_state(GRASS_READY)
        else:
            self.set_state(GRASS_HARVESTED)

    def harvest(self):
        if self._state == GRASS_HARVESTED:
            raise Exception("Cannot harvest: already harvested!")
        self.handle_object_detected(GRASS_HARVESTED)

    def is_harvested(self) -> bool:
        return self._state == GRASS_HARVESTED

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state


