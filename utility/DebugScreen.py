import tkinter as tk
from tkinter import ttk
from multiprocessing import Queue

import numpy as np
from PIL import Image, ImageTk

from perception.constants import SCREEN_SIZE
from modeling.constants import CHUNK_SIZE, TILE_SIZE
from modeling.TerrainTile import TerrainTile
from utility.utility import get_multiples_in_range, get_color_representation_dict
from utility.Point2d import Point2d

class DebugScreen:
    # reminder that the two below this are in pixels
    LOCAL_CANVAS_WIDTH = SCREEN_SIZE["width"]//3
    LOCAL_CANVAS_HEIGHT = SCREEN_SIZE["height"]//3
    # reminder that the two below this are in in-game units
    CLOSE_OBJECTS_X1 = 75
    CLOSE_OBJECTS_X2 = 75
    # reminder that the two below this are in pixels
    WORLD_CANVAS_WIDTH = 400
    WORLD_CANVAS_HEIGHT = 400
    def __init__(self) -> None:
        self.window = tk.Tk()
        self.window.title("Debug screen")
        self.window.geometry("1000x500")
        self.vision_debug_queue = Queue()
        self.segmentation_debug_queue = Queue()
        self.control_debug_queue = Queue()
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_columnconfigure(1, weight=1)
        self.primary_action_label = ttk.Label(text="Primary action: -", font=("Arial", 30), wraplength=800, justify='center')
        self.primary_action_label.grid(row=0, column=0, pady=2)
        self.secondary_action_label = ttk.Label(text="Secondary action: -", font=("Arial", 30), wraplength=800, justify='center')
        self.secondary_action_label.grid(row=1, column=0, pady=2)
        self.current_action_label = ttk.Label(text="Current action: -", font=("Arial", 30), wraplength=800, justify='center')
        self.current_action_label.grid(row=2, column=0, pady=2)
        self.key_label = ttk.Label(text="Key command: -", font=("Arial", 30), wraplength=800, justify='center')
        self.key_label.grid(row=3, column=0, pady=2)
        self.mouse_label = ttk.Label(text="Mouse command: -", font=("Arial", 30), wraplength=800, justify='center')
        self.mouse_label.grid(row=4, column=0, pady=2)
        # self.local_map_div = ttk.LabelFrame(self.window, text="Local modeling", padding=40)
        # self.local_map = tk.Canvas(self.local_map_div, height=self.LOCAL_CANVAS_HEIGHT, width=self.LOCAL_CANVAS_WIDTH, highlightbackground="red", highlightcolor="red", relief='ridge')
        # self.local_map.pack()
        # self.local_map_div.grid(row=0, column=1, rowspan=2)
        self.perception_display_choice = "objects" # this has to be either "objects" or "segmentation"
        assert self.perception_display_choice == "objects" or self.perception_display_choice == "segmentation"
        if self.perception_display_choice == "objects":
            self.perception_div = ttk.LabelFrame(self.window, text="Detected objects", padding=40)
        else: # self.perception_display_choice == segmentation
            self.perception_div = ttk.LabelFrame(self.window, text="Segmentation output", padding=40)
        self.perception_label = tk.Label(self.perception_div)
        self.perception_label.pack()
        self.perception_div.grid(row=0, column=1, rowspan=2)
        self.world_map_div = ttk.LabelFrame(self.window, text="Global modeling", padding=40)
        self.world_map = tk.Canvas(self.world_map_div, height=self.WORLD_CANVAS_HEIGHT, width=self.WORLD_CANVAS_WIDTH, highlightbackground="red", highlightcolor="red", relief='ridge')
        self.world_map.pack()
        self.world_map_div.grid(row=2, column=1, rowspan=3)
        self.player_position = None
        self.world_objects = []
        self.objective : Point2d = None
        self.fov_corners : list[float] = []
        self.palette = {}
        dsai_terrain_palette = [0, 0, 0, # bg black
                    255, 50, 50, # forest red
                    255, 204, 50, # grass yellow
                    153, 255, 50, # marsh lime (yellow green)
                    50, 255, 101, # ocean bright green
                    50, 255, 255, # rocky light blue
                    50, 101, 255, # savanna dark blue
                    153, 50, 255] # spider_web purple
        for i in range(0, len(dsai_terrain_palette), 3):
            self.palette[i//3] = np.array(dsai_terrain_palette[i:i+3])

    def update(self):
        info = None
        while not self.vision_debug_queue.empty():
            info = self.vision_debug_queue.get_nowait()
        # only use the most updated info
        if info is not None and info[0] == "detected_objects" and self.perception_display_choice == "objects":
            tuple_image = info[1][:, :, ::-1] # yolo seems to detect objects better in bgr?? so I'm converting it back to rgb here
            img = Image.fromarray(tuple_image)
            img = img.resize((SCREEN_SIZE["width"]//3, SCREEN_SIZE["height"]//3))
            tk_image = ImageTk.PhotoImage(img)
            self.perception_label.configure(image=tk_image)
            self.perception_label.image = tk_image
        
        info = None
        while not self.segmentation_debug_queue.empty():
            info = self.segmentation_debug_queue.get_nowait()
        # only use the most updated info
        if info is not None and info[0] == "segmentation_results" and self.perception_display_choice == "segmentation":
            colored_prediction = np.zeros((info[1].shape[0], info[1].shape[1], 3), dtype=np.uint8)
            for i, color in self.palette.items():
                colored_prediction[info[1][:, :, i]] = color
            img = Image.fromarray(colored_prediction)
            img = img.resize((SCREEN_SIZE["width"]//3, SCREEN_SIZE["height"]//3))
            tk_image = ImageTk.PhotoImage(img)
            self.perception_label.configure(image=tk_image)
            self.perception_label.image = tk_image
        
        info = None
        while not self.control_debug_queue.empty():
            info = self.control_debug_queue.get_nowait()
        # only use the most updated info
        if info is not None and info[0] == "control_info":
            _, q1, q2, q3 = info
            world_model_objects, fov_corners, player_position, terrain_tiles = q1
            primary_action, secondary_action = q2
            current_action, key_action, mouse_action = q3
            self.primary_action_label["text"] = "Primary action: " + str(primary_action)
            self.secondary_action_label["text"] = f"Secondary action: {str(secondary_action[0])}, {str(secondary_action[1])}"
            self.key_label["text"] = "Key command: " + str(key_action)
            if mouse_action is None:
                self.mouse_label["text"] = "Mouse command: " + str(mouse_action)
            else:
                self.mouse_label["text"] = f"Mouse command: {str(mouse_action[0])}, {str(mouse_action[1])}"
            if current_action[0] == "go_to" or current_action[0] == "explore":
                self.objective = current_action[1]
                self.current_action_label["text"] = f"Current action: {str(current_action[0])}, {str(current_action[1])}"
            else:
                self.current_action_label["text"] = "Current action: " + str(current_action)
            self.world_map.delete('all')
            for name, pos_list in world_model_objects:
                if name == "Grass":
                    for pos in pos_list:
                        self.world_objects.append(("Grass", pos))
                if name == "Sapling":
                    for pos in pos_list:
                        self.world_objects.append(("Sapling", pos))
            self.player_position = player_position
            # this can be None if we don't know player_position
            if fov_corners[0] is not None:
                self.fov_corners = (fov_corners[0].x1, fov_corners[0].x2, 
                                    fov_corners[1].x1, fov_corners[1].x2, 
                                    fov_corners[2].x1, fov_corners[2].x2, 
                                    fov_corners[3].x1, fov_corners[3].x2)
        if self.player_position is not None:
            x1_range = (self.player_position.x1 - self.CLOSE_OBJECTS_X1/2, self.player_position.x1 + self.CLOSE_OBJECTS_X1/2)
            x2_range = (self.player_position.x2 - self.CLOSE_OBJECTS_X2/2, self.player_position.x2 + self.CLOSE_OBJECTS_X2/2)
            self.draw_tiles(terrain_tiles, TILE_SIZE, x1_range, x2_range)
            for name, position in self.world_objects:
                if position.x1 > x1_range[0] and position.x1 < x1_range[1] and position.x2 > x2_range[0] and position.x2 < x2_range[1]:
                    if name == "Grass":
                        self.draw_shape(position.x1, position.x2, "triangle", "global", x1_range, x2_range)
                    elif name == "Sapling":
                        self.draw_shape(position.x1, position.x2, "square", "global", x1_range, x2_range)
            self.draw_shape(self.player_position.x1, self.player_position.x2, "circle", "global", x1_range, x2_range)
            if self.objective is not None:
                self.draw_shape(self.objective.x1, self.objective.x2, "x", "global", x1_range, x2_range)
            if len(self.fov_corners) > 0:
                self.draw_fov(self.fov_corners, "global", x1_range, x2_range)
            self.draw_chunk_lines_world_canvas(CHUNK_SIZE, x1_range, x2_range)
            self.player_position = None
            self.objective = None
            self.world_objects = []
        self.window.update_idletasks()
        self.window.update()

    def convert_world_coords_to_world_graph(self, x1, x2, x1_range, x2_range):
        x = (x2 - x2_range[0])/self.CLOSE_OBJECTS_X2*self.WORLD_CANVAS_WIDTH
        y = (x1 - x1_range[0])/self.CLOSE_OBJECTS_X1*self.WORLD_CANVAS_HEIGHT
        return x, y

    def draw_fov(self, point_list : list[float], canvas_name : str, x1_range : tuple[float, float], x2_range : tuple[float, float]) -> None:
        """Draw the fov trapezium defined by the point_list

        :param point_list: list of 4 points to draw
        :type point_list: list[float]
        :param canvas_name: should be "global" for now
        :type canvas_name: str
        :param x1_range: x1 range of objects that should be drawn
        :type x1_range: tuple[float, float]
        :param x2_range: x2 range of objects that should be drawn
        :type x2_range: tuple[float, float]
        """
        # point_list should be [x1, y1, x2, y2, x3, y3, x4, y4]
        if canvas_name == "global":
            map_ = self.world_map
            x1, y1 = self.convert_world_coords_to_world_graph(point_list[0], point_list[1], x1_range, x2_range)
            x2, y2 = self.convert_world_coords_to_world_graph(point_list[2], point_list[3], x1_range, x2_range)
            x3, y3 = self.convert_world_coords_to_world_graph(point_list[4], point_list[5], x1_range, x2_range)
            x4, y4 = self.convert_world_coords_to_world_graph(point_list[6], point_list[7], x1_range, x2_range)
        else:
            raise ValueError("Wrong usage!")
        
        map_.create_polygon(x1, y1, x2, y2, x3, y3, x4, y4, fill='', outline="black")
    
    def draw_tiles(self, terrain_tiles: dict[tuple[int, int], TerrainTile], tile_size : int, x1_range : tuple[int, int], x2_range : tuple[int, int]):
        x1_lines = get_multiples_in_range(tile_size, x1_range)
        x2_lines = get_multiples_in_range(tile_size, x2_range)
        map_ = self.world_map
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
                        map_.create_rectangle(lx, ly, rx, ry, fill=color)

    def draw_chunk_lines_world_canvas(self, chunk_size : int, x1_range : tuple[int, int], x2_range : tuple[int, int]):
        x1_lines = get_multiples_in_range(chunk_size, x1_range)
        x2_lines = get_multiples_in_range(chunk_size, x2_range)
        map_ = self.world_map
        for x1 in x1_lines:
            # x1 is y in the graph
            _, y = self.convert_world_coords_to_world_graph(x1, 0, x1_range, x2_range)
            map_.create_line(0, y, self.WORLD_CANVAS_WIDTH, y)
        for x2 in x2_lines:
            # x2 is x in the graph
            x, _ = self.convert_world_coords_to_world_graph(0, x2, x1_range, x2_range)
            map_.create_line(x, 0, x, self.WORLD_CANVAS_HEIGHT)

    def draw_shape(self, x1 : float, x2 : float, shape : str, canvas_name : str, 
                   x1_range : tuple[float, float], x2_range : tuple[float, float]):
        """Draw shape on the specified canvas

        :param x1: x1 position
        :type x1: float
        :param x2: x2 position
        :type x2: float
        :param shape: triangle, circle or square
        :type shape: str
        :param canvas_name: "global" for now
        :type canvas_name: str
        :param x1_range: x1 range of objects that should be drawn
        :type x1_range: tuple[float, float]
        :param x2_range: x2 range of objects that should be drawn
        :type x2_range: tuple[float, float]
        """
        # if canvas_name == "local":
        #     map_ = self.local_map
        #     x1 = x1/SCREEN_SIZE["width"]*self.LOCAL_CANVAS_WIDTH
        #     x2 = x2/SCREEN_SIZE["height"]*self.LOCAL_CANVAS_HEIGHT
        # elif canvas_name == "global":
        if canvas_name == "global":
            map_ = self.world_map
            x, y = self.convert_world_coords_to_world_graph(x1, x2, x1_range, x2_range)
        else:
            raise ValueError("Wrong usage!")
        if shape == "triangle":
            map_.create_polygon(x, y-6, x-4, y+2, x+4, y+2)
        elif shape == "circle":
            map_.create_oval(x-4, y-4, x+4, y+4)
        elif shape == "square":
            map_.create_rectangle(x-4, y-4, x+4, y+4)
        elif shape == "x":
            map_.create_line(x-6, y-6, x+6, y+6, fill="red")
            map_.create_line(x+6, y-6, x-6, y+6, fill="red")
