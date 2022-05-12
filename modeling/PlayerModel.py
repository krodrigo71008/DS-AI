from modeling.Inventory import Inventory
from utility.Point2d import Point2d
from modeling.constants import PLAYER_BASE_SPEED, BASE_SPEED_MODIFIER

NONE = 0
LEFT = 1
UP_LEFT = 2
UP = 3
UP_RIGHT = 4
RIGHT = 5
DOWN_RIGHT = 6
DOWN = 7
DOWN_LEFT = 8


class PlayerModel:
    def __init__(self, clock):
        self.position = Point2d(0, 0)
        self.clock = clock
        self.inventory = Inventory()
        self.health = 150
        self.max_health = 150
        self.hunger = 150
        self.max_hunger = 150
        self.sanity = 200
        self.max_sanity = 200
        self.speed = 6
        self.direction = NONE

    def move(self, dt):
        if self.direction == NONE:
            pass
        elif self.direction == LEFT:
            self.position += Point2d(-1, 0)*dt*PLAYER_BASE_SPEED*self.speed/BASE_SPEED_MODIFIER
        elif self.direction == UP_LEFT:
            self.position += Point2d(-1/1.4142135, 1/1.4142135)*dt*PLAYER_BASE_SPEED*self.speed/BASE_SPEED_MODIFIER
        elif self.direction == UP:
            self.position += Point2d(0, 1)*dt*PLAYER_BASE_SPEED*self.speed/BASE_SPEED_MODIFIER
        elif self.direction == UP_RIGHT:
            self.position += Point2d(1/1.4142135, 1/1.4142135)*dt*PLAYER_BASE_SPEED*self.speed/BASE_SPEED_MODIFIER
        elif self.direction == RIGHT:
            self.position += Point2d(1, 0)*dt*PLAYER_BASE_SPEED*self.speed/BASE_SPEED_MODIFIER
        elif self.direction == DOWN_RIGHT:
            self.position += Point2d(1/1.4142135, -1/1.4142135)*dt*PLAYER_BASE_SPEED*self.speed/BASE_SPEED_MODIFIER
        elif self.direction == DOWN:
            self.position += Point2d(0, -1)*dt*PLAYER_BASE_SPEED*self.speed/BASE_SPEED_MODIFIER
        elif self.direction == DOWN_LEFT:
            self.position += Point2d(-1/1.4142135, -1/1.4142135)*dt*PLAYER_BASE_SPEED*self.speed/BASE_SPEED_MODIFIER

    def set_direction(self, direction):
        if direction == "none":
            self.direction = NONE
        elif direction == "left":
            self.direction = LEFT
        elif direction == "up_left":
            self.direction = UP_LEFT
        elif direction == "up":
            self.direction = UP
        elif direction == "up_right":
            self.direction = UP_RIGHT
        elif direction == "right":
            self.direction = RIGHT
        elif direction == "down_right":
            self.direction = DOWN_RIGHT
        elif direction == "down":
            self.direction = DOWN
        elif direction == "down_left":
            self.direction = DOWN_LEFT

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
