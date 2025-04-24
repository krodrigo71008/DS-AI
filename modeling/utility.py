import math

from perception.constants import SCREEN_SIZE
from modeling.constants import CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV, FOLLOW_HEIGHT
from utility.Point2d import Point2d

# positions are Point2d
def image_to_local_position(image_position : Point2d, 
        heading : float = CAMERA_HEADING, pitch : float = CAMERA_PITCH, distance : float = CAMERA_DISTANCE, 
        fov : float = FOV, follow_height : float = FOLLOW_HEIGHT) -> Point2d:
    """Converts the image position (2d image position) to a local global position (could be 3d, 
    but everything is on the ground)

    :param image_position: object position relative to the top left corner
    :type image_position: Point2d
    :param heading: camera heading
    :type heading: float
    :param pitch: camera pitch
    :type pitch: float
    :param distance: camera distance
    :type distance: float
    :param fov: camera FOV
    :type fov: float
    :param follow_height: game follow height
    :type follow_height: float
    :return: position in the world's coordinate system, but with the origin in the point in the screen center
    :rtype: Point2d
    """
    # f = H / (2*tan(AFOV/2)), f focal distance, H height, AFOV angular FOV
    f = SCREEN_SIZE["height"]/(2*math.tan(fov/180*math.pi/2))
    # in opencv, y points down and x points to the right, so in our coordinate system u is right and v is down
    u = image_position.x1 - SCREEN_SIZE["width"]/2
    v = image_position.x2 - SCREEN_SIZE["height"]/2
    heading = heading*math.pi/180
    pitch = pitch*math.pi/180
    sin_heading = math.sin(heading)
    cos_heading = math.cos(heading)
    sin_pitch = math.sin(pitch)
    cos_pitch = math.cos(pitch)
    temp = distance + follow_height*sin_pitch
    temp2 = distance*sin_pitch + follow_height
    temp3 = follow_height*f*cos_pitch
    temp4 = cos_pitch*v+f*sin_pitch
    world_x = (-sin_heading*temp2*u + cos_heading*temp*v - 
                temp3*cos_heading)/temp4
    world_z = (cos_heading*temp2*u + sin_heading*temp*v - 
                temp3*sin_heading)/temp4
    # in our world model, we'll use (x,z) as the two coordinates
    return Point2d(world_x, world_z)