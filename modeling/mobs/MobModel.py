from utility.Point2d import Point2d
from modeling.constants import TIME_FOR_MOB_REMOVAL


class MobModel:
    def __init__(self, position, id_, name):
        self.position = position
        self.id = id_
        self.name = name
        self.destroy_time = TIME_FOR_MOB_REMOVAL

    def set_position(self, x, z):
        self.position = Point2d(x, z)

    def update(self, change):
        pass

    def refresh_destruction_time(self):
        self.destroy_time = TIME_FOR_MOB_REMOVAL

    def update_destruction_time(self, dt):
        self.destroy_time -= dt
        return self.destroy_time > 0
