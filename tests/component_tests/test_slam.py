import math
import random

from modeling.Modeling import Modeling


def test_slam_predict_control():
    modeling = Modeling()
    directions = [None, math.pi/4, math.pi/2, 3*math.pi/4, math.pi, -math.pi/4, -math.pi/2, -3*math.pi/4]
    for direction in directions:
        modeling.set_direction(direction)
        xEst_before = modeling.xEst.copy()
        dt = 0.05 + random.random()*0.1
        modeling.slam_predict(dt)
        xEst_after = modeling.xEst.copy()
        difference = xEst_after - xEst_before
        if direction is None:
            assert difference.max() == 0
        else:
            angle = math.atan2(difference[1, 0], difference[0, 0])
            distance = math.sqrt(difference[0, 0]**2 + difference[1, 0]**2)
            assert (angle - direction) < 1e-6
            assert (distance/modeling.DEFAULT_SPEED - dt) < 1e-6
