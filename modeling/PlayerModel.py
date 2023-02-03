import math
from modeling.Inventory import Inventory
from utility.Clock import Clock
from utility.Point2d import Point2d
from modeling.constants import PLAYER_BASE_SPEED


class PlayerModel:
    def __init__(self, clock : Clock):
        self.position : Point2d = Point2d(0, 0)
        self.position_before_correction : Point2d = Point2d(0, 0)
        self.clock : Clock = clock
        self.inventory = Inventory()
        self.health = 150
        self.max_health = 150
        self.hunger = 150
        self.max_hunger = 150
        self.sanity = 200
        self.max_sanity = 200
        self.speed = PLAYER_BASE_SPEED
        # direction in radians
        self.direction : float = None
        self.CORRECTION_GAIN = 0.9

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

    def update(self) -> None:
        self.inventory.update(self.clock.dt())
        self.move(self.clock.dt())
        self.hunger -= self.clock.dt()*75/480
        day_section = self.clock.day_section()
        if day_section == "Dusk" or day_section == "Night":
            self.sanity -= self.clock.dt()*5/60

    def correct_error(self, err : Point2d) -> None:
        self.position_before_correction = self.position
        self.position -= err*self.CORRECTION_GAIN
