from __future__ import annotations
from typing import TYPE_CHECKING
import math
import time
import queue
import glob
from pathlib import Path

import numpy as np
import cv2
from PIL import Image

from perception.ImageObject import ImageObject
from perception.constants import SCREEN_SIZE, SEGMENTATION_INPUT_SIZE
from modeling.mobs.MobModel import MobModel
from modeling.objects.ObjectModel import ObjectModel
from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from modeling.Factory import factory
from modeling.constants import DISTANCE_FOR_SAME_OBJECT, DISTANCE_FOR_SAME_MOB, CYCLES_TO_ADMIT_OBJECT, CYCLES_TO_ADMIT_MOB
from modeling.constants import FOV, CAMERA_DISTANCE, CAMERA_PITCH, CAMERA_HEADING, CHUNK_SIZE, DISTANCE_FOR_VALID_PLAYER_POSITION
from modeling.constants import TILE_SIZE, FOLLOW_HEIGHT
from modeling.ObjectsInfo import objects_info
from modeling.Scheduler import Scheduler
from modeling.SlamIndexManager import SlamIndexManager
from modeling.TileManager import TileManager
from modeling.utility import local_to_almost_global_position
from utility.Clock import Clock
from utility.Point2d import Point2d
from utility.utility import is_inside_convex_polygon, get_color_representation_dict
if TYPE_CHECKING:
    from modeling.Modeling import Modeling



