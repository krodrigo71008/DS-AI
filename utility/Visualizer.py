import numpy as np
from PIL import Image, ImageFont, ImageDraw

from perception.screen import SCREEN_SIZE
from modeling.constants import CHUNK_SIZE, DISTANCE_FOR_SAME_OBJECT
from utility.Point2d import Point2d
from utility.utility import draw_annotations

class Visualizer:
    # reminder that the two below this are in in-game units
    CLOSE_OBJECTS_X1 = 75
    CLOSE_OBJECTS_X2 = 75
    # reminder that the two below this are in pixels
    WORLD_CANVAS_WIDTH = 600
    WORLD_CANVAS_HEIGHT = 600
    # reminder that the two below this are in pixels
    ERROR_CANVAS_WIDTH = 200
    ERROR_CANVAS_HEIGHT = 200
    # max length in pixels of the visual representation of the error
    MAX_ERROR_LENGTH = ERROR_CANVAS_WIDTH//2
    def __init__(self) -> None:
        self.image = Image.new(mode="RGB", size=(SCREEN_SIZE["width"], SCREEN_SIZE["height"]), color="white")
        self.perception_image = None
        self.font = ImageFont.truetype("arial.ttf", 20)
    
    def update_image(self, image : np.array) -> None:
        """Updates the image part of the visualization screen

        :param image: Image in BGR
        :type image: np.array
        """
        # converting BGR to RGB
        img = Image.fromarray(image[:, :, ::-1])
        self.perception_image = img
    
    def draw_detected_objects(self, classes, scores, boxes):
        np_image = np.asarray(self.perception_image)
        res, _ = draw_annotations(np_image, classes, scores, boxes)
        res_image = Image.fromarray(res, mode="RGB")
        res_image = res_image.resize((SCREEN_SIZE["width"]//2, SCREEN_SIZE["height"]//2))
        self.image.paste(res_image, (SCREEN_SIZE["width"]//2, SCREEN_SIZE["height"]//2))
        # mark the perception image center
        draw = ImageDraw.Draw(self.image)
        draw.text((SCREEN_SIZE["width"]//2 + SCREEN_SIZE["width"]//4, SCREEN_SIZE["height"]//2+SCREEN_SIZE["height"]//4), 
            "O", fill="red", font=self.font, anchor="mm")
    
    def update_world_model(self, objects, player, vision_corners, origin_coordinates):
        draw = ImageDraw.Draw(self.image)
        # draw outline
        draw.rectangle((0, 0, 
                        self.WORLD_CANVAS_WIDTH, self.WORLD_CANVAS_HEIGHT), 
                        outline="red")
        world_objects = []
        for name, object_list in objects.items():
            if name == "Grass":
                for obj in object_list:
                    world_objects.append(("Grass", obj.position))
            if name == "Sapling":
                for obj in object_list:
                    world_objects.append(("Sapling", obj.position))
        player_position = player.position
        self.draw_world_model(world_objects, player_position, vision_corners, origin_coordinates)

    def draw_world_model(self, world_objects, player_position, vision_corners, origin_coordinates):
        if player_position is not None:
            x1_range = (player_position.x1 - self.CLOSE_OBJECTS_X1/2, player_position.x1 + self.CLOSE_OBJECTS_X1/2)
            x2_range = (player_position.x2 - self.CLOSE_OBJECTS_X2/2, player_position.x2 + self.CLOSE_OBJECTS_X2/2)
            for name, position in world_objects:
                if position.x1 > x1_range[0] and position.x1 < x1_range[1] and position.x2 > x2_range[0] and position.x2 < x2_range[1]:
                    if name == "Grass":
                        self.write_canvas(position.x1, position.x2, x1_range, x2_range, "G", "black")
                    elif name == "Sapling":
                        self.write_canvas(position.x1, position.x2, x1_range, x2_range, "S", "black")
            self.write_canvas(player_position.x1, player_position.x2, x1_range, x2_range, "P", "black")
            self.write_canvas(origin_coordinates.x1 ,origin_coordinates.x2,  x1_range, x2_range, "O", "red")
            self.player_position = None
            self.world_objects = []
            self.draw_quadrilateral(vision_corners, x1_range, x2_range)
            self.draw_chunk_lines(CHUNK_SIZE, x1_range, x2_range)

    def draw_estimation_errors(self, estimation_errors : list[Point2d]):
        draw = ImageDraw.Draw(self.image)
        corner_start_x = 200
        corner_start_y = 800
        # draw outline
        draw.rectangle((corner_start_x, corner_start_y, 
                        corner_start_x+self.ERROR_CANVAS_WIDTH, corner_start_y+self.ERROR_CANVAS_HEIGHT), 
                        outline="black")
        draw.arc((corner_start_x, corner_start_y, 
                        corner_start_x+self.ERROR_CANVAS_WIDTH, corner_start_y+self.ERROR_CANVAS_HEIGHT),
                        0, 360, fill="blue", width=1)
        center_x = corner_start_x + self.ERROR_CANVAS_WIDTH//2
        center_y = corner_start_y + self.ERROR_CANVAS_HEIGHT//2
        for error in estimation_errors:
            draw.line((center_x, center_y, 
                    center_x+error.x2*self.MAX_ERROR_LENGTH/DISTANCE_FOR_SAME_OBJECT, 
                    center_y+error.x1*self.MAX_ERROR_LENGTH/DISTANCE_FOR_SAME_OBJECT), fill="black", width=2)



    def _get_multiples_in_range(self, number : int, range_ : tuple[int, int]) -> list[int]:
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

    def convert_world_coords_to_world_graph(self, x1, x2, x1_range, x2_range):
        x = (x2 - x2_range[0])/self.CLOSE_OBJECTS_X2*self.WORLD_CANVAS_WIDTH
        y = (x1 - x1_range[0])/self.CLOSE_OBJECTS_X1*self.WORLD_CANVAS_HEIGHT
        return x, y
    
    def draw_chunk_lines(self, chunk_size, x1_range, x2_range):
        x1_lines = self._get_multiples_in_range(chunk_size, x1_range)
        x2_lines = self._get_multiples_in_range(chunk_size, x2_range)
        draw = ImageDraw.Draw(self.image)
        for x1 in x1_lines:
            # x1 is y in the graph
            _, y = self.convert_world_coords_to_world_graph(x1, 0, x1_range, x2_range)
            draw.line((0, y, self.WORLD_CANVAS_WIDTH, y), fill="blue")
        for x2 in x2_lines:
            # x2 is x in the graph
            x, _ = self.convert_world_coords_to_world_graph(0, x2, x1_range, x2_range)
            draw.line((x, 0, x, self.WORLD_CANVAS_HEIGHT), fill="blue")

    def draw_quadrilateral(self, vertices, x1_range, x2_range):
        p1_x, p1_y = self.convert_world_coords_to_world_graph(vertices[0].x1, vertices[0].x2, x1_range, x2_range)
        p2_x, p2_y = self.convert_world_coords_to_world_graph(vertices[1].x1, vertices[1].x2, x1_range, x2_range)
        p3_x, p3_y = self.convert_world_coords_to_world_graph(vertices[2].x1, vertices[2].x2, x1_range, x2_range)
        p4_x, p4_y = self.convert_world_coords_to_world_graph(vertices[3].x1, vertices[3].x2, x1_range, x2_range)
        draw = ImageDraw.Draw(self.image)
        draw.polygon([p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, p4_x, p4_y], outline="black")

    def export_results(self, output_path : str):
        self.image.save(output_path)
        self.image = Image.new(mode="RGB", size=(SCREEN_SIZE["width"], SCREEN_SIZE["height"]), color="white")

    def write_canvas(self, x1, x2, x1_range, x2_range, text, color):
        x, y = self.convert_world_coords_to_world_graph(x1, x2, x1_range, x2_range)
        draw = ImageDraw.Draw(self.image)
        draw.text((x, y), text, fill=color, font=self.font, anchor="mm")