import math

from PIL import Image, ImageDraw
import numpy as np
import cv2

from perception.classes import get_class_names
from utility.Point2d import Point2d

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
    limits = [(0, 190, 65, 890), (420, 1010, 1500, 1080), (1680, 0, 1920, 290), (1780, 950, 1920, 1080)]
    draw = ImageDraw.Draw(image)
    for limit in limits:
        draw.rectangle(limit, fill=0)
    del draw
    return image

def hide_huds_and_player(image : Image) -> Image:
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
        
def on_segment_collinear(p1 : Point2d, p2 : Point2d, p3 : Point2d) -> bool:
    """Checks whether p2 is on the segment p1-p3, given that all three points are collinear

    :param p1: point 1
    :type p1: Point2d
    :param p2: point 2
    :type p2: Point2d
    :param p3: point 3
    :type p3: Point2d
    :return: whether p2 is between p1 and p3
    :rtype: bool
    """
    if (p2.x1 <= max(p1.x1, p3.x1) and p2.x1 >= min(p1.x1, p3.x1) and
            p2.x2 <= max(p1.x2, p3.x2) and p2.x2 >= min(p1.x2, p3.x2)):
        return True
    return False
    
def orientation(p1 : Point2d, p2 : Point2d, p3 : Point2d) -> int:
    """Returns orientation of the ordered three points (p1, p2, p3)

    :param p1: point 1
    :type p1: Point2d
    :param p2: point 2
    :type p2: Point2d
    :param p3: point 3
    :type p3: Point2d
    :return: int representing orientation, 0 for collinear, 1 for clockwise and 2 for counterclockwise
    :rtype: bool
    """
    val = (p2.x2 - p1.x2) * (p3.x1 - p2.x1) - (p2.x1 - p1.x1) * (p3.x2 - p2.x2)
    if abs(val) < 1e-4:
        return 0
    elif val > 0:
        return 1
    else:
        # val < 0
        return 2
    
def lines_cross(p1 : Point2d, q1 : Point2d, p2 : Point2d, q2 : Point2d):
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # General case
    if ((o1 != o2) and (o3 != o4)):
        return True
  
    # Special Cases
  
    # p1 , q1 and p2 are collinear and p2 lies on segment p1q1
    if ((o1 == 0) and on_segment_collinear(p1, p2, q1)):
        return True
  
    # p1 , q1 and q2 are collinear and q2 lies on segment p1q1
    if ((o2 == 0) and on_segment_collinear(p1, q2, q1)):
        return True
  
    # p2 , q2 and p1 are collinear and p1 lies on segment p2q2
    if ((o3 == 0) and on_segment_collinear(p2, p1, q2)):
        return True
  
    # p2 , q2 and q1 are collinear and q1 lies on segment p2q2
    if ((o4 == 0) and on_segment_collinear(p2, q1, q2)):
        return True
  
    # If none of the cases
    return False

def is_inside_convex_polygon(points: list[Point2d], p: Point2d) -> bool:
    """Checks whether a point is inside the polygon described by points

    :param points: points describing polygon
    :type points: list[Point2d]
    :param p: point to check
    :type p: Point2d
    :return: whether the point is inside the polygon
    :rtype: bool
    """
    n = len(points)
     
    # There must be at least 3 vertices
    # in polygon
    if n < 3:
        return False
     
    i = 0
    while True:
        next = (i + 1) % n
        next_2 = (next + 1) % n

        if next_2 == 0:
            break

        if i == 0:
            if orientation(points[i], p, points[next]) == 0:
                return on_segment_collinear(points[i], p, points[next])
        
        if orientation(points[next], p, points[next_2]) == 0:
            return on_segment_collinear(points[next], p, points[next_2])

        if orientation(points[i], p, points[next]) != orientation(points[next], p, points[next_2]):
            return False
             
        i = next
     
    # Return true if count is odd, false otherwise
    return True

def get_multiples_in_range(number : int, range_ : tuple[int, int]) -> list[int]:
    """Get multiples of number inside the range range_

    :param number: number to find multiples of
    :type number: int
    :param range_: range to filter multiples
    :type range_: tuple[int, int]
    :return: list of multiples inside the given range
    :rtype: list[int]
    """
    aux_ = round(range_[0]/number)*number
    ans = []
    while aux_ < range_[1]:
        ans.append(aux_)
        aux_ += number
    return ans

def draw_annotations(image : np.array, classes : list[int], scores : list[float], boxes : list[list[int]]) -> tuple[np.array, list[str]]:
    """Draws (into image) annotations described by classes, scores and boxes

    :param image: image to be modified
    :type image: np.array
    :param classes: list of identified classes
    :type classes: list[int]
    :param scores: estimated accuracy for each object
    :type scores: list[float]
    :param boxes: bounding boxes for each object
    :type boxes: list[list[int]]
    :return: resulting image and list of strings with information for each object
    :rtype: tuple[np.array, list[str]]
    """
    class_names = get_class_names()
    color = (255, 0, 0)

    image_result = np.copy(image)
    results = []
    for class_id, score, box in zip(classes, scores, boxes):
        results.append('%s %f %f %f %f %f\n' % (class_names[class_id], score, box[0], box[1], box[0] + box[2],
                                                     box[1] + box[3]))
        
        label = "%s: %f" % (class_names[class_id], score)
        cv2.rectangle(image_result, box, color, 2)
        cv2.putText(image_result, label, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return image_result, results
    