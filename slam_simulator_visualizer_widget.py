import tkinter as tk
from tkinter import ttk
import pickle

import numpy as np

from modeling.SlamSimulator import SlamSimulator
from utility.Point2d import Point2d

class InteractiveCanvas(tk.Canvas):
    def __init__(self, parent, player_positions_gt : np.ndarray, player_positions_estimate : np.ndarray, 
                 landmarks : np.ndarray, trapezoid : np.ndarray, **kwargs):
        super().__init__(parent, **kwargs)
        self.player_positions_gt = player_positions_gt
        self.player_positions_estimate = player_positions_estimate
        self.landmarks = landmarks
        self.point_radius = 1
        self.zoom_level = 1.0
        self.zoom_factor = 1.1
        self.player_estimate = None
        self.player_gt = None
        self.estimate_path_lines = []
        self.vision_trapezoid_lines = []
        self.gt_path_lines = []
        self.point_items = []
        self.transformation_matrix = np.eye(2)
        self.transformation_vector = np.zeros((2, 1))
        self.tracking_mode = False
        self.latest_time = None
        self.autoplay = False
        self.trapezoid = trapezoid

        self.bind("<ButtonPress-1>", self.on_button_press)
        self.bind("<ButtonPress-3>", self.on_right_click)
        self.bind("<B1-Motion>", self.on_mouse_drag)
        self.bind("<MouseWheel>", self.on_zoom)
        self.finish_update_to_time(0)

    def handle_keypress(self, event):
        if event.char == 's':
            self.advance_time()
        elif event.keysym == 'space':
            self.handle_pause()

    def handle_pause(self):
        self.autoplay = not self.autoplay
        if self.autoplay:
            self.after(100, self.advance_time)

    def advance_time(self):
        self.latest_time += 1
        self.handle_time_change(self.latest_time)
        self.master.change_slider_value(self.latest_time)
        if self.autoplay:
            self.after(100, self.advance_time)

    def on_right_click(self, event):
        self.tracking_mode = not self.tracking_mode
        if self.tracking_mode:
            self.center_on_player_gt()

    def handle_time_change(self, time):
        if self.tracking_mode:
            self.center_on_player_gt(time)
        else:
            self.finish_update_to_time(time)

    def center_on_player_gt(self, time = None):
        if self.player_estimate is None or self.player_gt is None:
            return
        if time is None:
            time = self.latest_time
        width = self.winfo_width()
        height = self.winfo_height()
        center_x = width/2
        center_y = height/2
        gt_coords = self.coords(self.player_gt)
        current_player_gt = np.array([[(gt_coords[0]+gt_coords[2])/2, (gt_coords[1]+gt_coords[3])/2]]).T
        translation = np.array([[center_x],[center_y]]) - current_player_gt
        self.transformation_vector += translation
        self.finish_update_to_time(time)

    def convert_coords(self, coords : np.array):
        return self.transformation_matrix @ coords + self.transformation_vector

    def finish_update_to_time(self, time : int):
        self.latest_time = time
        if self.player_gt is not None:
            self.delete(self.player_gt)

        radius = min(self.point_radius * self.zoom_level, 20)

        conv_coords = self.convert_coords(self.player_positions_gt[[time], :].T)
        conv_x = conv_coords[0, 0]
        conv_y = conv_coords[1, 0]
        item = self.create_oval(
            conv_x - radius, conv_y - radius,
            conv_x + radius, conv_y + radius,
            fill="green", tags="point"
        )
        self.player_gt = item

        if len(self.vision_trapezoid_lines) > 0:
            self.delete('vision_trapezoid_line')
        self.vision_trapezoid_lines = []
        for i in range(self.trapezoid.shape[0]-1):
            p1 = self.trapezoid[[i], :].T + self.player_positions_gt[[time], :].T
            conv_coords1 = self.convert_coords(p1)
            conv_x1 = conv_coords1[0, 0]
            conv_y1 = conv_coords1[1, 0]
            p2 = self.trapezoid[[i+1], :].T + self.player_positions_gt[[time], :].T
            conv_coords2 = self.convert_coords(p2)
            conv_x2 = conv_coords2[0, 0]
            conv_y2 = conv_coords2[1, 0]
            line = self.create_line(conv_x1, conv_y1, conv_x2, conv_y2, width=1, fill="grey", tags=('vision_trapezoid_line',))
            self.vision_trapezoid_lines.append(line)

        if self.player_estimate is not None:
            self.delete(self.player_estimate)

        conv_coords = self.convert_coords(self.player_positions_estimate[[time], :].T)
        conv_x = conv_coords[0, 0]
        conv_y = conv_coords[1, 0]
        
        
        item = self.create_oval(
            conv_x - radius, conv_y - radius,
            conv_x + radius, conv_y + radius,
            fill="red", tags="point"
        )
        self.player_estimate = item

        if len(self.point_items) > 0:
            self.delete('lm_point')
        self.point_items = []
        for row in range(self.landmarks.shape[0]):
            conv_coords = self.convert_coords(self.landmarks[[row], :].T)
            conv_x = conv_coords[0, 0]
            conv_y = conv_coords[1, 0]
            item = self.create_oval(
                conv_x - radius, conv_y - radius,
                conv_x + radius, conv_y + radius,
                fill="blue", tags="lm_point"
            )
            self.point_items.append(item)

        if len(self.estimate_path_lines) > 0:
            self.delete('estimate_path_line')
        self.estimate_path_lines = []
        for t in range(self.player_positions_estimate.shape[0]-1):
            p1 = self.player_positions_estimate[[t], :].T
            conv_coords1 = self.convert_coords(p1)
            conv_x1 = conv_coords1[0, 0]
            conv_y1 = conv_coords1[1, 0]
            p2 = self.player_positions_estimate[[t+1], :].T
            conv_coords2 = self.convert_coords(p2)
            conv_x2 = conv_coords2[0, 0]
            conv_y2 = conv_coords2[1, 0]
            line = self.create_line(conv_x1, conv_y1, conv_x2, conv_y2, width=1, fill="red", tags=('estimate_path_line',))
            self.estimate_path_lines.append(line)

        if len(self.gt_path_lines) > 0:
            self.delete('gt_path_line')
        self.gt_path_lines = []
        for t in range(self.player_positions_gt.shape[0]-1):
            p1 = self.player_positions_gt[[t], :].T
            conv_coords1 = self.convert_coords(p1)
            conv_x1 = conv_coords1[0, 0]
            conv_y1 = conv_coords1[1, 0]
            p2 = self.player_positions_gt[[t+1], :].T
            conv_coords2 = self.convert_coords(p2)
            conv_x2 = conv_coords2[0, 0]
            conv_y2 = conv_coords2[1, 0]
            line = self.create_line(conv_x1, conv_y1, conv_x2, conv_y2, width=1, fill="green", tags=('gt_path_line',))
            self.gt_path_lines.append(line)


    def on_button_press(self, event):
        self.scan_mark(event.x, event.y)

    def on_mouse_drag(self, event):
        self.scan_dragto(event.x, event.y, gain=1)

    def on_zoom(self, event):
        scale = self.zoom_factor if event.delta > 0 else 1 / self.zoom_factor
        self.zoom_level *= scale
        self.scale("all", event.x, event.y, scale, scale)
        self.transformation_matrix = np.eye(2)*scale @ self.transformation_matrix
        self.transformation_vector = np.eye(2)*scale @ self.transformation_vector + np.array([[-(scale-1)*event.x], [-(scale-1)*event.y]])
        if self.tracking_mode:
            self.center_on_player_gt()

