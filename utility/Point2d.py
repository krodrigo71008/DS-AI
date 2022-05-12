import math


class Point2d:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point2d(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point2d(self.x - other.x, self.y - other.y)

    def __mul__(self, number):
        return Point2d(self.x*number, self.y*number)

    def distance(self, other):
        return math.sqrt((self.x-other.x)**2+(self.y-other.y)**2)

    def angle(self):
        # this returns a value between pi and -pi
        return math.atan2(self.y, self.x)
