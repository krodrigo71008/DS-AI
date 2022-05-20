import heapq
from typing import List
from modeling.objects.ObjectWithMultipleForms import ObjectWithMultipleForms
from modeling.Factory import factory
from modeling.constants import DISTANCE_FOR_SAME_OBJECT, DISTANCE_FOR_SAME_MOB
from modeling.ObjectsInfo import objects_info


class WorldModel:
    def __init__(self, player, clock):
        # map of object lists, the first index represents an object id and
        # object_list[id] has the objects with that id
        self.object_lists = {}
        self.mob_list = set()
        # update_queue has (time, object_id, index, change)
        self.update_queue = []
        self.player = player
        self.clock = clock

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

    # time_delta should be GameTime
    def schedule_update(self, id_, ind, change, time_delta, instance):
        heapq.heappush(self.update_queue, (id_, ind, change, self.clock.time_from_now(time_delta), instance))

    # positions are Point2d
    def local_to_global_position(self, local_position):
        return self.player.position + local_position

    def object_detected(self, image_obj):
        pos = self.local_to_global_position(image_obj.position_from_player())
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
        # for now I'll just track mobs on screen, later I should track the last position when
        # the mob goes off screen and maybe keep tracking if it appears close to that position
        pos = image_obj.position_from_player()
        for mob in self.mob_list:
            if pos.distance(mob.position) < DISTANCE_FOR_SAME_MOB and image_obj.id == mob.id:
                mob.update(pos)
                mob.refresh_destruction_time()
                return
        mob = factory.create_mob(image_obj.id, pos)
        self.mob_list.add(mob)

    # returns dict of objects
    def get_all_of(self, obj_list: List[str]) -> dict:
        result = {}
        for obj in obj_list:
            obj_id = objects_info.get_item_info(info="obj_id", name=obj)
            if obj_id in self.object_lists.keys():
                result[obj] = self.object_lists[obj_id]
            else:
                result[obj] = []
        return result