class Application(tk.Tk):
    def __init__(self, player_positions_gt : np.ndarray, player_positions_estimate : np.ndarray, 
                 landmarks : np.ndarray, trapezoid : np.ndarray, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Interactive 2D Plot with Slider")

        self.canvas = InteractiveCanvas(self, player_positions_gt, player_positions_estimate, landmarks, trapezoid, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.slider_value = tk.IntVar()
        self.slider = ttk.Scale(self, from_=0, to=player_positions_gt.shape[0]-1, orient=tk.HORIZONTAL, variable=self.slider_value, command=self.on_slider_change)
        self.slider.pack(fill=tk.X, side=tk.BOTTOM)

        self.label = tk.Label(self, text="Slider Value: 0")
        self.label.pack(side=tk.BOTTOM)

        self.bind("<KeyPress>", self.canvas.handle_keypress)

    def on_slider_change(self, event):
        self.label.config(text=f"Slider Value: {self.slider_value.get()}")
        self.canvas.handle_time_change(self.slider_value.get())
    
    def change_slider_value(self, value):
        self.slider.set(value)


if __name__ == "__main__":
    # 445,150,spiral_1,"[2, 2]","[40.0, 50.0]"
    seed = 445
    num_landmarks = 150
    trajectory_name = "spiral_1"
    trajectories = {
        "square_1" : [Point2d(50, 50), Point2d(50, -50), Point2d(-50, -50), Point2d(-50, 50), Point2d(50, 50), Point2d(0, 0)],
        "square_2" : [Point2d(0, 50), Point2d(50, 0), Point2d(0, -50), Point2d(-50, 0), Point2d(0, 50), Point2d(0, 0)],
        "spiral_1" : [Point2d(0, 20), Point2d(20, 20), Point2d(20, -40), Point2d(-40, -40), 
                        Point2d(-40, 60), Point2d(60, 60), Point2d(60, -80), Point2d(-80, -80)],
        "spiral_2" : [Point2d(1, 1), Point2d(3, -1), Point2d(3, -4), Point2d(0, -5), Point2d(-3, -3), Point2d(-5, 0), Point2d(-3, 5),  
                    Point2d(0, 8), Point2d(5, 8), Point2d(10, 4), Point2d(14, -4), Point2d(10, -10), Point2d(1, -14), Point2d(-12, -9),  
                    Point2d(-16, 3), Point2d(-10, 14), Point2d(-1, 23), Point2d(13, 20), Point2d(24, 7), Point2d(27, -6), Point2d(17, -18),  
                    Point2d(2, -28), Point2d(-15, -25), Point2d(-31, -6), Point2d(-26, 17), Point2d(-11, 34), Point2d(14, 35), Point2d(32, 21),  
                    Point2d(41, 0), Point2d(29, -28), Point2d(11, -41), Point2d(-21, -44), Point2d(-41, -31)],
    }
    u_noise = [2, 2]
    h_noise = [40.0, 50.0]

    player_positions_gt = np.load(f"slam_simulator_results/player_positions_gt__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.npy")
    with open(f"slam_simulator_results/state_estimate__{seed}__{num_landmarks}__{trajectory_name}__{str(u_noise[0])}__{str(u_noise[1])}__{str(h_noise[0])}__{str(h_noise[1])}.pkl", "rb") as file:
        state_list = pickle.load(file)
    temp_list = []
    for state in state_list:
        temp_list.append([state[0, 0], state[1, 0]])
    player_positions_estimate = np.array(temp_list)
    if num_landmarks > 0:
        landmarks = np.load(f"slam_simulator_results/landmark_positions__{seed}__{num_landmarks}.npy")
    else:
        landmarks = None

    sim = SlamSimulator(0, 0, [], [0, 0], [0, 0])
    trapezoid = sim.vision_trapezoid
    trapezoid_np = np.array([[p.x1, p.x2] for p in trapezoid])

    app = Application(player_positions_gt, player_positions_estimate, landmarks, trapezoid_np)

    app.mainloop()
