import math


class Point2d:
    def __init__(self, x1 : float, x2 : float):
        self.x1 = x1
        self.x2 = x2

    @classmethod
    def bottom_from_box(cls, box : tuple[int, int, int, int]):
        return cls(box[0], box[1]+box[3]//2)

    @classmethod
    def center_from_box(cls, box : tuple[int, int, int, int]):
        return cls(box[0], box[1])

    def __add__(self, other):
        return Point2d(self.x1 + other.x1, self.x2 + other.x2)

    def __sub__(self, other):
        return Point2d(self.x1 - other.x1, self.x2 - other.x2)

    def __mul__(self, number):
        return Point2d(self.x1*number, self.x2*number)

    def __truediv__(self, number):
        return Point2d(self.x1/number, self.x2/number)

    def distance(self, other) -> float:
        return math.sqrt((self.x1-other.x1)**2+(self.x2-other.x2)**2)

    def angle(self) -> float:
        # this returns a value between pi and -pi
        return math.atan2(self.x2, self.x1)

    def rotate(self, angle : float):
        """Rotate point around the origin by angle

        :param angle: angle in radians
        :type angle: float
        :return: rotated point
        :rtype: Point2d
        """
        return Point2d(self.x1*math.cos(angle) - self.x2*math.sin(angle), self.x1*math.sin(angle) + self.x2*math.cos(angle))

    def rotate_degrees(self, angle : float):
        """Rotate point around the origin by angle

        :param angle: angle in degrees
        :type angle: float
        :return: rotated point
        :rtype: Point2d
        """
        angle = angle/180*math.pi
        return Point2d(self.x1*math.cos(angle) - self.x2*math.sin(angle), self.x1*math.sin(angle) + self.x2*math.cos(angle))

    def __str__(self) -> str:
        return f"({self.x1:.2f}, {self.x2:.2f})"
