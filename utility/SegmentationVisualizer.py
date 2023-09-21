import tkinter as tk
from tkinter import ttk
from multiprocessing import Queue

import numpy as np
from PIL import Image, ImageTk

from perception.constants import SCREEN_SIZE

class SegmentationVisualizer:
    def __init__(self) -> None:
        self.window = tk.Tk()
        self.window.title("Debug screen")
        self.window.geometry("1000x500")
        self.window.grid_columnconfigure(0)
        self.segmentation_debug_queue = Queue()
        self.perception_div = ttk.LabelFrame(self.window, text="Segmentation output", padding=40)
        self.perception_label = tk.Label(self.perception_div)
        self.perception_label.pack()
        self.perception_div.grid(row=0, column=0)
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
        while not self.segmentation_debug_queue.empty():
            info = self.segmentation_debug_queue.get_nowait()
        # only use the most updated info
        if info is not None and info[0] == "segmentation_results":
            colored_prediction = np.zeros((info[1].shape[0], info[1].shape[1], 3), dtype=np.uint8)
            for i, color in self.palette.items():
                colored_prediction[info[1][:, :, i]] = color
            img = Image.fromarray(colored_prediction, mode="RGB")
            img = img.resize((int(SCREEN_SIZE["width"]/1.5), int(SCREEN_SIZE["height"]/1.5)))
            tk_image = ImageTk.PhotoImage(img)
            self.perception_label.configure(image=tk_image)
            self.perception_label.image = tk_image
        self.window.update_idletasks()
        self.window.update()
