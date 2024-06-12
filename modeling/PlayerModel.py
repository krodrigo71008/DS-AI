import time

from modeling.Inventory import Inventory
from utility.Clock import Clock


class PlayerModel:
    def __init__(self, clock : Clock):
        self.clock : Clock = clock
        self.inventory = Inventory()
        self.health = 150
        self.max_health = 150
        self.hunger = 150
        self.max_hunger = 150
        self.sanity = 200
        self.max_sanity = 200

    def update(self) -> None:
        self.inventory.update(self.clock.dt())
        self.hunger -= self.clock.dt()*75/480
        day_section = self.clock.day_section()
        if day_section == "Dusk" or day_section == "Night":
            self.sanity -= self.clock.dt()*5/60

class PlayerModelTimer(PlayerModel):
    def __init__(self, clock: Clock):
        super().__init__(clock)
        self.time_records = []

    def update(self) -> None:
        t1 = time.time_ns()
        super().update()
        t2 = time.time_ns()
        self.time_records.append(t2-t1)
    
