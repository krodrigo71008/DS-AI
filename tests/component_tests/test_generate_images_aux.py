from utility.generate_images import rectangles_intersect

def test_rectangles_intersect():
    test_cases = [
        [[0, 0, 100, 100], [100, 100, 200, 200], True],
        [[0, 0, 200, 200], [100, 100, 200, 200], True],
        [[0, 0, 100, 100], [0, 0, 200, 200], True],
        [[0, 0, 100, 200], [0, 0, 200, 100], True],
        [[0, 0, 200, 200], [100, 100, 300, 300], True],
        [[0, 0, 200, 200], [0, 300, 200, 500], False],
        [[100, 100, 300, 200], [400, 100, 600, 200], False],
        [[100, 100, 300, 200], [150, 100, 350, 200], True],
    ]
    for test_case in test_cases:
        assert rectangles_intersect(test_case[0], test_case[1]) == test_case[2]