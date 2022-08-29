import math

def clamp2pi(angle: float) -> float:
    """Normalizes an angle so its value is between -pi and pi (including both ends)

    :param angle: angle in radians to be normalized
    :type angle: float
    :return: angle in radians in interval [-pi, pi]
    :rtype: float
    """
    while angle > math.pi:
        angle -= 2*math.pi
    
    while angle < -math.pi:
        angle += 2*math.pi
    
    return angle