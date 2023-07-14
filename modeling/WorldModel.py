import heapq
import math
import time
import queue

from perception.ImageObject import ImageObject
from modeling.PlayerModel import PlayerModel
from modeling.objects.ObjectModel import ObjectModel
from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from modeling.Factory import factory
from modeling.constants import DISTANCE_FOR_SAME_OBJECT, DISTANCE_FOR_SAME_MOB, CYCLES_FOR_OBJECT_REMOVAL, CYCLES_TO_ADMIT_OBJECT
from modeling.constants import FOV, CAMERA_DISTANCE, CAMERA_PITCH, CAMERA_HEADING, CHUNK_SIZE, DISTANCE_FOR_VALID_PLAYER_POSITION
from modeling.ObjectsInfo import objects_info
from perception.constants import SCREEN_SIZE
from utility.Clock import Clock
from utility.Point2d import Point2d
from utility.utility import is_inside_convex_polygon


class WorldModel:
    def __init__(self, player : PlayerModel, clock : Clock):
        """Generates the world model. It should be noted that the full workflow for a cycle of updating is:
            - if player was detected (on perception), call player_detected()
            - call start_cycle()
            - for each object detected, call object_detected()
            - after all that, call finish_cycle()

        :param player: the player model
        :type player: PlayerModel
        :param clock: a clock to keep track of how much time passed since the last update
        :type clock: Clock
        """
        # map of object lists, the first index represents an object id and
        # object_list[id] has the objects with that id
        self.local_objects = []
        # maps object name to the object list
        self.object_lists = {}
        # objects_by_chunks maps a chunk index to a list of objects in it
        # (x1, x2) -> list
        self.objects_by_chunks : dict[tuple[int, int], list[ObjectModel]] = {}
        self.mob_list = set()
        self.explored_chunks = set()
        # update_queue has (time, object_id, index, change)
        self.update_queue = []
        self.detected_this_cycle : list[list[ObjectModel, bool]] = {}
        self.player : PlayerModel = player
        self.latest_detected_player_position : Point2d = None
        self.cycles_since_player_detected : int = 0
        self.origin_coordinates : Point2d = player.position
        self.clock : Clock = clock
        self.c1 : Point2d = None
        self.c2 : Point2d = None
        self.c3 : Point2d = None
        self.c4 : Point2d = None
        self.c1_deletion_border : Point2d = None
        self.c2_deletion_border : Point2d = None
        self.c3_deletion_border : Point2d = None
        self.c4_deletion_border : Point2d = None
        self.estimation_errors : list[Point2d] = []
        self.estimation_pairs : list[tuple[str, Point2d, Point2d]] = []
        self.avg_observed_error : Point2d = None
        self.recent_objects : list[list[ObjectModel, int]] = []
        self.additions_to_recent_objects : list[list[ObjectModel, int]] = []
        self.hovering_object : ObjectModel = None

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

    def decide_if_explored(self, player_position : Point2d) -> bool:
        """Calculates if the current chunk should be considered explored

        :param player_position: current player position
        :type player_position: Point2d
        :return: whether it should be considered explored
        :rtype: bool
        """
        x1 = player_position.x1 - math.floor(player_position.x1/CHUNK_SIZE)*CHUNK_SIZE
        x2 = player_position.x2 - math.floor(player_position.x2/CHUNK_SIZE)*CHUNK_SIZE
        return x1 > 0.4*CHUNK_SIZE and x1 < 0.6*CHUNK_SIZE and x2 > 0.4*CHUNK_SIZE and x2 < 0.6*CHUNK_SIZE

    @staticmethod
    def point_to_chunk_index(p : Point2d) -> tuple[int, int]:
        """Convert a point to its corresponding chunk index

        :param p: point to be converted
        :type p: Point2d
        :return: chunk index
        :rtype: tuple[int, int]
        """
        return (math.floor(p.x1/CHUNK_SIZE), math.floor(p.x2/CHUNK_SIZE))
    
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
        if chunk_pos.x1 < DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0]-1, cur[1]))
        elif chunk_pos.x1 > CHUNK_SIZE - DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0]+1, cur[1]))
        if chunk_pos.x2 < DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0], cur[1]-1))
        elif chunk_pos.x2 > CHUNK_SIZE - DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0], cur[1]+1))
        if chunk_pos.distance(Point2d(0, 0)) < DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0]-1, cur[1]-1))
        if chunk_pos.distance(Point2d(0, CHUNK_SIZE)) < DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0]-1, cur[1]+1))
        if chunk_pos.distance(Point2d(CHUNK_SIZE, 0)) < DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0]+1, cur[1]-1))
        if chunk_pos.distance(Point2d(CHUNK_SIZE, CHUNK_SIZE)) < DISTANCE_FOR_SAME_OBJECT:
            required.append((cur[0]+1, cur[1]+1))
        return required

    def update(self) -> None:
        # the [0] gets the 'timestamp' in which the change should happen
        while len(self.update_queue) > 0 and self.update_queue[0][0] < self.clock.time():
            tup = heapq.heappop(self.update_queue)
            pos = tup[2]
            change = tup[3]
            instance = tup[4]
            if change == "disappear":
                self.objects_by_chunks[self.point_to_chunk_index(pos)].remove(instance)
                self.object_lists[type(instance).__name__].remove(instance)
            else:
                instance.update(change)

        self.mob_list = set(filter(lambda mob: mob.update_destruction_time(self.clock.dt()), self.mob_list))

    def update_local(self, object_list : list[ImageObject]) -> None:
        self.local_objects = object_list

    # time_delta should be GameTime
    def schedule_update(self, pos : Point2d, creation_time : float, change : str, time_delta : float, instance : ObjectModel) -> None:
        heapq.heappush(self.update_queue, (self.clock.time_from_now(time_delta), creation_time, pos, change, instance))

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
            if distance_to_center < DISTANCE_FOR_VALID_PLAYER_POSITION:
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


    def start_cycle(self, heading : float, pitch : float, distance : float, fov : float) -> None:
        """Updates origin position and sets objects that should be detected
        :param heading: camera heading
        :type heading: float
        :param pitch: camera pitch
        :type pitch: float
        :param distance: camera distance
        :type distance: float
        :param fov: camera FOV
        :type fov: float

        """
        # if it's been more than 10 cycles since the last time the player was detected, we'll assume 
        # that the camera is above the player
        if self.cycles_since_player_detected > 10 or self.latest_detected_player_position is None:
            self.origin_coordinates = self.player.position
        else:
            # pos in (x, z) in world coords
            pos = self.local_to_almost_global_position(self.latest_detected_player_position, heading, pitch, distance, fov)
            self.origin_coordinates = self.player.position - pos
        # corners of the trapezoid that we are seeing
        self.c1 = self.local_to_global_position(Point2d(0, 0), heading, pitch, distance, fov)
        self.c2 = self.local_to_global_position(Point2d(0, SCREEN_SIZE["height"]), heading, pitch, distance, fov)
        self.c3 = self.local_to_global_position(Point2d(SCREEN_SIZE["width"], SCREEN_SIZE["height"]), heading, pitch, distance, fov)
        self.c4 = self.local_to_global_position(Point2d(SCREEN_SIZE["width"], 0), heading, pitch, distance, fov)
        self.c1_deletion_border = self.local_to_global_position(Point2d(SCREEN_SIZE["width"]*0.1, SCREEN_SIZE["height"]*0.1), heading, pitch, distance, fov)
        self.c2_deletion_border = self.local_to_global_position(Point2d(SCREEN_SIZE["width"]*0.1, SCREEN_SIZE["height"]*0.9), heading, pitch, distance, fov)
        self.c3_deletion_border = self.local_to_global_position(Point2d(SCREEN_SIZE["width"]*0.9, SCREEN_SIZE["height"]*0.9), heading, pitch, distance, fov)
        self.c4_deletion_border = self.local_to_global_position(Point2d(SCREEN_SIZE["width"]*0.9, SCREEN_SIZE["height"]*0.1), heading, pitch, distance, fov)
        # chunks in the trapezoid view
        cur_chunk_list = self.get_current_chunks()
        # objects in our modeling that should be currently rendered, paired with a flag indicating 
        cur_obj_list = []
        for chunk in cur_chunk_list:
            # if the chunk exists in our modeling (there are objects in our WorldModel that are in that chunk), 
            # we get all the objects that should be currently rendered
            if chunk in self.objects_by_chunks:
                cur_obj_list.extend([[obj, False] for obj in self.objects_by_chunks[chunk] 
                                                if is_inside_convex_polygon([self.c1, self.c2, self.c3, self.c4], obj.position)])
        self.detected_this_cycle = cur_obj_list
        # add recent objects to the list that we're going to observe whether we detect them this cycle
        self.detected_this_cycle.extend([[pair[0], False] for pair in self.recent_objects])
        self.estimation_errors = []
        self.additions_to_recent_objects = []
        self.estimation_pairs = []

    # positions are Point2d
    def local_to_almost_global_position(self, local_position : Point2d, 
            heading : float, pitch : float, distance : float, fov : float,  
            ) -> Point2d:
        """Converts the local position (2d image position) to an almost global position (could be 3d, 
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
        :return: position in the world's coordinate system, but with the origin in the point in the screen center
        :rtype: Point2d
        """
        # f = H / (2*tan(AFOV/2)), f focal distance, H height, AFOV angular FOV
        f = SCREEN_SIZE["height"]/(2*math.tan(fov/180*math.pi/2))
        # in opencv, y points down and x points to the right, but in our coordinate system x is down and y to the right 
        fx = (local_position.x1 - SCREEN_SIZE["width"]/2)/f
        fy = (local_position.x2 - SCREEN_SIZE["height"]/2)/f
        heading = heading*math.pi/180
        pitch = pitch*math.pi/180
        # extracted from the game code
        follow_height = 1.5
        world_x = (-math.sin(heading)*follow_height*fx
                    -math.sin(heading)*math.sin(pitch)*distance*fx
                    +math.cos(heading)*math.sin(pitch)*follow_height*fy
                    +math.cos(heading)*distance*fy
                    -math.cos(heading)*math.cos(pitch)*follow_height)/(math.cos(pitch)*fy+math.sin(pitch))
        world_z = (math.cos(heading)*follow_height*fx
                    +math.cos(heading)*math.sin(pitch)*distance*fx
                    +math.sin(heading)*math.sin(pitch)*follow_height*fy
                    +math.sin(heading)*distance*fy
                    -math.sin(heading)*math.cos(pitch)*follow_height)/(math.cos(pitch)*fy+math.sin(pitch))
        # in our world model, we'll use (x,z) as the two coordinates
        return Point2d(world_x, world_z)

    def local_to_global_position(self, local_position : Point2d, heading : float, pitch : float, distance : float, fov : float) -> Point2d:
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
        :return: position in the world's coordinate system, but with the origin in the point in the screen center
        :rtype: Point2d
        """
        pos = self.local_to_almost_global_position(local_position, heading, pitch, distance, fov)
        return self.origin_coordinates + pos

    def object_detected(self, image_obj : ImageObject) -> None:
        # anchor points are usually at the bottom (y) and middle (x)
        pos = self.local_to_global_position(
            Point2d.bottom_from_box(image_obj.box),
            CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
        obj_name = objects_info.get_item_info(info="name", image_id=image_obj.id)
        required_chunks = [self.point_to_chunk_index(pos)]
        adj_required_chunks = self.required_nearby_chunks(pos)
        required_chunks.extend(adj_required_chunks)
        objects_to_analyze = []
        for chunk_index in required_chunks:
            if chunk_index in self.objects_by_chunks:
                objects_to_analyze.extend(self.objects_by_chunks[chunk_index])
        
        # getting object from pair (obj, cycle_count)
        objects_to_analyze.extend([pair[0] for pair in self.recent_objects])

        best_match : ObjectModel = None
        lowest_distance : float = None
        for obj in objects_to_analyze:
            # if the object is close enough to an already detected object of the same type
            if pos.distance(obj.position) < DISTANCE_FOR_SAME_OBJECT and type(obj).__name__ == obj_name:
                if best_match is None or obj.position.distance(pos) < lowest_distance:
                    best_match = obj
                    lowest_distance = obj.position.distance(pos)
        
        if best_match is None:
            # in this case, I just identified something that's not in the WorldModel yet, so I create a new object
            # the second parameter (creation_time) is used as tiebreaker in case two updates are scheduled at the same time
            obj = factory.create_object(image_obj.id, pos, image_obj.box,
                                        lambda change, time_delta, instance:
                                        self.schedule_update(pos, time.time(), change, time_delta, instance))

            self.additions_to_recent_objects.append([obj, 1])
        else:
            best_match.latest_screen_position = image_obj.box
            # in this case, I identified an object that's already in my WorldModel or in the recent objects list
            if best_match in [pair[0] for pair in self.detected_this_cycle]:
                obj_index = [pair[0] for pair in self.detected_this_cycle].index(best_match)
                self.detected_this_cycle[obj_index][1] = True
                # if it's in the recent objects list, update its position
                if best_match in [pair[0] for pair in self.recent_objects]:
                    # maybe there's a better way, but for now just update its position
                    best_match.position = pos
            if isinstance(best_match, ObjectWithMultipleForms):
                best_match.handle_object_detected(image_obj.id)
            # this is the error from the position in modeling to the one being observed now 
            self.estimation_errors.append(pos - best_match.position)
            self.estimation_pairs.append((type(best_match).__name__, pos, best_match.position))
        # if obj_name in self.object_lists:
        #     self.object_lists[obj_name].append(obj)
        # else:
        #     self.object_lists[obj_name] = [obj]
        # if self.point_to_chunk_index(pos) in self.objects_by_chunks:
        #     self.objects_by_chunks[self.point_to_chunk_index(pos)].append(obj)
        # else:
        #     self.objects_by_chunks[self.point_to_chunk_index(pos)] = [obj]

    def mob_detected(self, image_obj : ImageObject):
        # this is just plain wrong, but for now I'll leave it commented for reference
        # pos = image_obj.position_from_player()
        # for mob in self.mob_list:
        #     if pos.distance(mob.position) < DISTANCE_FOR_SAME_MOB and image_obj.id == mob.id:
        #         mob.update(pos)
        #         mob.refresh_destruction_time()
        #         return
        # mob = factory.create_mob(image_obj.id, pos)
        # self.mob_list.add(mob)
        pass

    def finish_cycle(self) -> None:
        """Marks the end of a modeling cycle, this should be called in the end of update_model() on Modeling.
        It also removes objects that were not detected and should be.
        """
        self.cycles_since_player_detected += 1
        for pair in self.detected_this_cycle:
            obj = pair[0]
            detected = pair[1]
            # handling the case in which obj is a recent object
            if obj in [pair[0] for pair in self.recent_objects]:
                obj_index = [pair[0] for pair in self.recent_objects].index(obj)
                if detected:
                    new_count = self.recent_objects[obj_index][1]+1
                    obj_name = type(obj).__name__
                    # if the required number of cycles to admit an object is met, add it to both object_lists and objects_by_chunks
                    if new_count == CYCLES_TO_ADMIT_OBJECT:
                        if obj_name in self.object_lists:
                            self.object_lists[obj_name].append(obj)
                        else:
                            self.object_lists[obj_name] = [obj]
                        pos = obj.position
                        if self.point_to_chunk_index(pos) in self.objects_by_chunks:
                            self.objects_by_chunks[self.point_to_chunk_index(pos)].append(obj)
                        else:
                            self.objects_by_chunks[self.point_to_chunk_index(pos)] = [obj]
                        # also remove it
                        del self.recent_objects[obj_index]
                    else:
                        # update the cycle count for the object
                        self.recent_objects[obj_index][1] = new_count
                else:
                    # if the object wasn't detected, we remove it
                    del self.recent_objects[obj_index]
            # handling the case in which obj is a world model object (object removal if it wasn't detected for
            # many cycles in a row)
            else:
                if detected:
                    obj.cycles_to_be_deleted = CYCLES_FOR_OBJECT_REMOVAL
                else:
                    # we make it so that objects on the screen border aren't deleted if they aren't seen for a while
                    # since they often are offscreen or blocked by HUD
                    if is_inside_convex_polygon([self.c1_deletion_border, 
                                                    self.c2_deletion_border,
                                                    self.c3_deletion_border, 
                                                    self.c4_deletion_border], obj.position):
                        # we shouldn't count down an object for deletion if we're hovering over it
                        if obj != self.hovering_object:
                            obj.cycles_to_be_deleted -= 1
                            if obj.cycles_to_be_deleted == 0:
                                obj_name = type(obj).__name__
                                obj_list = self.object_lists[obj_name]
                                obj_index = obj_list.index(obj)
                                del obj_list[obj_index]
                                chunk_index = self.point_to_chunk_index(obj.position)
                                chunk_obj_list = self.objects_by_chunks[chunk_index]
                                obj_index_in_chunk_list = chunk_obj_list.index(obj)
                                del chunk_obj_list[obj_index_in_chunk_list]

        # adding new recent objects 
        self.recent_objects.extend(self.additions_to_recent_objects)

        avg_error_x1 = 0
        avg_error_x2 = 0
        if len(self.estimation_errors) > 0:
            for err in self.estimation_errors:
                avg_error_x1 += err.x1
                avg_error_x2 += err.x2
            avg_error_x1 /= len(self.estimation_errors)
            avg_error_x2 /= len(self.estimation_errors)
            self.avg_observed_error = Point2d(avg_error_x1, avg_error_x2)
        else:
            self.avg_observed_error = Point2d(0, 0)
        
        # mark current chunk as explored if applicable
        player_chunk = self.point_to_chunk_index(self.player.position)
        if self.decide_if_explored(self.player.position):
            self.explored_chunks.add(player_chunk)

    def get_closest_unexplored_chunk(self) -> tuple[int, int]:
        """Get closest unexplored chunk

        :return: chunk index of the closest unexplored chunk
        :rtype: tuple[int, int]
        """
        di = [-1, 0, 1, 0]
        dj = [0, 1, 0, -1]
        used_list = set()
        potential_list = queue.Queue()
        chunk_aux = self.point_to_chunk_index(self.player.position)
        while True:
            if chunk_aux not in self.explored_chunks:
                return chunk_aux
            for k in range(4):
                if (chunk_aux[0] + di[k], chunk_aux[1] + dj[k]) not in used_list:
                    potential_list.put((chunk_aux[0] + di[k], chunk_aux[1] + dj[k]))
            used_list.add(chunk_aux)
            chunk_aux = potential_list.get()


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
                            # if the object doesn't have the is_harvested method, we can choose it
                            op = getattr(obj_aux, "is_harvested", None)
                            if callable(op):
                                if not obj_aux.is_harvested():
                                    res_aux.append(obj_aux)
                            else:
                                res_aux.append(obj_aux)
                        result[obj] = res_aux
                    else:
                        raise ValueError("Filter not implemented")
            else:
                result[obj] = []
        return result
