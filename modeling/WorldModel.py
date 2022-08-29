import heapq
import math

from modeling.PlayerModel import PlayerModel
from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from modeling.Factory import factory
from modeling.constants import DISTANCE_FOR_SAME_OBJECT, DISTANCE_FOR_SAME_MOB
from modeling.ObjectsInfo import objects_info
from perception.screen import SCREEN_SIZE
from modeling.constants import FOV, CAMERA_DISTANCE, CAMERA_PITCH, CAMERA_HEADING
from utility.Clock import Clock
from utility.Point2d import Point2d


class WorldModel:
    def __init__(self, player : PlayerModel, clock : Clock):
        """Generates the world model. It should be noted that the full workflow for a cycle of updating is:
            - if player was detected (on perception), call player_detected()
            - call update_origin_position()
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
        self.object_lists = {}
        self.mob_list = set()
        # update_queue has (time, object_id, index, change)
        self.update_queue = []
        self.player : PlayerModel = player
        self.latest_detected_player_position : Point2d = None
        self.cycles_since_player_detected : int = 0
        self.origin_coordinates : Point2d = player.position
        self.clock : Clock = clock

    def update(self):
        # [3] gets the 'timestamp' in which the change should happen
        while len(self.update_queue) > 0 and heapq.nsmallest(1, self.update_queue)[0][3] < self.clock.time():
            tup = heapq.heappop(self.update_queue)
            id_ = tup[0]
            ind = tup[1]
            change = tup[2]
            instance = tup[4]
            if change == "disappear":
                self.object_lists[id_].pop(ind)
            else:
                instance.update(change)

        self.mob_list = set(filter(lambda mob: mob.update_destruction_time(self.clock.dt()), self.mob_list))

    def update_local(self, object_list):
        self.local_objects = object_list

    # time_delta should be GameTime
    def schedule_update(self, id_, ind, change, time_delta, instance):
        heapq.heappush(self.update_queue, (id_, ind, change, self.clock.time_from_now(time_delta), instance))

    def player_detected(self, image_obj_pos : Point2d):
        self.latest_detected_player_position = image_obj_pos
        self.cycles_since_player_detected = 0

    def update_origin_position(self):
        # if it's been more than 10 cycles since the last time the player was detected, use the center of the screen
        if self.cycles_since_player_detected > 10:
            player_screen_position = Point2d(SCREEN_SIZE["height"]/2, SCREEN_SIZE["width"]/2)
        else:
            player_screen_position = self.latest_detected_player_position
        # pos in (x, z) in world coords
        pos = self.local_to_almost_global_position(player_screen_position, CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
        self.origin_coordinates = self.player.position - pos

    # positions are Point2d
    def local_to_almost_global_position(self, local_position : Point2d, heading : float, pitch : float, distance : float, fov : float) -> Point2d:
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
        fx = (local_position.x2 - SCREEN_SIZE["height"]/2)/f
        fy = (local_position.x1 - SCREEN_SIZE["width"]/2)/f
        heading = heading*math.pi/180
        pitch = pitch*math.pi/180
        world_x = ((math.cos(heading)*fx
                +math.sin(pitch)*math.sin(heading)*fy
                +math.sin(pitch)*math.cos(heading)*fx*1.5/distance
                +math.sin(heading)*fy*1.5/distance
                -math.cos(pitch)*math.cos(heading)*1.5/distance)/(math.sin(pitch)+math.cos(pitch)*fx))*distance
        world_z = ((math.sin(heading)*fx
                -math.sin(pitch)*math.cos(heading)*fy
                +math.sin(pitch)*math.sin(heading)*fx*1.5/distance
                -math.cos(heading)*fy*1.5/distance
                -math.cos(pitch)*math.sin(heading)*1.5/distance)/(math.sin(pitch)+math.cos(pitch)*fx))*distance
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

    def object_detected(self, image_obj):
        # anchor points are usually at the bottom (y) and middle (x)
        pos = self.local_to_global_position(
            Point2d(image_obj.box[0] + image_obj.box[2]//2, image_obj.box[1] + image_obj.box[3]),
            CAMERA_HEADING, CAMERA_PITCH, CAMERA_DISTANCE, FOV)
        obj_id = objects_info.get_item_info(info="obj_id", image_id=image_obj.id)
        if obj_id in self.object_lists:
            for obj in self.object_lists[obj_id]:
                # if the object is close enough to an already detected object of the same type, ignore it
                if pos.distance(obj.position) < DISTANCE_FOR_SAME_OBJECT:
                    if isinstance(obj, ObjectWithMultipleForms):
                        obj.handle_object_detected(image_obj.id)
                    else:
                        return
                    return
        # if the object isn't close to other previously detected objects, it should be added to the model
        if obj_id in self.object_lists:
            list_size = len(self.object_lists[obj_id])
        else:
            list_size = 0
        obj = factory.create_object(image_obj.id, pos,
                                    lambda change, time_delta, instance:
                                    self.schedule_update(objects_info.get_item_info(
                                        info="obj_id", image_id=image_obj.id),
                                        list_size, change, time_delta, instance))

        if obj_id in self.object_lists:
            self.object_lists[obj_id].append(obj)
        else:
            self.object_lists[obj_id] = [obj]

    def mob_detected(self, image_obj):
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
        """Marks the end of a modeling cycle, this should be called in the end of update_model() on Modeling
        """
        self.cycles_since_player_detected += 1

    # returns dict of objects
    def get_all_of(self, obj_list: list[str]) -> dict:
        result = {}
        for obj in obj_list:
            obj_id = objects_info.get_item_info(info="obj_id", name=obj)
            if obj_id in self.object_lists.keys():
                result[obj] = self.object_lists[obj_id]
            else:
                result[obj] = []
        return result