class WorldModel:
    def __init__(self, modeling : Modeling, clock : Clock, debug : bool = False):
        """Generates the world model. It should be noted that the full workflow for a cycle of updating is:
            - if player was detected (on perception), call player_detected()
            - call start_cycle()
            - for each object detected, call object_detected()
            - after all that, call finish_cycle()

        :param modeling: the modeling model
        :type modeling: Modeling
        :param clock: a clock to keep track of how much time passed since the last update
        :type clock: Clock
        """
        self.modeling = modeling
        # maps object name to the object list
        self.object_lists : dict[str, list[ObjectModel]] = {}
        # objects_by_chunks maps a chunk index to a list of objects in it
        # (x1, x2) -> list
        self.objects_by_chunks : dict[tuple[int, int], list[ObjectModel]] = {}
        self.mob_lists : dict[str, list[MobModel]] = {}
        self.explored_chunks = set()
        self.objects_detected_this_cycle : list[list[ObjectModel, bool]] = {}
        self.mobs_detected_this_cycle : list[list[MobModel, bool]] = {}
        self.latest_detected_player_position : Point2d = None
        self.cycles_since_player_detected : int = 0
        self.origin_coordinates : Point2d = Point2d(modeling.xEst[0, 0], modeling.xEst[1, 0])
        self.clock : Clock = clock
        self.c1 : Point2d = None # for usual values, (2.202, -36.468)
        self.c2 : Point2d = None # for usual values, (16.263, -2.791)
        self.c3 : Point2d = None # for usual values, (-2.791, 16.263)
        self.c4 : Point2d = None # for usual values, (-36.468, 2.202)
        # for heading = 0, the values are:
        # -24.230 -27.344
        # 9.526 -13.474
        # 9.526 13.474
        # -24.230 27.344
        self.c1_deletion_border : Point2d = None
        self.c2_deletion_border : Point2d = None
        self.c3_deletion_border : Point2d = None
        self.c4_deletion_border : Point2d = None
        self.recent_objects : list[list[ObjectModel, int]] = []
        self.recent_mobs : list[list[MobModel, int]] = []
        self.additions_to_recent_objects : list[list[ObjectModel, int]] = []
        self.additions_to_recent_mobs : list[list[MobModel, int]] = []
        self.hovering_object : ObjectModel = None
        self.tile_manager : TileManager = TileManager()
        self._THRESHOLD_FOR_EXPLORED : float = 0.7
        self.scheduler = Scheduler(self.clock, self)
        self.slam_index_manager = SlamIndexManager()
        self.segmentation_timestamp : float = None
        self.debug = debug
        self.latest_debug_image : Image.Image = None

    @staticmethod
    def coords_to_chunk_coords(p : Point2d) -> Point2d:
        """Convert coordinates to chunk coordinates, bounded in [0, CHUNK_SIZE]

        :param p: point to convert
        :type p: Point2d
        :return: converted coordinates
        :rtype: Point2d
        """
        x1 = p.x1 - math.floor(p.x1/CHUNK_SIZE)*CHUNK_SIZE
        x2 = p.x2 - math.floor(p.x2/CHUNK_SIZE)*CHUNK_SIZE
        return Point2d(x1, x2)

    @staticmethod
    def tile_to_chunk_index(i : int, j : int) -> tuple[int, int]:
        """Maps tile index to which chunk it is in

        :param i: tile index 1
        :type i: int
        :param j: tile index 2
        :type j: int
        :return: chunk index
        :rtype: tuple[int, int]
        """
        return Point2d(i // (CHUNK_SIZE // TILE_SIZE), j // (CHUNK_SIZE // TILE_SIZE))

    def remove_object(self, obj : ObjectModel) -> None:
        """Remove object from world model

        :param obj: object obj
        :type obj: ObjectModel
        """
        count = 0
        for obj_chunk_list in self.objects_by_chunks.values():
            count += len(obj_chunk_list)
        print(f"before objects_by_chunks deletion: {count}")
        chunk_index = self.point_to_chunk_index(obj.position())
        # if obj is in the chunk we expect it to be
        if chunk_index in self.objects_by_chunks.keys() and obj in self.objects_by_chunks[chunk_index]:
            self.objects_by_chunks[chunk_index].remove(obj)
        else:
            self.remove_object_from_chunk_lists(obj)
        
        count = 0
        for obj_chunk_list in self.objects_by_chunks.values():
            count += len(obj_chunk_list)
        print(f"after objects_by_chunks deletion: {count}")
        
        print(f"before object_lists deletion: {len(self.object_lists[obj.name_str()])}")
        self.object_lists[obj.name_str()].remove(obj)
        print(f"after object_lists deletion: {len(self.object_lists[obj.name_str()])}")
        

    def warp_image_to_ground(self, image: np.ndarray, heading : float, pitch : float, 
                             distance : float, fov : float) -> tuple[np.ndarray, tuple[float, float], tuple[float, float]]:
        """Warp image to transform a camera image to the ground coordinates

        :param image: game image from camera's perspective
        :type image: np.ndarray
        :param heading: camera heading
        :type heading: float
        :param pitch: camera pitch
        :type pitch: float
        :param distance: camera distance
        :type distance: float
        :param fov: camera FOV
        :type fov: float
        :return: warped image, x range and y range relative to the player
        :rtype: tuple[np.ndarray, tuple[float, float], tuple[float, float]]
        """
        # f = H / (2*tan(AFOV/2)), f focal distance, H height, AFOV angular FOV
        f = SCREEN_SIZE["height"]/(2*math.tan(fov/180*math.pi/2))
        cx = SCREEN_SIZE["width"]/2
        cy = SCREEN_SIZE["height"]/2
        heading = heading*math.pi/180
        pitch = pitch*math.pi/180
        matrix = np.array([
            [(-f*math.sin(heading)-cx*math.cos(pitch)*math.cos(heading))*SEGMENTATION_INPUT_SIZE[0]/SCREEN_SIZE["width"], 
             (f*math.cos(heading)-cx*math.cos(pitch)*math.sin(heading))*SEGMENTATION_INPUT_SIZE[0]/SCREEN_SIZE["width"], 
             (cx*distance+cx*FOLLOW_HEIGHT*math.sin(pitch))*SEGMENTATION_INPUT_SIZE[0]/SCREEN_SIZE["width"]],

            [(f*math.sin(pitch)*math.cos(heading)-cy*math.cos(pitch)*math.cos(heading))*SEGMENTATION_INPUT_SIZE[1]/SCREEN_SIZE["height"],
             (f*math.sin(pitch)*math.sin(heading)-cy*math.cos(pitch)*math.sin(heading))*SEGMENTATION_INPUT_SIZE[1]/SCREEN_SIZE["height"],
             (f*FOLLOW_HEIGHT*math.cos(pitch)+cy*distance+cy*FOLLOW_HEIGHT*math.sin(pitch))*SEGMENTATION_INPUT_SIZE[1]/SCREEN_SIZE["height"]],

            [-math.cos(pitch)*math.cos(heading),
             -math.cos(pitch)*math.sin(heading),
             distance+FOLLOW_HEIGHT*math.sin(pitch)],
        ])
        
        matrix = np.linalg.inv(matrix)
        # matrix[0, :] = matrix[0, :]*(SEGMENTATION_INPUT_SIZE[0]/52.731)
        # matrix[1, :] = matrix[1, :]*(SEGMENTATION_INPUT_SIZE[1]/52.731)
        # 4 image corners
        c1 = np.array([[0, 0, 1]]).T
        c2 = np.array([[SEGMENTATION_INPUT_SIZE[0], 0, 1]]).T
        c3 = np.array([[SEGMENTATION_INPUT_SIZE[0], SEGMENTATION_INPUT_SIZE[1], 1]]).T
        c4 = np.array([[0, SEGMENTATION_INPUT_SIZE[1], 1]]).T
        # converted corners
        r1 = np.matmul(matrix, c1)
        r2 = np.matmul(matrix, c2)
        r3 = np.matmul(matrix, c3)
        r4 = np.matmul(matrix, c4)
        # finding x and y range
        x_min = min(r1[0]/r1[2], r2[0]/r2[2], r3[0]/r3[2], r4[0]/r4[2])
        y_min = min(r1[1]/r1[2], r2[1]/r2[2], r3[1]/r3[2], r4[1]/r4[2])
        x_max = max(r1[0]/r1[2], r2[0]/r2[2], r3[0]/r3[2], r4[0]/r4[2])
        y_max = max(r1[1]/r1[2], r2[1]/r2[2], r3[1]/r3[2], r4[1]/r4[2])
        # this rescales the output because world coordinates would be like 50, but we need it to be like 500
        matrix[0, :] = matrix[0, :]*(SEGMENTATION_INPUT_SIZE[0]/(x_max - x_min))
        matrix[1, :] = matrix[1, :]*(SEGMENTATION_INPUT_SIZE[1]/(y_max - y_min))
        # translating output to be on positive x and y
        transl_mat = np.eye(3)
        transl_mat[0, 2] = -x_min*(SEGMENTATION_INPUT_SIZE[0]/(x_max - x_min))
        transl_mat[1, 2] = -y_min*(SEGMENTATION_INPUT_SIZE[1]/(y_max - y_min))
        matrix = np.matmul(transl_mat, matrix)
        
        image = image.astype('uint8')
        res = cv2.warpPerspective(image, matrix, (SEGMENTATION_INPUT_SIZE[0], SEGMENTATION_INPUT_SIZE[1]), flags=cv2.INTER_NEAREST)

        return res, (x_min[0], x_max[0]), (y_min[0], y_max[0])

    def process_segmentation_image(self, image: np.ndarray, past_player_position : Point2d) -> Image.Image:
        """Updates tiles based on segmentation info

        :param image: segmentation result image
        :type image: np.ndarray
        :param past_player_position: estimated position of the player in the timestamp the segmentation screenshot was taken
        :type past_player_position: Point2d
        """
        # in openCV, x is right and y is down, but for us x1 is down and x2 is right, so they are inverted
        warped_image, x_range, y_range = self.warp_image_to_ground(image, CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
        player_pos = past_player_position
        x_min = x_range[0] + player_pos.x2
        x_max = x_range[1] + player_pos.x2
        y_min = y_range[0] + player_pos.x1
        y_max = y_range[1] + player_pos.x1

        x_lines = []
        aux = (x_min // TILE_SIZE) * TILE_SIZE + TILE_SIZE
        left_corner_x = aux
        while aux < x_max:
            x_lines.append(int((aux - x_min)/(x_max - x_min)*SEGMENTATION_INPUT_SIZE[0]))
            aux += TILE_SIZE

        y_lines = []
        aux = (y_min // TILE_SIZE) * TILE_SIZE + TILE_SIZE
        left_corner_y = aux
        while aux < y_max:
            y_lines.append(int((aux - y_min)/(y_max - y_min)*SEGMENTATION_INPUT_SIZE[1]))
            aux += TILE_SIZE

        # how to do averages efficiently?
        # kernel_size = x_lines[1] - x_lines[0]
        # conv_kernel = torch.Tensor(np.ones((kernel_size, kernel_size))/kernel_size/kernel_size)
        # res_tensor = torch.Tensor(warped_image[x_lines[0]:x_lines[-1], y_lines[0]:y_lines[-1], :]).unsqueeze(0).permute(0, 3, 1, 2)
        
        self.tile_manager.add_detections(x_lines, y_lines, warped_image, (int(left_corner_y // TILE_SIZE), int(left_corner_x // TILE_SIZE)))
        # check if enough tiles were detected to consider the chunk explored
        chunk_index = self.point_to_chunk_index(past_player_position)
        tile1 = (chunk_index[0]*(CHUNK_SIZE//TILE_SIZE), chunk_index[1]*(CHUNK_SIZE//TILE_SIZE))
        tile2 = ((chunk_index[0]+1)*(CHUNK_SIZE//TILE_SIZE) - 1, (chunk_index[1]+1)*(CHUNK_SIZE//TILE_SIZE) - 1)
        chunk_tiles = self.tile_manager.get_tiles(tile1, tile2)
        # chunk_tiles being None also means that the chunk wasn't fully explored
        if chunk_tiles is not None and np.sum(chunk_tiles != 0) >= self._THRESHOLD_FOR_EXPLORED:
            self.explored_chunks.add(chunk_index)
        
        if self.debug:
            # files = glob.glob(debug_folder_path + "*.png")
            # if len(files) == 0:
            #     start = 0
            # else:
            #     nums = [int(Path(f).name.split(".")[0].split("_")[0]) for f in files]
            #     nums.sort()
            #     start = nums[-1] + 1
            # # we just want to save the result with the name being the next available integer
            # output_path = Path(debug_folder_path)
            # debug_image_out = output_path / f"{start}.png"
            # raw_image_out = output_path / f"{start}_raw.png"

            new_width = SEGMENTATION_INPUT_SIZE[0] + len(y_lines)
            new_height = SEGMENTATION_INPUT_SIZE[1] + len(x_lines)
            color_dict = get_color_representation_dict()
            debug_image_arr = np.zeros((new_width, new_height), dtype=np.uint8)

            palette = [0]*256*3
            for c, color_info in color_dict.items():
                if color_info[0] is not None:
                    palette[c*3:c*3+3] = color_info[0] # [0] is array, [1] is hex representation
            palette[-3:] = [255, 0, 0] # color for border between tiles

            for i in range(len(x_lines)-1):
                x1 = x_lines[i]
                x2 = x_lines[i+1]
                for j in range(len(y_lines)-1):
                    y1 = y_lines[j]
                    y2 = y_lines[j+1]
                    cur_chunk = warped_image[x1:x2, y1:y2]
                    debug_image_arr[x1+i+1:x2+i+1, y1+j+1:y2+j+1] = cur_chunk
            
            for i, x_line in enumerate(x_lines):
                debug_image_arr[x_line+i, :] = 255 # border color
            
            for i, y_line in enumerate(y_lines):
                debug_image_arr[:, y_line+i] = 255 # border color

            
            debug_image = Image.fromarray(debug_image_arr.transpose(), mode="P") # transposing since the game coordinate system has x down and z right
            debug_image.putpalette(palette, rawmode="RGB")
            # debug_image.save(debug_image_out)
            self.latest_debug_image = debug_image

    @staticmethod
    def point_to_chunk_index(p : Point2d) -> tuple[int, int]:
        """Convert a point to its corresponding chunk index

        :param p: point to be converted
        :type p: Point2d
        :return: chunk index
        :rtype: tuple[int, int]
        """
        return (math.floor(p.x1/CHUNK_SIZE), math.floor(p.x2/CHUNK_SIZE))
    
    def remove_object_from_chunk_lists(self, obj : ObjectModel) -> None:
        """Removes object from self.objects_by_chunks

        :param obj: object to be removed
        :type obj: ObjectModel
        """
        for chunk_list in self.objects_by_chunks.values():
            if obj in chunk_list:
                chunk_list.remove(obj)
                return

    def required_nearby_chunks(self, p : Point2d) -> list[tuple[int, int]]:
        """Calculates which nearby chunks should be checked for nearby objects (two close objects could be in 
        different chunks if close to a border)

        :param p: object position
        :type p: Point2d
        :return: list of required chunks
        :rtype: list[tuple[int, int]]
        """
        cur = self.point_to_chunk_index(p)
        chunk_pos = self.coords_to_chunk_coords(p)
        required = []
        if chunk_pos.x1 <= DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0]-1, cur[1]))
        elif chunk_pos.x1 >= CHUNK_SIZE - DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0]+1, cur[1]))
        if chunk_pos.x2 <= DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0], cur[1]-1))
        elif chunk_pos.x2 >= CHUNK_SIZE - DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0], cur[1]+1))
        if chunk_pos.distance(Point2d(0, 0)) <= DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0]-1, cur[1]-1))
        if chunk_pos.distance(Point2d(0, CHUNK_SIZE)) <= DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0]-1, cur[1]+1))
        if chunk_pos.distance(Point2d(CHUNK_SIZE, 0)) <= DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0]+1, cur[1]-1))
        if chunk_pos.distance(Point2d(CHUNK_SIZE, CHUNK_SIZE)) <= DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0]+1, cur[1]+1))
        return required

    def update(self) -> None:
        self.scheduler.update()
        for mob_list in self.mob_lists.values():
            for mob in mob_list:
                mob.update()

    def decide_player_position(self, player_positions : list[Point2d]) -> None:
        """Decide which one of the given possible positions is the real one

        :param player_positions: list of the currently detected player screen positions
        :type player_positions: list[Point2d]
        """
        if len(player_positions) == 0:
            return
        player_pos = None
        best_distance = None
        for possibility in player_positions:
            # if the detected player is that far from the center of the screen, it's a false positive
            distance_to_center = possibility.distance(Point2d(SCREEN_SIZE["width"]//2, SCREEN_SIZE["height"]//2))
            if distance_to_center <= DISTANCE_FOR_VALID_PLAYER_POSITION:
                if player_pos is None:
                    player_pos = possibility
                    best_distance = distance_to_center
                else:
                    if distance_to_center < best_distance:
                        player_pos = possibility
                        best_distance = distance_to_center
        if player_pos is not None:
            self.latest_detected_player_position = player_pos
            self.cycles_since_player_detected = 0

    def handle_yolo_info(self, obj_list : list[ImageObject], past_player_position : Point2d) -> tuple[list[float], list[float], list[ImageObject]]:
        """Prepares the WorldModel to process the detected objects and returns a list of object positions

        :param obj_list: list of objects detected by the Perception layer
        :type obj_list: list[ImageObject]
        :param past_player_position: estimated player position at the screenshot time
        :type past_player_position: Point2d
        :return: list of object screen positions, list of object xy coordinates and list of image_objs
        :rtype: tuple[list[float], list[float], list[ImageObject]]
        """
        self.start_cycle(past_player_position)
        detections = []
        converted_detections = []
        image_objs = []
        for obj in obj_list:
            if objects_info.get_item_info(image_id=obj.id, info="object_type") == "OBJECT":
                pos = self.object_detected(obj)
                # converting from global to local position for SLAM
                pos = pos - past_player_position
                # for pos, x1 is x and x2 is z
                bottom_box_point = Point2d.bottom_from_box(obj.box)
                detections.extend([bottom_box_point.x1, bottom_box_point.x2])
                converted_detections.extend([pos.x1, pos.x2])
                image_objs.append(obj)
            elif objects_info.get_item_info(image_id=obj.id, info="object_type") == "MOB":
                self.mob_detected(obj)
        
        return detections, converted_detections, image_objs


    def start_cycle(self, past_player_position : Point2d, heading : float = CAMERA_HEADING, pitch : float = CAMERA_PITCH, 
                    distance : float = CAMERA_DISTANCE, fov : float = FOV, follow_height : float = FOLLOW_HEIGHT) -> None:
        """Updates origin position and sets objects that should be detected
        :param past_player_position: player position estimate at the screenshot moment
        :type past_player_position: Point2d
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

        """
        # if it's been more than 10 cycles since the last time the player was detected, we'll assume 
        # that the camera is above the player
        if self.cycles_since_player_detected > 10 or self.latest_detected_player_position is None:
            self.origin_coordinates = past_player_position
        else:
            # pos in (x, z) in world coords
            pos = local_to_almost_global_position(self.latest_detected_player_position, heading, pitch, distance, fov, follow_height)
            self.origin_coordinates = past_player_position - pos
        # corners of the trapezoid that we are seeing
        self.c1 = self.local_to_global_position(Point2d(0, 0), heading, pitch, distance, fov, follow_height)
        self.c2 = self.local_to_global_position(Point2d(0, SCREEN_SIZE["height"]), heading, pitch, distance, fov, follow_height)
        self.c3 = self.local_to_global_position(Point2d(SCREEN_SIZE["width"], SCREEN_SIZE["height"]), heading, pitch, distance, fov, follow_height)
        self.c4 = self.local_to_global_position(Point2d(SCREEN_SIZE["width"], 0), heading, pitch, distance, fov, follow_height)
        self.c1_deletion_border = self.local_to_global_position(Point2d(SCREEN_SIZE["width"]*0.1, SCREEN_SIZE["height"]*0.1), 
                                                                heading, pitch, distance, fov, follow_height)
        self.c2_deletion_border = self.local_to_global_position(Point2d(SCREEN_SIZE["width"]*0.1, SCREEN_SIZE["height"]*0.9), 
                                                                heading, pitch, distance, fov, follow_height)
        self.c3_deletion_border = self.local_to_global_position(Point2d(SCREEN_SIZE["width"]*0.9, SCREEN_SIZE["height"]*0.9), 
                                                                heading, pitch, distance, fov, follow_height)
        self.c4_deletion_border = self.local_to_global_position(Point2d(SCREEN_SIZE["width"]*0.9, SCREEN_SIZE["height"]*0.1), 
                                                                heading, pitch, distance, fov, follow_height)
        # chunks in the trapezoid view
        cur_chunk_list = self.get_current_chunks()
        # objects in our modeling that should be currently rendered, paired with a flag indicating 
        cur_obj_list = []
        for chunk in cur_chunk_list:
            # if the chunk exists in our modeling (there are objects in our WorldModel that are in that chunk), 
            # we get all the objects that should be currently rendered
            if chunk in self.objects_by_chunks:
                cur_obj_list.extend([[obj, False] for obj in self.objects_by_chunks[chunk] 
                                                if is_inside_convex_polygon([self.c1, self.c2, self.c3, self.c4], obj.position())])
        self.objects_detected_this_cycle = cur_obj_list
        cur_mob_list = []
        for mob_list in self.mob_lists.values():
            cur_mob_list.extend([[mob, False] for mob in mob_list])
        self.mobs_detected_this_cycle = cur_mob_list
        # add recent objects to the list that we're going to observe whether we detect them this cycle
        self.objects_detected_this_cycle.extend([[pair[0], False] for pair in self.recent_objects])
        # add recent mobs to the list that we're going to observe whether we detect them this cycle
        self.mobs_detected_this_cycle.extend([[pair[0], False] for pair in self.recent_mobs])
        self.additions_to_recent_objects = []
        self.additions_to_recent_mobs = []

    def local_to_global_position(self, local_position : Point2d, heading : float, pitch : float, 
                                 distance : float, fov : float, follow_height : float) -> Point2d:
        """Converts the local position (2d image position) to the global position (could be 3d, 
        but everything is on the ground)

        :param local_position: object position relative to the top left corner
        :type local_position: Point2d
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
        :return: position in the world's coordinate system
        :rtype: Point2d
        """
        pos = local_to_almost_global_position(local_position, heading, pitch, distance, fov, follow_height)

        return self.origin_coordinates + pos

    def object_detected(self, image_obj : ImageObject) -> Point2d:
        # anchor points are usually at the bottom (y) and middle (x)
        pos = self.local_to_global_position(
            Point2d.bottom_from_box(image_obj.box),
            CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV, FOLLOW_HEIGHT)
        
        return pos

    def create_object(self, image_obj : ImageObject, slam_state_index : int) -> ObjectModel: 
        # in this case, I just identified something that's not in the WorldModel yet, so I create a new object1
        obj = factory.create_object(image_obj.id, self.modeling, slam_state_index, image_obj.box, self.slam_index_manager, self.scheduler)

        self.additions_to_recent_objects.append([obj, 1])
        return obj

    def matched_object(self, obj : ObjectModel, image_obj : ImageObject) -> None:
        obj.latest_screen_position = image_obj.box
        # in this case, I identified an object that's already in my WorldModel or in the recent objects list
        if obj in [pair[0] for pair in self.objects_detected_this_cycle]:
            obj_index = [pair[0] for pair in self.objects_detected_this_cycle].index(obj)
            self.objects_detected_this_cycle[obj_index][1] = True
        if isinstance(obj, ObjectWithMultipleForms):
            obj.handle_object_detected(image_obj.id)

    def mob_detected(self, image_obj : ImageObject) -> None:
        # anchor points are usually at the bottom (y) and middle (x)
        pos = self.local_to_global_position(
            Point2d.bottom_from_box(image_obj.box),
            CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV, FOLLOW_HEIGHT)
        self.handle_mob_at_position(image_obj, pos)
    

    def handle_mob_at_position(self, image_obj : ImageObject, pos : Point2d) -> None:
        obj_name = objects_info.get_item_info(info="name", image_id=image_obj.id)
        mobs_to_analyze : list[MobModel]= []
        
        # getting object from pair (obj, cycle_count)
        mobs_to_analyze.extend([pair[0] for pair in self.recent_mobs])

        best_match : MobModel = None
        lowest_distance : float = None
        for mob in mobs_to_analyze:
            # if the object is close enough to an already detected object of the same type
            if pos.distance(mob.position) <= DISTANCE_FOR_SAME_MOB and mob.name_str() == obj_name:
                if best_match is None or mob.position.distance(pos) < lowest_distance:
                    best_match = mob
                    lowest_distance = mob.position.distance(pos)
        
        if best_match is None:
            # in this case, I just identified something that's not in the WorldModel yet, so I create a new object1
            obj = factory.create_mob(image_obj.id, pos, image_obj.box)

            self.additions_to_recent_mobs.append([obj, 1])
        else:
            best_match.latest_screen_position = image_obj.box
            # in this case, I identified an object that's already in my WorldModel or in the recent objects list
            if best_match in [pair[0] for pair in self.mobs_detected_this_cycle]:
                obj_index = [pair[0] for pair in self.mobs_detected_this_cycle].index(best_match)
                self.mobs_detected_this_cycle[obj_index][1] = True
                # if it's in the recent objects list, update its position
                if best_match in [pair[0] for pair in self.recent_mobs]:
                    # maybe there's a better way, but for now just update its position
                    best_match.position = pos
            best_match.handle_mob_detected(image_obj.id)

    def finish_cycle(self) -> None:
        """Marks the end of a modeling cycle, this should be called in the end of update_model() on Modeling.
        It also removes objects that were not detected and should be.
        """
        self.cycles_since_player_detected += 1
        for pair in self.objects_detected_this_cycle:
            obj = pair[0]
            detected = pair[1]
            # handling the case in which obj is a recent object
            if obj in [pair[0] for pair in self.recent_objects]:
                obj_index = [pair[0] for pair in self.recent_objects].index(obj)
                if detected:
                    new_count = self.recent_objects[obj_index][1]+1
                    # if the required number of cycles to admit an object is met, add it to both object_lists and objects_by_chunks
                    if new_count == CYCLES_TO_ADMIT_OBJECT:
                        self.add_object(obj)
                        # also remove it from recent objects
                        del self.recent_objects[obj_index]
                    else:
                        # update the cycle count for the object
                        self.recent_objects[obj_index][1] = new_count
                else:
                    # if the object wasn't detected, we remove it
                    self.modeling.remove_from_slam_state(obj.slam_state_index())
                    print(f"before recent objects deletion: {len(self.recent_objects)}")
                    del self.recent_objects[obj_index]
                    print(f"after recent objects deletion: {len(self.recent_objects)}")
                    # update index to object mapping
                    index_ = (obj.slam_state_index() - 2) // 2
                    assert self.modeling.lm_id_to_object[index_] == obj
                    del self.modeling.lm_id_to_object[index_]
                    self.slam_index_manager.remove_object(obj)
            # handling the case in which obj is a world model object (object removal if it wasn't detected for
            # many cycles in a row)
            else:
                if detected:
                    obj.reset_cycles_to_be_deleted()
                else:
                    # we make it so that objects on the screen border aren't deleted if they aren't seen for a while
                    # since they often are offscreen or blocked by HUD
                    if is_inside_convex_polygon([self.c1_deletion_border, 
                                                    self.c2_deletion_border,
                                                    self.c3_deletion_border, 
                                                    self.c4_deletion_border], obj.position()):
                        # we shouldn't count down an object for deletion if we're hovering over it
                        if obj != self.hovering_object:
                            obj.countdown_cycles_to_be_deleted()
                            if obj.get_cycles_to_be_deleted() == 0:
                                self.remove_object(obj)
                                self.modeling.remove_from_slam_state(obj.slam_state_index())
                                # update index to object mapping
                                index_ = (obj.slam_state_index() - 2) // 2
                                assert self.modeling.lm_id_to_object[index_] == obj
                                del self.modeling.lm_id_to_object[index_]
                                self.slam_index_manager.remove_object(obj)
                        del obj

        for pair in self.mobs_detected_this_cycle:
            mob = pair[0]
            detected = pair[1]
            # handling the case in which mob is a recent object
            if mob in [pair[0] for pair in self.recent_mobs]:
                mob_index = [pair[0] for pair in self.recent_mobs].index(mob)
                if detected:
                    new_count = self.recent_mobs[mob_index][1]+1
                    # if the required number of cycles to admit a mob is met, add it to both object_lists and objects_by_chunks
                    if new_count == CYCLES_TO_ADMIT_MOB:
                        self.add_mob(mob)
                        # also remove it from recent objects
                        del self.recent_mobs[mob_index]
                    else:
                        # update the cycle count for the object
                        self.recent_mobs[mob_index][1] = new_count
                else:
                    # if the object wasn't detected, we remove it
                    del self.recent_mobs[mob_index]
            # handling the case in which mob is a world model object (object removal if it wasn't detected for
            # many cycles in a row)
            else:
                if detected:
                    mob.reset_cycles_to_be_deleted()
                else:
                    # we make it so that objects on the screen border aren't deleted if they aren't seen for a while
                    # since they often are offscreen or blocked by HUD
                    if is_inside_convex_polygon([self.c1_deletion_border, 
                                                    self.c2_deletion_border,
                                                    self.c3_deletion_border, 
                                                    self.c4_deletion_border], mob.position):
                        # we shouldn't count down an object for deletion if we're hovering over it
                        if mob != self.hovering_object:
                            mob.countdown_cycles_to_be_deleted()
                            if mob.get_cycles_to_be_deleted() == 0:
                                mob_name = mob.name_str()
                                mob_list = self.mob_lists[mob_name]
                                mob_index = mob_list.index(mob)
                                del mob_list[mob_index]

        # adding new recent objects 
        self.recent_objects.extend(self.additions_to_recent_objects)

    # def recheck_object_chunk(self, obj : ObjectModel, pos : tuple[int, int], prev_pos : tuple[int, int]) -> None:
    #     """Checks if an object is on the correct chunk and moves it if necessary

    #     :param obj: object that has had its position changed
    #     :type obj: ObjectModel
    #     :param pos: position the object has after the change
    #     :type pos: tuple[int, int]
    #     :param prev_pos: position the object had before the change
    #     :type prev_pos: tuple[int, int]
    #     """
    #     # return if the object is still recent cause that means it's not in the chunk lists
    #     if obj in [pair[0] for pair in self.recent_objects]:
    #         return
    #     pos = Point2d(pos[0], pos[1])
    #     chunk_index = self.point_to_chunk_index(pos)
    #     prev_chunk_index = self.point_to_chunk_index(Point2d(prev_pos[0], prev_pos[1]))
    #     print(f"Comparing pos {pos.x1:.2f}, {pos.x2:.2f} to prev_pos {prev_pos[0]:.2f}, {prev_pos[1]:.2f}")
    #     if chunk_index != prev_chunk_index:
    #         print(f"Changed chunk from {prev_chunk_index} to {chunk_index}")
    #         chunk_obj_list = self.objects_by_chunks[prev_chunk_index]
    #         obj_index_in_chunk_list = chunk_obj_list.index(obj)
    #         del chunk_obj_list[obj_index_in_chunk_list]
    #         if chunk_index in self.objects_by_chunks:
    #             self.objects_by_chunks[chunk_index].append(obj)
    #         else:
    #             self.objects_by_chunks[chunk_index] = [obj]


    def get_closest_unexplored_chunk(self) -> tuple[int, int]:
        """Get closest unexplored chunk

        :return: chunk index of the closest unexplored chunk
        :rtype: tuple[int, int]
        """
        di = [-1, 0, 1, 0]
        dj = [0, 1, 0, -1]
        used_list = set()
        potential_list = queue.Queue()
        chunk_aux = self.point_to_chunk_index(self.modeling.player_position())
        while True:
            if chunk_aux not in self.explored_chunks:
                break
            for k in range(4):
                if (chunk_aux[0] + di[k], chunk_aux[1] + dj[k]) not in used_list:
                    potential_list.put((chunk_aux[0] + di[k], chunk_aux[1] + dj[k]))
            used_list.add(chunk_aux)
            chunk_aux = potential_list.get()

        return chunk_aux


    def get_current_chunks(self) -> list[tuple[int, int]]:
        """Gets chunks that could have objects being currently rendered

        :return: list of chunk indices (i, j)
        :rtype: list[tuple[int, int]]
        """
        min_x1 = min([self.c1.x1, self.c2.x1, self.c3.x1, self.c4.x1])
        max_x1 = max([self.c1.x1, self.c2.x1, self.c3.x1, self.c4.x1])
        min_x2 = min([self.c1.x2, self.c2.x2, self.c3.x2, self.c4.x2])
        max_x2 = max([self.c1.x2, self.c2.x2, self.c3.x2, self.c4.x2])
        chunk_1 = self.point_to_chunk_index(Point2d(min_x1, min_x2))
        chunk_2 = self.point_to_chunk_index(Point2d(max_x1, min_x2))
        chunk_3 = self.point_to_chunk_index(Point2d(max_x1, max_x2))
        chunk_4 = self.point_to_chunk_index(Point2d(min_x1, max_x2))
        return [chunk_1, chunk_2, chunk_3, chunk_4]

    def set_hovering_over(self, obj : ObjectModel):
        self.hovering_object = obj

    # returns dict of objects
    def get_all_of(self, obj_list : list[str], filter_ : str = None) -> dict[str, list[ObjectModel]]:
        """Get all of objects of the requested types, possibly filtered by some criteria

        :param obj_list: list of object names
        :type obj_list: list[str]
        :param filter_: filter name, defaults to None
        :type filter_: str, optional
        :raises ValueError: _description_
        :return: dict with keys being object names and values being lists of objects
        :rtype: dict[str, list[ObjectModel]]
        """
        result = {}
        for obj in obj_list:
            if obj in self.object_lists.keys():
                if filter_ is None:
                    result[obj] = self.object_lists[obj]
                else:
                    if filter_ == "only_not_harvested":
                        res_aux = []
                        for obj_aux in self.object_lists[obj]:
                            # if the object has the is_harvested method, we can choose it
                            op = getattr(obj_aux, "is_harvested", None)
                            if callable(op):
                                if not obj_aux.is_harvested():
                                    res_aux.append(obj_aux)
                            else:
                                res_aux.append(obj_aux)
                        result[obj] = res_aux
                    elif filter_ == "evergreen_small":
                        res_aux = []
                        for obj_aux in self.object_lists[obj]:
                            # if the object has the is_small method, we can choose it
                            op = getattr(obj_aux, "is_small", None)
                            if callable(op):
                                if obj_aux.is_small():
                                    res_aux.append(obj_aux)
                            else:
                                res_aux.append(obj_aux)
                        result[obj] = res_aux
                    elif filter_ == "evergreen_medium":
                        res_aux = []
                        for obj_aux in self.object_lists[obj]:
                            # if the object has the is_medium method, we can choose it
                            op = getattr(obj_aux, "is_medium", None)
                            if callable(op):
                                if obj_aux.is_medium():
                                    res_aux.append(obj_aux)
                            else:
                                res_aux.append(obj_aux)
                        result[obj] = res_aux
                    elif filter_ == "evergreen_big":
                        res_aux = []
                        for obj_aux in self.object_lists[obj]:
                            # if the object has the is_big method, we can choose it
                            op = getattr(obj_aux, "is_big", None)
                            if callable(op):
                                if obj_aux.is_big():
                                    res_aux.append(obj_aux)
                            else:
                                res_aux.append(obj_aux)
                        result[obj] = res_aux
                    elif filter_ == "evergreen_dead":
                        res_aux = []
                        for obj_aux in self.object_lists[obj]:
                            # if the object has the is_dead method, we can choose it
                            op = getattr(obj_aux, "is_dead", None)
                            if callable(op):
                                if obj_aux.is_dead():
                                    res_aux.append(obj_aux)
                            else:
                                res_aux.append(obj_aux)
                        result[obj] = res_aux
                    elif filter_ == "nest_small":
                        res_aux = []
                        for obj_aux in self.object_lists[obj]:
                            # if the object has the is_small method, we can choose it
                            op = getattr(obj_aux, "is_small", None)
                            if callable(op):
                                if obj_aux.is_small():
                                    res_aux.append(obj_aux)
                            else:
                                res_aux.append(obj_aux)
                        result[obj] = res_aux
                    elif filter_ == "nest_medium":
                        res_aux = []
                        for obj_aux in self.object_lists[obj]:
                            # if the object has the is_medium method, we can choose it
                            op = getattr(obj_aux, "is_medium", None)
                            if callable(op):
                                if obj_aux.is_medium():
                                    res_aux.append(obj_aux)
                            else:
                                res_aux.append(obj_aux)
                        result[obj] = res_aux
                    elif filter_ == "nest_big":
                        res_aux = []
                        for obj_aux in self.object_lists[obj]:
                            # if the object has the is_big method, we can choose it
                            op = getattr(obj_aux, "is_big", None)
                            if callable(op):
                                if obj_aux.is_big():
                                    res_aux.append(obj_aux)
                            else:
                                res_aux.append(obj_aux)
                        result[obj] = res_aux
                    else:
                        raise ValueError("Filter not implemented")
            else:
                result[obj] = []
        
        return result
    
    def add_object(self, obj : ObjectModel) -> None:
        """Add object to world model

        :param obj: object to be added
        :type obj: ObjectModel
        """
        obj_name = obj.name_str()
        if obj_name in self.object_lists:
            self.object_lists[obj_name].append(obj)
        else:
            self.object_lists[obj_name] = [obj]
        pos = obj.position()
        if self.point_to_chunk_index(pos) in self.objects_by_chunks:
            self.objects_by_chunks[self.point_to_chunk_index(pos)].append(obj)
        else:
            self.objects_by_chunks[self.point_to_chunk_index(pos)] = [obj]
    
    def add_mob(self, mob : MobModel) -> None:
        """Add object to world model

        :param mob: mob to be added
        :type mob: MobModel
        """
        mob_name = mob.name_str()
        if mob_name in self.object_lists:
            self.object_lists[mob_name].append(mob)
        else:
            self.object_lists[mob_name] = [mob]

    def H_function(self, x : float, z : float,
            heading : float = CAMERA_HEADING, pitch : float = CAMERA_PITCH, distance : float = CAMERA_DISTANCE, 
            fov : float = FOV) -> tuple[float, float]:
        c_u = SCREEN_SIZE["width"]/2
        c_v = SCREEN_SIZE["height"]/2
        heading = heading*math.pi/180
        pitch = pitch*math.pi/180
        sin_heading = math.sin(heading)
        cos_heading = math.cos(heading)
        sin_pitch = math.sin(pitch)
        cos_pitch = math.cos(pitch)
        f = SCREEN_SIZE["height"]/(2*math.tan(fov/180*math.pi/2))
        temp1 = ((-f*sin_heading-c_u*cos_pitch*cos_heading)*x+(f*cos_heading-c_u*cos_pitch*sin_heading)*z
                 +c_u*(distance+FOLLOW_HEIGHT*sin_pitch))
        temp2 = ((f*sin_pitch*cos_heading-c_v*cos_pitch*cos_heading)*x+(f*sin_pitch*sin_heading-c_v*cos_pitch*sin_heading)*z
                 +c_v*(distance+FOLLOW_HEIGHT*sin_pitch)+f*FOLLOW_HEIGHT*cos_pitch)
        temp3 = -cos_pitch*cos_heading*x-cos_pitch*sin_heading*z+distance+FOLLOW_HEIGHT*sin_pitch
        
        u = temp1/temp3
        v = temp2/temp3
        return (u, v)

    def jacobH_numerical(self, x : float, z : float,
            heading : float = CAMERA_HEADING, pitch : float = CAMERA_PITCH, distance : float = CAMERA_DISTANCE, 
            fov : float = FOV) -> np.ndarray:
        eps = 1e-4
        t1 = self.H_function(x-eps, z, heading, pitch, distance, fov)
        t2 = self.H_function(x+eps, z, heading, pitch, distance, fov)
        t3 = self.H_function(x, z-eps, heading, pitch, distance, fov)
        t4 = self.H_function(x, z+eps, heading, pitch, distance, fov)
        u_x = (t2[0] - t1[0])/(2*eps)
        u_z = (t4[0] - t3[0])/(2*eps)
        v_x = (t2[1] - t1[1])/(2*eps)
        v_z = (t4[1] - t3[1])/(2*eps)
        return np.array([
            [u_x, u_z],
            [v_x, v_z]
        ])

    def jacobH(self, x : float, z : float,
            heading : float = CAMERA_HEADING, pitch : float = CAMERA_PITCH, distance : float = CAMERA_DISTANCE, 
            fov : float = FOV) -> np.ndarray:
        c_u = SCREEN_SIZE["width"]/2
        c_v = SCREEN_SIZE["height"]/2
        heading = heading*math.pi/180
        pitch = pitch*math.pi/180
        sin_heading = math.sin(heading)
        cos_heading = math.cos(heading)
        sin_pitch = math.sin(pitch)
        cos_pitch = math.cos(pitch)
        f = SCREEN_SIZE["height"]/(2*math.tan(fov/180*math.pi/2))
        temp1 = ((-f*sin_heading-c_u*cos_pitch*cos_heading)*x+(f*cos_heading-c_u*cos_pitch*sin_heading)*z
                 +c_u*(distance+FOLLOW_HEIGHT*sin_pitch))
        temp2 = ((f*sin_pitch*cos_heading-c_v*cos_pitch*cos_heading)*x+(f*sin_pitch*sin_heading-c_v*cos_pitch*sin_heading)*z
                 +c_v*(distance+FOLLOW_HEIGHT*sin_pitch)+f*FOLLOW_HEIGHT*cos_pitch)
        temp3 = -cos_pitch*cos_heading*x-cos_pitch*sin_heading*z+distance+FOLLOW_HEIGHT*sin_pitch
        temp3_2 = temp3**2
        H = np.array([[((-f*sin_heading-c_u*cos_pitch*cos_heading)*temp3+cos_pitch*cos_heading*temp1)/temp3_2, 
                          ((f*cos_heading-c_u*cos_pitch*sin_heading)*temp3+cos_pitch*sin_heading*temp1)/temp3_2],
                      [((f*sin_pitch*cos_heading-c_v*cos_pitch*cos_heading)*temp3+cos_pitch*cos_heading*temp2)/temp3_2, 
                          ((f*sin_pitch*sin_heading-c_v*cos_pitch*sin_heading)*temp3+cos_pitch*sin_heading*temp2)/temp3_2]])
        return H
    
    def jacob_inverseH(self, u : float, v : float,
            heading : float = CAMERA_HEADING, pitch : float = CAMERA_PITCH, distance : float = CAMERA_DISTANCE, 
            fov : float = FOV) -> np.ndarray:
        c_u = SCREEN_SIZE["width"]/2
        c_v = SCREEN_SIZE["height"]/2
        u_c = u - c_u
        v_c = v - c_v
        heading = heading*math.pi/180
        pitch = pitch*math.pi/180
        sin_heading = math.sin(heading)
        cos_heading = math.cos(heading)
        sin_pitch = math.sin(pitch)
        cos_pitch = math.cos(pitch)
        f = SCREEN_SIZE["height"]/(2*math.tan(fov/180*math.pi/2))

        temp1 = distance*sin_pitch+FOLLOW_HEIGHT
        temp2 = distance+FOLLOW_HEIGHT*sin_pitch
        temp3 = cos_pitch*v_c+f*sin_pitch
        temp4 = cos_pitch*sin_heading*f*FOLLOW_HEIGHT
        x_u = -sin_heading*temp1/temp3
        x_v = (cos_heading*temp2*temp3-cos_pitch*(-sin_heading*temp1*u_c+cos_heading*temp2*v_c-temp4))/temp3**2
        z_u = cos_heading*temp1/temp3
        z_v = (sin_heading*temp2*temp3-cos_pitch*(cos_heading*temp1*u_c+sin_heading*temp2*v_c-temp4))/temp3**2

        return np.array([
            [x_u, x_v],
            [z_u, z_v]
        ])
        

class WorldModelTimer(WorldModel):
    def __init__(self, modeling: Modeling, clock: Clock, debug: bool = False):
        super().__init__(modeling, clock, debug)
        self.time_records_list = []

    def remove_object(self, instance: ObjectModel) -> None:
        t1 = time.time_ns()
        super().remove_object(instance)
        t2  = time.time_ns()
        self.time_records_list.append(("remove_object", t2-t1))
    
    def warp_image_to_ground(self, image: np.ndarray, heading: float, pitch: float, distance: float, fov: float) -> tuple[np.ndarray, tuple[float, float], tuple[float, float]]:
        t1 = time.time_ns()
        return_value = super().warp_image_to_ground(image, heading, pitch, distance, fov)
        t2  = time.time_ns()
        self.time_records_list.append(("warp_image_to_ground", t2-t1))
        return return_value
    
    def process_segmentation_image(self, image: np.ndarray, past_player_position: Point2d) -> Image:
        t1 = time.time_ns()
        return_value = super().process_segmentation_image(image, past_player_position)
        t2  = time.time_ns()
        self.time_records_list.append(("process_segmentation_image", t2-t1))
        return return_value
    
    def required_nearby_chunks(self, p: Point2d) -> list[tuple[int, int]]:
        t1 = time.time_ns()
        return_value = super().required_nearby_chunks(p)
        t2  = time.time_ns()
        self.time_records_list.append(("required_nearby_chunks", t2-t1))
        return return_value
    
    def update(self) -> None:
        t1 = time.time_ns()
        super().update()
        t2  = time.time_ns()
        self.time_records_list.append(("update", t2-t1))
    
    def decide_player_position(self, player_positions: list[Point2d]) -> None:
        t1 = time.time_ns()
        super().decide_player_position(player_positions)
        t2  = time.time_ns()
        self.time_records_list.append(("decide_player_position", t2-t1))
    
    def handle_yolo_info(self, obj_list: list[ImageObject], past_player_position: Point2d) -> tuple[list[float], list[ImageObject]]:
        t1 = time.time_ns()
        return_value = super().handle_yolo_info(obj_list, past_player_position)
        t2  = time.time_ns()
        self.time_records_list.append(("handle_yolo_info", t2-t1))
        return return_value
    
    def start_cycle(self, past_player_position: Point2d, 
                    heading: float = CAMERA_HEADING, pitch: float = CAMERA_PITCH, distance: float = CAMERA_DISTANCE, 
                    fov: float = FOV) -> None:
        t1 = time.time_ns()
        super().start_cycle(past_player_position, heading, pitch, distance, fov)
        t2  = time.time_ns()
        self.time_records_list.append(("start_cycle", t2-t1))
    
    def local_to_global_position(self, local_position: Point2d, heading: float, pitch: float, 
                                 distance: float, fov: float, follow_height : float) -> Point2d:
        t1 = time.time_ns()
        return_value = super().local_to_global_position(local_position, heading, pitch, distance, fov, follow_height)
        t2  = time.time_ns()
        self.time_records_list.append(("local_to_global_position", t2-t1))
        return return_value
    
    def create_object(self, image_obj: ImageObject, slam_state_index: int) -> ObjectModel:
        t1 = time.time_ns()
        return_value = super().create_object(image_obj, slam_state_index)
        t2  = time.time_ns()
        self.time_records_list.append(("create_object", t2-t1))
        return return_value
    
    def matched_object(self, obj: ObjectModel, image_obj: ImageObject) -> None:
        t1 = time.time_ns()
        super().matched_object(obj, image_obj)
        t2  = time.time_ns()
        self.time_records_list.append(("matched_object", t2-t1))
    
    def mob_detected(self, image_obj: ImageObject) -> None:
        t1 = time.time_ns()
        super().mob_detected(image_obj)
        t2  = time.time_ns()
        self.time_records_list.append(("mob_detected", t2-t1))
    
    def handle_mob_at_position(self, image_obj: ImageObject, pos: Point2d) -> None:
        t1 = time.time_ns()
        super().handle_mob_at_position(image_obj, pos)
        t2  = time.time_ns()
        self.time_records_list.append(("handle_mob_at_position", t2-t1))
    
    def finish_cycle(self) -> None:
        t1 = time.time_ns()
        super().finish_cycle()
        t2  = time.time_ns()
        self.time_records_list.append(("finish_cycle", t2-t1))
    
    # def recheck_object_chunk(self, obj: ObjectModel, pos: tuple[int, int], prev_pos: tuple[int, int]) -> None:
    #     t1 = time.time_ns()
    #     super().recheck_object_chunk(obj, pos, prev_pos)
    #     t2  = time.time_ns()
    #     self.time_records_list.append(("recheck_object_chunk", t2-t1))
    
    def get_closest_unexplored_chunk(self) -> tuple[int, int]:
        t1 = time.time_ns()
        return_value = super().get_closest_unexplored_chunk()
        t2  = time.time_ns()
        self.time_records_list.append(("get_closest_unexplored_chunk", t2-t1))
        return return_value
    
    def get_current_chunks(self) -> list[tuple[int, int]]:
        t1 = time.time_ns()
        return_value = super().get_current_chunks()
        t2  = time.time_ns()
        self.time_records_list.append(("get_current_chunks", t2-t1))
        return return_value
    
    def get_all_of(self, obj_list: list[str], filter_: str = None) -> dict[str, list[ObjectModel]]:
        t1 = time.time_ns()
        return_value = super().get_all_of(obj_list, filter_)
        t2  = time.time_ns()
        self.time_records_list.append(("get_all_of", t2-t1))
        return return_value
    
    def add_object(self, obj : ObjectModel) -> None:
        t1 = time.time_ns()
        super().add_object(obj)
        t2  = time.time_ns()
        self.time_records_list.append(("add_object", t2-t1))
    
    def add_mob(self, mob : MobModel) -> None:
        t1 = time.time_ns()
        super().add_mob(mob)
        t2  = time.time_ns()
        self.time_records_list.append(("add_mob", t2-t1))

class WorldModelSlamMock(WorldModel):
    def __init__(self, modeling: Modeling, clock: Clock, debug: bool = False):
        super().__init__(modeling, clock, debug)
    
    def matched_object(self, obj: ObjectModel, image_obj: ImageObject) -> None:
        pass
    
    # def recheck_object_chunk(self, obj: ObjectModel, pos: tuple[int, int], prev_pos: tuple[int, int]) -> None:
    #     pass

    
