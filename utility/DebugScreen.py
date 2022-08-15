import tkinter as tk
from tkinter import ttk
import queue
from turtle import pos

from perception.screen import SCREEN_SIZE
from modeling.ObjectsInfo import objects_info

class DebugScreen:
    LOCAL_CANVAS_WIDTH = SCREEN_SIZE["width"]//3
    LOCAL_CANVAS_HEIGHT = SCREEN_SIZE["height"]//3
    CLOSE_OBJECTS_WIDTH = 800
    CLOSE_OBJECTS_HEIGHT = 400
    WORLD_CANVAS_WIDTH = CLOSE_OBJECTS_WIDTH*0.75
    WORLD_CANVAS_HEIGHT = CLOSE_OBJECTS_HEIGHT*0.75
    def __init__(self) -> None:
        self.window = tk.Tk()
        self.window.title("Debug screen")
        self.window.geometry("1000x500")
        self.q = queue.Queue()
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_columnconfigure(1, weight=1)
        self.primary_action_label = ttk.Label(text="Primary action: -", font=("Arial", 40), wraplength=800, justify='center')
        self.primary_action_label.grid(row=0, column=0, pady=2)
        self.secondary_action_label = ttk.Label(text="Secondary action: -", font=("Arial", 40), wraplength=800, justify='center')
        self.secondary_action_label.grid(row=1, column=0, pady=2)
        self.key_label = ttk.Label(text="Key command: -", font=("Arial", 40), wraplength=800, justify='center')
        self.key_label.grid(row=2, column=0, pady=2)
        self.mouse_label = ttk.Label(text="Mouse command: -", font=("Arial", 40), wraplength=800, justify='center')
        self.mouse_label.grid(row=3, column=0, pady=2)
        self.local_map_div = ttk.LabelFrame(self.window, text="Local modeling", padding=40)
        self.local_map = tk.Canvas(self.local_map_div, height=self.LOCAL_CANVAS_HEIGHT, width=self.LOCAL_CANVAS_WIDTH, highlightbackground="red", highlightcolor="red", relief='ridge')
        self.local_map.pack()
        self.local_map_div.grid(row=0, column=1, rowspan=2)
        self.world_map_div = ttk.LabelFrame(self.window, text="Global modeling", padding=40)
        self.world_map = tk.Canvas(self.world_map_div, height=self.WORLD_CANVAS_HEIGHT, width=self.WORLD_CANVAS_WIDTH, highlightbackground="red", highlightcolor="red", relief='ridge')
        self.world_map.pack()
        self.world_map_div.grid(row=2, column=1, rowspan=2)
        self.player_position = None
        self.world_objects = []
    
    def update(self):
        while not self.q.empty():
            info = self.q.get_nowait()
            if info[0] == "primary_action":
                self.primary_action_label["text"] = "Primary action: " + str(info[1])
            elif info[0] == "secondary_action":
                self.secondary_action_label["text"] = "Secondary action: " + str(info[1])
            elif info[0] == "key_action":
                self.key_label["text"] = "Key command: " + str(info[1])
            elif info[0] == "mouse_action":
                self.mouse_label["text"] = "Mouse command: " + str(info[1])
            elif info[0] == "detected_objects":
                self.local_map.delete('all')
                for item in info[1]:
                    if objects_info.get_item_info(info="name", image_id=item.id) == "Wilson":
                        self.draw_shape(item.box[0], item.box[1], "circle", "local")
                    if objects_info.get_item_info(info="name", image_id=item.id) == "Grass":
                        self.draw_shape(item.box[0], item.box[1], "triangle", "local")
                    if objects_info.get_item_info(info="name", image_id=item.id) == "Sapling":
                        self.draw_shape(item.box[0], item.box[1], "square", "local")
            elif info[0] == "world_model_objects":
                self.world_map.delete('all')
                for id_, object_list in info[1].items():
                    if objects_info.get_item_info(info="name", obj_id=id_) == "Grass":
                        for obj in object_list:
                            self.world_objects.append(("Grass", obj.position))
                    if objects_info.get_item_info(info="name", obj_id=id_) == "Sapling":
                        for obj in object_list:
                            self.world_objects.append(("Sapling", obj.position))
            elif info[0] == "player":
                self.player_position = info[1].position
        if self.player_position is not None:
            x_range = (self.player_position.x - self.CLOSE_OBJECTS_WIDTH/2, self.player_position.x + self.CLOSE_OBJECTS_WIDTH/2)
            y_range = (self.player_position.y - self.CLOSE_OBJECTS_HEIGHT/2, self.player_position.y + self.CLOSE_OBJECTS_HEIGHT/2)
            for name, position in self.world_objects:
                if position.x > x_range[0] and position.x < x_range[1] and position.y > y_range[0] and position.y < y_range[1]:
                    if name == "Grass":
                        self.draw_shape(position.x-x_range[0], position.y-y_range[0], "triangle", "global")
                    elif name == "Sapling":
                        self.draw_shape(position.x-x_range[0], position.y-y_range[0], "square", "global")
            self.draw_shape(self.CLOSE_OBJECTS_WIDTH/2, self.CLOSE_OBJECTS_HEIGHT/2, "circle", "global")
            self.player_position = None
            self.world_objects = []
        self.window.update_idletasks()
        self.window.update()

    def draw_shape(self, x, y, shape, canvas_name):
        if canvas_name == "local":
            map_ = self.local_map
            x = x/SCREEN_SIZE["width"]*self.LOCAL_CANVAS_WIDTH
            y = y/SCREEN_SIZE["height"]*self.LOCAL_CANVAS_HEIGHT
        elif canvas_name == "global":
            map_ = self.world_map
            x = x/self.CLOSE_OBJECTS_WIDTH*self.WORLD_CANVAS_WIDTH
            y = y/self.CLOSE_OBJECTS_HEIGHT*self.WORLD_CANVAS_HEIGHT
        else:
            raise Exception("Wrong usage!")
        if shape == "triangle":
            map_.create_polygon(x, y-6, x-4, y+2, x+4, y+2)
        elif shape == "circle":
            map_.create_oval(x-4, y-4, x+4, y+4)
        elif shape == "square":
            map_.create_polygon(x-4, y-4, x+4, y+4)
