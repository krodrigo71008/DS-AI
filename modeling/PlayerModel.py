import math
from modeling.Inventory import Inventory
from utility.Clock import Clock
from utility.Point2d import Point2d
from modeling.constants import PLAYER_BASE_SPEED


class PlayerModel:
    def __init__(self, clock):
        self.position : Point2d = Point2d(0, 0)
        self.clock : Clock = clock
        self.inventory = Inventory()
        self.health = 150
        self.max_health = 150
        self.hunger = 150
        self.max_hunger = 150
        self.sanity = 200
        self.max_sanity = 200
        self.speed = PLAYER_BASE_SPEED
        self.direction : float = None

    def move(self, dt : float) -> None:
        """Moves the player model in the current direction

        :param dt: amount of time to update for
        :type dt: float
        """
        if self.direction is None:
            return
        self.position += Point2d(math.cos(self.direction), math.sin(self.direction))*dt*self.speed

    def set_direction(self, direction : float) -> None:
        """Sets player direction

        :param direction: direction in radians, expected to be a multiple of pi/4
        :type direction: float
        """
        self.direction = direction

    def update(self):
        self.inventory.update(self.clock.dt())
        self.move(self.clock.dt())
        self.hunger -= self.clock.dt()*75/480
        day_section = self.clock.day_section()
        if day_section == "Dusk" or day_section == "Night":
            self.sanity -= self.clock.dt()*5/60

    def player_detected(self, image_obj):
        # not sure what to do here, i'll probably use this when I start tracking what
        # the camera should be capturing, like to detect when objects were deleted
        pass
