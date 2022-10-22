from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from utility.GameTime import GameTime

BERRYBUSH_READY = 35
BERRYBUSH_HARVESTED = 36


class BerryBush(ObjectWithMultipleForms):
    def __init__(self, position, latest_screen_position, id_, update_function):
        super().__init__(False, position, latest_screen_position, [BERRYBUSH_READY, BERRYBUSH_HARVESTED], id_, update_function)
        if id_ == BERRYBUSH_HARVESTED:
            self.update_function("grow", GameTime(non_winter_days=4.6875), self)

    def update(self, change):
        if change == "grow":
            self._state = BERRYBUSH_READY

    def handle_object_detected(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        if state == self._state:
            return
        # update state and schedule growth if it was just picked
        if state == BERRYBUSH_READY:
            self.set_state(BERRYBUSH_READY)
        else:
            self.set_state(BERRYBUSH_HARVESTED)

    def harvest(self):
        self._state = BERRYBUSH_HARVESTED
        self.update_function("grow", GameTime(non_winter_days=4.6875), self)

    def is_harvested(self) -> bool:
        return self._state == BERRYBUSH_HARVESTED

    def set_state(self, state):
        if state not in self.object_ids:
            raise Exception("Invalid id!")
        self._state = state


