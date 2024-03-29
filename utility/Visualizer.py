import numpy as np
from PIL import Image, ImageFont, ImageDraw

from modeling.Modeling import Modeling
from modeling.objects.ObjectModel import ObjectModel
from modeling.ObjectsInfo import objects_info
from perception.constants import SCREEN_SIZE, SEGMENTATION_INPUT_SIZE
from modeling.constants import CHUNK_SIZE, DISTANCE_FOR_SAME_OBJECT, TILE_SIZE
from modeling.TerrainTile import TerrainTile
from utility.Point2d import Point2d
from utility.utility import draw_annotations, get_multiples_in_range, get_color_representation_dict

class Visualizer:
    # things we want here:
    # latest yolo output (highlighted when new)
    # latest segmentation output (highlighted when new)
    # time
    # explored chunks (chunks have black borders)
    # objects in world (represented by obj_id in black)
    # objects detected this cycle (represented by obj_id in orange)
    # objects detected recently (represented by obj_id in blue)
    # cycles since player detected
    # area currently on screen (brown trapezoid)
    # deletion border (red trapezoid)
    # position errors (detected position in gray, position in model in black, as said before)
    # avg error
    # tiles (tiles have gray borders)
    
    # reminder that the two below this are in in-game units
    CLOSE_OBJECTS_X1 = 75
    CLOSE_OBJECTS_X2 = 75
    # reminder that the two below this are in pixels
    WORLD_CANVAS_WIDTH = 500
    WORLD_CANVAS_HEIGHT = 500
    # reminder that the two below this are in pixels
    TILES_CANVAS_WIDTH = 300
    TILES_CANVAS_HEIGHT = 300
    # reminder that the two below this are in pixels
    ERROR_CANVAS_WIDTH = 200
    ERROR_CANVAS_HEIGHT = 200
    # max length in pixels of the visual representation of the error
    MAX_ERROR_LENGTH = ERROR_CANVAS_WIDTH//2
    def __init__(self) -> None:
        self.image = Image.new(mode="RGB", size=(SCREEN_SIZE["width"], SCREEN_SIZE["height"]), color="white")
        self.perception_image = None
        self.segmentation_image = None
        self.font = ImageFont.truetype("arial.ttf", 20)
        self.segmentation_color_dict = get_color_representation_dict()
        self.segmentation_palette = [0]*256*3
        for c, color_info in self.segmentation_color_dict.items():
            if color_info[0] is not None:
                self.segmentation_palette[c*3:c*3+3] = color_info[0] # [0] is array, [1] is hex representation
        self.yolo_border = (SCREEN_SIZE["width"]//2, 0, SCREEN_SIZE["width"], SCREEN_SIZE["height"]//2)
        self.segmentation_border = (SCREEN_SIZE["width"]//2, SCREEN_SIZE["height"]//2, SCREEN_SIZE["width"], SCREEN_SIZE["height"])
        self.warped_position = (SCREEN_SIZE["width"]//2-SEGMENTATION_INPUT_SIZE[0]-30, SCREEN_SIZE["height"]-SEGMENTATION_INPUT_SIZE[1]-30)
        self.time_ = 0
        self.time_position = (SCREEN_SIZE["width"]//2-50, 30)
        self.player_position_position = (SCREEN_SIZE["width"]//2-150, 100)
        self.player_direction_position = (SCREEN_SIZE["width"]//2-150, 200)
        self.tiles_position = (self.WORLD_CANVAS_WIDTH+50, 50)
        self.error_position = (SCREEN_SIZE["width"]//20, SCREEN_SIZE["height"]//2+250)
        self.draw = ImageDraw.Draw(self.image)
        self.last_yolo_image = None
        self.last_segmentation_image = None
        self.last_warped_image = None
    
    def update_yolo_image(self, image : np.array) -> None:
        """Updates the yolo image part of the visualization screen

        :param image: yolo input in BGR
        :type image: np.array
        """
        # converting BGR to RGB
        self.perception_image = image[:, :, ::-1]
    
    def draw_detected_objects(self, classes : list[int], scores : list[float], boxes : tuple[int, int, int, int]) -> None:
        """Draw detected objects

        :param classes: list of identified classes
        :type classes: list[int]
        :param scores: estimated accuracy for each object
        :type scores: list[float]
        :param boxes: bounding boxes for each object
        :type boxes: list[list[int]]
        """
        yolo_size = (self.yolo_border[2] - self.yolo_border[0], self.yolo_border[3] - self.yolo_border[1])
        np_image = self.perception_image
        res, _ = draw_annotations(np_image, classes, scores, boxes)
        res_image = Image.fromarray(res, mode="RGB")
        res_image = res_image.resize(yolo_size)
        self.last_yolo_image = res_image
        self.image.paste(res_image, (self.yolo_border[0], self.yolo_border[1]))
        # mark the perception image center
        self.draw.text((self.yolo_border[0]+yolo_size[0]//2, self.yolo_border[1]+yolo_size[1]//2), 
            "+", fill="red", font=self.font, anchor="mm")
        self.draw.rectangle(self.yolo_border, outline="green", width=3)
    
    def redraw_detected_objects(self) -> None:
        yolo_size = (self.yolo_border[2] - self.yolo_border[0], self.yolo_border[3] - self.yolo_border[1])
        self.image.paste(self.last_yolo_image, (self.yolo_border[0], self.yolo_border[1]))
        # mark the perception image center
        self.draw.text((self.yolo_border[0]+yolo_size[0]//2, self.yolo_border[1]+yolo_size[1]//2), 
            "+", fill="red", font=self.font, anchor="mm")

    def update_segmentation_image(self, image : np.array) -> None:
        """Updates the segmentation image part of the visualization screen

        :param image: segmentation input in RGB
        :type image: np.array
        """
        self.segmentation_image = Image.fromarray(image)
    
    def draw_segmentation_results(self, results : np.array) -> None:
        """Draw segmentation results

        :param results: segmentation output
        :type results: np.array
        """
        segmentation_size = (SCREEN_SIZE["width"]//2, SCREEN_SIZE["height"]//2)
        classes_image = Image.fromarray(results.astype("uint8"), mode="P")
        classes_image.putpalette(self.segmentation_palette, rawmode="RGB")

        res_image = Image.blend(self.segmentation_image.resize(classes_image.size), classes_image.convert("RGB"), 0.2)
        res_image = res_image.resize(segmentation_size)
        self.last_segmentation_image = res_image
        self.image.paste(res_image, (self.segmentation_border[0], self.segmentation_border[1]))
        self.draw.rectangle(self.segmentation_border, outline="green", width=3)
    
    def redraw_segmentation_results(self) -> None:
        self.image.paste(self.last_segmentation_image, (self.segmentation_border[0], self.segmentation_border[1]))

    def draw_time(self, time_ : float) -> None:
        """Update time

        :param time_: time in seconds since start of the game
        :type time_: float
        """
        self.time_ = time_
        self.draw.text(self.time_position, f"{self.time_:.3f}", fill="black", font=self.font, anchor="mm")

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
        # draw outline
        self.draw.rectangle((0, 0, 
                        self.WORLD_CANVAS_WIDTH, self.WORLD_CANVAS_HEIGHT), 
                        outline="red")
        world_objects : list[tuple[str, Point2d]] = []
        for name, object_list in objects.items():
            obj_id = objects_info.get_item_info(info="obj_id", name=name)
            for obj in object_list:
                world_objects.append((obj_id, obj.position))
        player_position = player.position
        player_position_no_corrections = player.position_before_correction
        new_recent_obj = [obj_pair[0] for obj_pair in recent_objects]
        terrain_tiles = modeling.world_model.tiles
        self.draw_world_model(world_objects, player_position, player_position_no_corrections,
                                vision_corners, deletion_corners, origin_coordinates, 
                                new_recent_obj, estimation_pairs, terrain_tiles)

    def draw_world_model(self, world_objects : list[tuple[str, Point2d]], player_position : Point2d, player_position_no_corrections : Point2d,
                            vision_corners : tuple[Point2d, Point2d, Point2d, Point2d], 
                            deletion_corners : tuple[Point2d, Point2d, Point2d, Point2d], 
                            origin_coordinates : Point2d, recent_objects : list[ObjectModel], 
                            estimation_pairs : list[tuple[str, Point2d, Point2d]],
                            terrain_tiles : dict[tuple[int, int], TerrainTile]) -> None:
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
        :type recent_objects: list[ObjectModel]
        :param estimation_pairs: list of tuples of object name, estimated position and model position
        :type estimation_pairs: list[tuple[str, Point2d, Point2d]]
        """
        if player_position is not None:
            x1_range = (player_position.x1 - self.CLOSE_OBJECTS_X1/2, player_position.x1 + self.CLOSE_OBJECTS_X1/2)
            x2_range = (player_position.x2 - self.CLOSE_OBJECTS_X2/2, player_position.x2 + self.CLOSE_OBJECTS_X2/2)
            self.draw_tiles(terrain_tiles, TILE_SIZE, x1_range, x2_range)
            # black for objects in world model
            for obj_id, position in world_objects:
                if position.x1 > x1_range[0] and position.x1 < x1_range[1] and position.x2 > x2_range[0] and position.x2 < x2_range[1]:
                    self.write_canvas(position.x1, position.x2, x1_range, x2_range, str(obj_id), "black")
            # estimation_pair is (estimate, position in modeling)
            # gray for estimates
            for name, estimate, model_position in estimation_pairs:
                if estimate.x1 > x1_range[0] and estimate.x1 < x1_range[1] and estimate.x2 > x2_range[0] and estimate.x2 < x2_range[1]:
                    obj_id = objects_info.get_item_info(info="obj_id", name=name)
                    self.write_canvas(estimate.x1, estimate.x2, x1_range, x2_range, str(obj_id), "#444444")
                    self.write_canvas(model_position.x1, model_position.x2, x1_range, x2_range, str(obj_id), "orangered")
                    self.draw_line_world_canvas(estimate.x1, estimate.x2, model_position.x1, model_position.x2, x1_range, x2_range)
            # blue for recent objects
            for obj in recent_objects:
                name = obj.name_str()
                position = obj.position
                if position.x1 > x1_range[0] and position.x1 < x1_range[1] and position.x2 > x2_range[0] and position.x2 < x2_range[1]:
                    obj_id = objects_info.get_item_info(info="obj_id", name=name)
                    self.write_canvas(position.x1, position.x2, x1_range, x2_range, str(obj_id), "blue")

            # player position related
            self.write_canvas(player_position_no_corrections.x1, player_position_no_corrections.x2, x1_range, x2_range, "P", "#444444")
            self.write_canvas(player_position.x1, player_position.x2, x1_range, x2_range, "P", "black")
            self.draw_line_world_canvas(player_position.x1, player_position.x2, 
                                        player_position_no_corrections.x1, player_position_no_corrections.x2, 
                                        x1_range, x2_range)

            self.write_canvas(origin_coordinates.x1 ,origin_coordinates.x2,  x1_range, x2_range, "O", "red")
            self.draw_quadrilateral_world_canvas(vision_corners, x1_range, x2_range, "black")
            self.draw_quadrilateral_world_canvas(deletion_corners, x1_range, x2_range, "red")
            self.draw_chunk_lines_world_canvas(CHUNK_SIZE, x1_range, x2_range)

    def draw_world_model_image(self, world_model_image : Image.Image):
        self.last_warped_image = world_model_image
        self.image.paste(world_model_image, self.warped_position)
        self.draw.rectangle((self.warped_position[0], self.warped_position[1], 
                             self.warped_position[0]+world_model_image.size[0], self.warped_position[1]+world_model_image.size[1]), outline="green", width=3)
    
    def redraw_world_model_image(self):
        self.image.paste(self.last_warped_image, self.warped_position)

    def draw_estimation_errors(self, estimation_errors : list[Point2d]):
        # draw outline
        self.draw.rectangle((self.error_position[0], self.error_position[1], 
                        self.error_position[0]+self.ERROR_CANVAS_WIDTH, self.error_position[1]+self.ERROR_CANVAS_HEIGHT), 
                        outline="black")
        self.draw.arc((self.error_position[0], self.error_position[1], 
                        self.error_position[0]+self.ERROR_CANVAS_WIDTH, self.error_position[1]+self.ERROR_CANVAS_HEIGHT),
                        0, 360, fill="blue", width=1)
        center_x = self.error_position[0] + self.ERROR_CANVAS_WIDTH//2
        center_y = self.error_position[1] + self.ERROR_CANVAS_HEIGHT//2
        for error in estimation_errors:
            self.draw.line((center_x, center_y, 
                    center_x+error.x2*self.MAX_ERROR_LENGTH/DISTANCE_FOR_SAME_OBJECT, 
                    center_y+error.x1*self.MAX_ERROR_LENGTH/DISTANCE_FOR_SAME_OBJECT), fill="black", width=2)
        self.draw.text((center_x, center_y), "O", fill="red", font=self.font, anchor="mm")

    def draw_line_world_canvas(self, p1_x1, p1_x2, p2_x1, p2_x2, x1_range, x2_range):
        conv_est_x, conv_est_y = self.convert_world_coords_to_world_graph(p1_x1, p1_x2, x1_range, x2_range)
        conv_mod_x, conv_mod_y = self.convert_world_coords_to_world_graph(p2_x1, p2_x2, x1_range, x2_range)
        self.draw.line((conv_est_x, conv_est_y, conv_mod_x, conv_mod_y), fill="dimgray")

    def convert_world_coords_to_world_graph(self, x1, x2, x1_range, x2_range):
        x = (x2 - x2_range[0])/self.CLOSE_OBJECTS_X2*self.WORLD_CANVAS_WIDTH
        y = (x1 - x1_range[0])/self.CLOSE_OBJECTS_X1*self.WORLD_CANVAS_HEIGHT
        return x, y
    
    def draw_chunk_lines_world_canvas(self, chunk_size, x1_range, x2_range):
        x1_lines = get_multiples_in_range(chunk_size, x1_range)
        x2_lines = get_multiples_in_range(chunk_size, x2_range)
        for x1 in x1_lines:
            # x1 is y in the graph
            _, y = self.convert_world_coords_to_world_graph(x1, 0, x1_range, x2_range)
            self.draw.line((0, y, self.WORLD_CANVAS_WIDTH, y), fill="blue")
        for x2 in x2_lines:
            # x2 is x in the graph
            x, _ = self.convert_world_coords_to_world_graph(0, x2, x1_range, x2_range)
            self.draw.line((x, 0, x, self.WORLD_CANVAS_HEIGHT), fill="blue")

    def draw_quadrilateral_world_canvas(self, vertices, x1_range, x2_range, color):
        p1_x, p1_y = self.convert_world_coords_to_world_graph(vertices[0].x1, vertices[0].x2, x1_range, x2_range)
        p2_x, p2_y = self.convert_world_coords_to_world_graph(vertices[1].x1, vertices[1].x2, x1_range, x2_range)
        p3_x, p3_y = self.convert_world_coords_to_world_graph(vertices[2].x1, vertices[2].x2, x1_range, x2_range)
        p4_x, p4_y = self.convert_world_coords_to_world_graph(vertices[3].x1, vertices[3].x2, x1_range, x2_range)
        self.draw.polygon([p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, p4_x, p4_y], outline=color)

    
    def draw_tiles(self, terrain_tiles: dict[tuple[int, int], TerrainTile], tile_size : int, x1_range : tuple[int, int], x2_range : tuple[int, int]):
        x1_lines = get_multiples_in_range(tile_size, x1_range)
        x2_lines = get_multiples_in_range(tile_size, x2_range)
        color_dict = get_color_representation_dict()
        for x1 in x1_lines:
            for x2 in x2_lines:
                if x1 + tile_size < x1_range[1] and x2 + tile_size < x2_range[1]:
                    if (int(x1//tile_size), int(x2//tile_size)) not in terrain_tiles:
                        continue
                    tile_type = terrain_tiles[int(x1//tile_size), int(x2//tile_size)].type
                    lx, ly = self.convert_world_coords_to_world_graph(x1, x2, x1_range, x2_range)
                    rx, ry = self.convert_world_coords_to_world_graph(x1+tile_size, x2+tile_size, x1_range, x2_range)
                    color = color_dict[tile_type][1]
                    if color is not None:
                        self.draw.rectangle((lx, ly, rx, ry), outline="gray", fill=color)

    def export_results(self, output_path : str):
        self.image.save(output_path)
        self.image = Image.new(mode="RGB", size=(SCREEN_SIZE["width"], SCREEN_SIZE["height"]), color="white")
        self.draw = ImageDraw.Draw(self.image)

    def write_canvas(self, x1, x2, x1_range, x2_range, text, color):
        x, y = self.convert_world_coords_to_world_graph(x1, x2, x1_range, x2_range)
        self.draw.text((x, y), text, fill=color, font=self.font, anchor="mm")