import math
import random

from utility.Point2d import Point2d

def test_point2d():
    random.seed(727)
    def points_equal(p1 : Point2d, p2 : Point2d):
        return p1.distance(p2) < 1e-4
    
    for _ in range(10):
        x = random.random()*20
        y = random.random()*20
        p = Point2d(x, y)
        res = p.rotate(math.pi/2)
        assert points_equal(res, Point2d(-y, x))
        res = res.rotate(math.pi/2)
        assert points_equal(res, Point2d(-x, -y))
        res = res.rotate(math.pi/2)
        assert points_equal(res, Point2d(y, -x))
        res = res.rotate(math.pi/2)
        assert points_equal(res, Point2d(x, y))

        res = p.rotate_degrees(90)
        assert points_equal(res, Point2d(-y, x))
        res = res.rotate_degrees(90)
        assert points_equal(res, Point2d(-x, -y))
        res = res.rotate_degrees(90)
        assert points_equal(res, Point2d(y, -x))
        res = res.rotate_degrees(90)
        assert points_equal(res, Point2d(x, y))
    
    for _ in range(10):
        x = random.random()*20
        y = random.random()*20
        p = Point2d(x, y)
        angle = random.random()*2*math.pi
        assert abs(p.rotate(angle).distance(Point2d(0, 0)) - p.distance(Point2d(0, 0))) < 1e-4
        angle = random.random()*360
        assert abs(p.rotate_degrees(angle).distance(Point2d(0, 0)) - p.distance(Point2d(0, 0))) < 1e-4
    
    for _ in range(10):
        p = Point2d(1, 0)
        angle = random.random()*2*math.pi - math.pi
        assert abs(p.rotate(angle).angle() - angle) < 1e-4
