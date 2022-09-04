import math

from PIL import Image, ImageDraw

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

def hide_huds(image : Image) -> Image:
    """_summary_

    :param image: input image
    :type image: Image
    :return: output image
    :rtype: Image
    """
    limits = [(0, 190, 65, 890), (420, 1010, 1500, 1080), (850, 410, 1065, 665), (1680, 0, 1920, 290), (1780, 950, 1920, 1080)]
    draw = ImageDraw.Draw(image)
    for limit in limits:
        draw.rectangle(limit, fill=0)
    del draw
    return image