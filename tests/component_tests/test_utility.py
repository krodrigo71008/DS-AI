from utility.utility import lines_cross, is_inside_convex_polygon
from utility.Point2d import Point2d

def test_lines_cross():
    test_cases = [
        [Point2d(0, 0), Point2d(1, 1), Point2d(2, 2), Point2d(3, 3), False],
        [Point2d(0, 0), Point2d(2, 2), Point2d(1, 1), Point2d(3, 3), True],
        [Point2d(0, 0), Point2d(1, 1), Point2d(1, 1), Point2d(3, 3), True],
        [Point2d(0, 0), Point2d(0, 1), Point2d(2, 0), Point2d(0, 2), False],
        [Point2d(0, 0), Point2d(2, 2), Point2d(0, 2), Point2d(2, 0), True],
        [Point2d(5, 7), Point2d(8, 9), Point2d(6, 7), Point2d(7, 9), True],
        [Point2d(5, 7), Point2d(6, 8), Point2d(-2, -2), Point2d(-1, -1), False],
        [Point2d(6, 6), Point2d(8, 8), Point2d(7, 7), Point2d(-10, -1), True],
    ]
    for test_case in test_cases:
        assert lines_cross(test_case[0], test_case[1], test_case[2], test_case[3]) == test_case[4]

def test_is_inside_convex_polygon():
    poly_1 = [Point2d(0, 0), Point2d(0, 2), Point2d(2, 2), Point2d(2, 0)]
    poly_2 = [Point2d(1, 1), Point2d(0, 2), Point2d(1, 3), Point2d(2, 2)]
    poly_3 = [Point2d(-3, -3), Point2d(-3, 2), Point2d(4, 2), Point2d(10, -3)]
    poly_4 = [Point2d(-1, -1), Point2d(1, 1), Point2d(3, 1), Point2d(5, -1)]
    test_cases = [
        [poly_1, Point2d(1, 1), True],
        [poly_1, Point2d(0, 1), True],
        [poly_1, Point2d(2, 2), True],
        [poly_1, Point2d(0, -1), False],
        [poly_1, Point2d(-1, -1), False],
        [poly_2, Point2d(1, 1), True],
        [poly_2, Point2d(0, 0), False],
        [poly_2, Point2d(-1, 2), False],
        [poly_2, Point2d(1, 2), True],
        [poly_2, Point2d(1.5, 1.5), True],
        [poly_3, Point2d(1.5, -3), True],
        [poly_3, Point2d(-4.5, -3), False],
        [poly_3, Point2d(1.5, 2), True],
        [poly_3, Point2d(10, 2), False],
        [poly_4, Point2d(-1, -1), True],
        [poly_4, Point2d(10, -1), False],
        [poly_4, Point2d(-2, -1), False],
        [poly_4, Point2d(10, 1), False],
        [poly_4, Point2d(-10, 1), False],
        [poly_4, Point2d(-1, 0), False],
        [poly_4, Point2d(0, 0), True],
        [poly_4, Point2d(1, 0), True],
        [poly_4, Point2d(3.5, 0), True],
    ]
    for test_case in test_cases:
        assert is_inside_convex_polygon(test_case[0], test_case[1]) == test_case[2]