import numpy as np
from PIL import Image, ImageFont, ImageDraw
from modeling.Modeling import Modeling
from modeling.PlayerModel import PlayerModel

from perception.screen import SCREEN_SIZE
from modeling.constants import CHUNK_SIZE, DISTANCE_FOR_SAME_OBJECT
from utility.Point2d import Point2d
from utility.utility import draw_annotations, get_multiples_in_range

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
    
    def draw_detected_objects(self, classes : list[int], scores : list[float], boxes : tuple[int, int, int, int]) -> None:
        """Draw detected objects

        :param classes: list of identified classes
        :type classes: list[int]
        :param scores: estimated accuracy for each object
        :type scores: list[float]
        :param boxes: bounding boxes for each object
        :type boxes: list[list[int]]
        """
        np_image = np.asarray(self.perception_image)
        res, _ = draw_annotations(np_image, classes, scores, boxes)
        res_image = Image.fromarray(res, mode="RGB")
        res_image = res_image.resize((SCREEN_SIZE["width"]//2, SCREEN_SIZE["height"]//2))
        self.image.paste(res_image, (SCREEN_SIZE["width"]//2, SCREEN_SIZE["height"]//2))
        # mark the perception image center
        draw = ImageDraw.Draw(self.image)
        draw.text((SCREEN_SIZE["width"]//2 + SCREEN_SIZE["width"]//4, SCREEN_SIZE["height"]//2+SCREEN_SIZE["height"]//4), 
            "O", fill="red", font=self.font, anchor="mm")
    
    def update_world_model(self, modeling : Modeling) -> None:
        """Update world model

        :param modeling: modeling
        :type modeling: Modeling
        """
        objects = modeling.world_model.object_lists
        player = modeling.player_model
        vision_corners = (modeling.world_model.c1, modeling.world_model.c2, modeling.world_model.c3, modeling.world_model.c4)
        deletion_corners = (modeling.world_model.c1_deletion_border,
                            modeling.world_model.c2_deletion_border,
                            modeling.world_model.c3_deletion_border, 
                            modeling.world_model.c4_deletion_border)
        origin_coordinates = modeling.world_model.origin_coordinates
        recent_objects = modeling.world_model.recent_objects
        estimation_pairs = modeling.world_model.estimation_pairs
        draw = ImageDraw.Draw(self.image)
        # draw outline
        draw.rectangle((0, 0, 
                        self.WORLD_CANVAS_WIDTH, self.WORLD_CANVAS_HEIGHT), 
                        outline="red")
        world_objects : list[tuple[str, Point2d]] = []
        for name, object_list in objects.items():
            if name == "Grass":
                for obj in object_list:
                    world_objects.append(("Grass", obj.position))
            if name == "Sapling":
                for obj in object_list:
                    world_objects.append(("Sapling", obj.position))
        player_position = player.position
        player_position_no_corrections = player.position_before_correction
        new_recent_obj = [(type(obj_pair[0]).__name__, obj_pair[0].position) for obj_pair in recent_objects]
        self.draw_world_model(world_objects, player_position, player_position_no_corrections,
                                vision_corners, deletion_corners, origin_coordinates, 
                                new_recent_obj, estimation_pairs)

    def draw_world_model(self, world_objects : list[tuple[str, Point2d]], player_position : Point2d, player_position_no_corrections : Point2d,
                            vision_corners : tuple[Point2d, Point2d, Point2d, Point2d], 
                            deletion_corners : tuple[Point2d, Point2d, Point2d, Point2d], 
                            origin_coordinates : Point2d, recent_objects : list[tuple[str, Point2d]], 
                            estimation_pairs : list[tuple[str, Point2d, Point2d]]) -> None:
        """Draw world model

        :param world_objects: list of relevant world objects
        :type world_objects: list[tuple[str, Point2d]]
        :param player_position: player position before corrections
        :type player_position: Point2d
        :param player_position_no_corrections: player position after corrections
        :type player_position_no_corrections: Point2d
        :param vision_corners: region currently on screen
        :type vision_corners: tuple[Point2d, Point2d, Point2d, Point2d]
        :param deletion_corners: region that is being considered for deletion
        :type deletion_corners: tuple[Point2d, Point2d, Point2d, Point2d]
        :param origin_coordinates: origin coordinates
        :type origin_coordinates: Point2d
        :param recent_objects: objects that have been detected but not yet added to the world model
        :type recent_objects: list[tuple[str, Point2d]]
        :param estimation_pairs: list of tuples of object name, estimated position and model position
        :type estimation_pairs: list[tuple[str, Point2d, Point2d]]
        """
        if player_position is not None:
            x1_range = (player_position.x1 - self.CLOSE_OBJECTS_X1/2, player_position.x1 + self.CLOSE_OBJECTS_X1/2)
            x2_range = (player_position.x2 - self.CLOSE_OBJECTS_X2/2, player_position.x2 + self.CLOSE_OBJECTS_X2/2)
            # estimation_pair is (estimate, position in modeling)
            # yellow for estimates
            for name, estimate, model_position in estimation_pairs:
                if estimate.x1 > x1_range[0] and estimate.x1 < x1_range[1] and estimate.x2 > x2_range[0] and estimate.x2 < x2_range[1]:
                    if name == "Grass":
                        self.write_canvas(estimate.x1, estimate.x2, x1_range, x2_range, "G", "dimgray")
                    elif name == "Sapling":
                        self.write_canvas(estimate.x1, estimate.x2, x1_range, x2_range, "S", "dimgray")
                    self.draw_line_world_canvas(estimate.x1, estimate.x2, model_position.x1, model_position.x2, x1_range, x2_range)
            # black for objects in world model
            for name, position in world_objects:
                if position.x1 > x1_range[0] and position.x1 < x1_range[1] and position.x2 > x2_range[0] and position.x2 < x2_range[1]:
                    if name == "Grass":
                        self.write_canvas(position.x1, position.x2, x1_range, x2_range, "G", "black")
                    elif name == "Sapling":
                        self.write_canvas(position.x1, position.x2, x1_range, x2_range, "S", "black")
            # blue for recent objects
            for name, position in recent_objects:
                if position.x1 > x1_range[0] and position.x1 < x1_range[1] and position.x2 > x2_range[0] and position.x2 < x2_range[1]:
                    if name == "Grass":
                        self.write_canvas(position.x1, position.x2, x1_range, x2_range, "G", "blue")
                    elif name == "Sapling":
                        self.write_canvas(position.x1, position.x2, x1_range, x2_range, "S", "blue")

            # player position related
            self.write_canvas(player_position_no_corrections.x1, player_position_no_corrections.x2, x1_range, x2_range, "P", "dimgray")
            self.write_canvas(player_position.x1, player_position.x2, x1_range, x2_range, "P", "black")
            self.draw_line_world_canvas(player_position.x1, player_position.x2, 
                                        player_position_no_corrections.x1, player_position_no_corrections.x2, 
                                        x1_range, x2_range)

            self.write_canvas(origin_coordinates.x1 ,origin_coordinates.x2,  x1_range, x2_range, "O", "red")
            self.draw_quadrilateral_world_canvas(vision_corners, x1_range, x2_range, "black")
            self.draw_quadrilateral_world_canvas(deletion_corners, x1_range, x2_range, "red")
            self.draw_chunk_lines_world_canvas(CHUNK_SIZE, x1_range, x2_range)

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
        draw.text((center_x, center_y), "O", fill="red", font=self.font, anchor="mm")

    def draw_line_world_canvas(self, p1_x1, p1_x2, p2_x1, p2_x2, x1_range, x2_range):
        conv_est_x, conv_est_y = self.convert_world_coords_to_world_graph(p1_x1, p1_x2, x1_range, x2_range)
        conv_mod_x, conv_mod_y = self.convert_world_coords_to_world_graph(p2_x1, p2_x2, x1_range, x2_range)
        draw = ImageDraw.Draw(self.image)
        draw.line((conv_est_x, conv_est_y, conv_mod_x, conv_mod_y), fill="dimgray")

    def convert_world_coords_to_world_graph(self, x1, x2, x1_range, x2_range):
        x = (x2 - x2_range[0])/self.CLOSE_OBJECTS_X2*self.WORLD_CANVAS_WIDTH
        y = (x1 - x1_range[0])/self.CLOSE_OBJECTS_X1*self.WORLD_CANVAS_HEIGHT
        return x, y
    
    def draw_chunk_lines_world_canvas(self, chunk_size, x1_range, x2_range):
        x1_lines = get_multiples_in_range(chunk_size, x1_range)
        x2_lines = get_multiples_in_range(chunk_size, x2_range)
        draw = ImageDraw.Draw(self.image)
        for x1 in x1_lines:
            # x1 is y in the graph
            _, y = self.convert_world_coords_to_world_graph(x1, 0, x1_range, x2_range)
            draw.line((0, y, self.WORLD_CANVAS_WIDTH, y), fill="blue")
        for x2 in x2_lines:
            # x2 is x in the graph
            x, _ = self.convert_world_coords_to_world_graph(0, x2, x1_range, x2_range)
            draw.line((x, 0, x, self.WORLD_CANVAS_HEIGHT), fill="blue")

    def draw_quadrilateral_world_canvas(self, vertices, x1_range, x2_range, color):
        p1_x, p1_y = self.convert_world_coords_to_world_graph(vertices[0].x1, vertices[0].x2, x1_range, x2_range)
        p2_x, p2_y = self.convert_world_coords_to_world_graph(vertices[1].x1, vertices[1].x2, x1_range, x2_range)
        p3_x, p3_y = self.convert_world_coords_to_world_graph(vertices[2].x1, vertices[2].x2, x1_range, x2_range)
        p4_x, p4_y = self.convert_world_coords_to_world_graph(vertices[3].x1, vertices[3].x2, x1_range, x2_range)
        draw = ImageDraw.Draw(self.image)
        draw.polygon([p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, p4_x, p4_y], outline=color)

    def export_results(self, output_path : str):
        self.image.save(output_path)
        self.image = Image.new(mode="RGB", size=(SCREEN_SIZE["width"], SCREEN_SIZE["height"]), color="white")

    def write_canvas(self, x1, x2, x1_range, x2_range, text, color):
        x, y = self.convert_world_coords_to_world_graph(x1, x2, x1_range, x2_range)
        draw = ImageDraw.Draw(self.image)
        draw.text((x, y), text, fill=color, font=self.font, anchor="mm")