from perception.screen import SCREEN_SIZE
from utility.Point2d import Point2d


class ImageObject:
    def __init__(self, class_id, score, box, player_position):
        self.id = class_id
        self.score = score
        self.box = box
        self.player_position = player_position

    def position_from_player(self):
        # converting opencv coordinates to a coordinate system with (0,0) on the center of the screen,
        # x to the right and y up
        return Point2d(self.box[0] + self.box[2]//2 - self.player_position.x,
                       -(self.box[1] + self.box[3]//2 - self.player_position.y))
