from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.TallbirdNest import TallbirdNest
from modeling.objects.Grass import Grass
from modeling.objects.Reeds import Reeds
from modeling.objects.Sapling import Sapling
from modeling.objects.Ashes import Ashes
from modeling.objects.Evergreen import Evergreen
from modeling.objects.SpiderNest import SpiderNest
from modeling.objects.PickableObjectModel import PickableObjectModel
from modeling.objects.StructureModel import StructureModel
from modeling.objects.BerryBush import BerryBush
from modeling.objects.Campfire import Campfire
from modeling.objects.MarshBush import MarshBush
from modeling.mobs.MobModel import MobModel
from modeling.objects.ObjectModel import ObjectModel
from modeling.ObjectsInfo import objects_info
from utility.Point2d import Point2d
if TYPE_CHECKING:
    from modeling.Scheduler import Scheduler


class Factory:
    def __init__(self):
        self.pickable_object_ids = [2, 6, [7,10], [15,19], 21, 22, [24,38], [40,42], 44, 46, [49,54], 57, 58, 60, [65,146]]
        self.structure_ids = [3, 20, 39, 43, 45, 47, 56, 59, [62,64]]
        aux = []
        for elem in self.pickable_object_ids:
            if type(elem) == list:
                for a in range(elem[0], elem[1]+1):
                    aux.append(a)
            else:
                aux.append(elem)
        self.pickable_object_ids = aux
        aux = []
        for elem in self.structure_ids:
            if type(elem) == list:
                for a in range(elem[0], elem[1]+1):
                    aux.append(a)
            else:
                aux.append(elem)
        self.structure_ids = aux

    # receives image id and returns an object
    def create_object(self, image_id : int, pos : Point2d, latest_screen_position : Point2d, scheduler : Scheduler=None) -> ObjectModel:
        """Create object described by image_id

        :param image_id: image_id from Perception
        :type image_id: int
        :param pos: position in the world
        :type pos: Point2d
        :param latest_screen_position: latest screen position of the object
        :type latest_screen_position: Point2d
        :param scheduler: update scheduler to pass to some objects, defaults to None
        :type scheduler: Scheduler
        :return: requested object
        :rtype: ObjectModel
        """
        obj_id = objects_info.get_item_info(info="obj_id", image_id=image_id)
        name = objects_info.get_item_info(info="name", image_id=image_id)
        if obj_id in self.pickable_object_ids:
            return PickableObjectModel(pos, latest_screen_position, obj_id, name)
        if obj_id in self.structure_ids:
            return StructureModel(pos, latest_screen_position, obj_id, name)
        if obj_id == 1:
            return TallbirdNest(pos, latest_screen_position)
        if obj_id == 4:
            return Grass(pos, latest_screen_position, image_id, scheduler)
        if obj_id == 5:
            return Sapling(pos, latest_screen_position, image_id, scheduler)
        if obj_id == 11:
            return Ashes(pos, latest_screen_position, scheduler)
        if obj_id == 12:
            return Evergreen(pos, latest_screen_position, image_id, scheduler, lumpy=False)
        if obj_id == 13:
            return SpiderNest(pos, latest_screen_position, image_id, scheduler)
        if obj_id == 14:
            return BerryBush(pos, latest_screen_position, image_id, scheduler)
        if obj_id == 23:
            return Campfire(pos, latest_screen_position, image_id, scheduler)
        if obj_id == 48:
            return Evergreen(pos, latest_screen_position, image_id, scheduler, lumpy=True)
        if obj_id == 55:
            return MarshBush(pos, latest_screen_position, image_id, scheduler)
        if obj_id == 61:
            return Reeds(pos, latest_screen_position, image_id, scheduler)

    @staticmethod
    def create_mob(id_ : int, pos : Point2d, latest_screen_position : Point2d) -> MobModel:
        """Create mob described by id_

        :param id_: image_id
        :type id_: int
        :param pos: position in the world
        :type pos: Point2d
        :return: requested mob
        :rtype: MobModel
        """
        if id_ == 1:
            return MobModel(pos, id_, "Treeguard", latest_screen_position)
        if id_ == 2:
            return MobModel(pos, id_, "Bee", latest_screen_position)
        if id_ == 3:
            return MobModel(pos, id_, "KillerBee", latest_screen_position)
        if id_ == 4:
            return MobModel(pos, id_, "Frog", latest_screen_position)
        if id_ == 5:
            return MobModel(pos, id_, "Hound", latest_screen_position)
        if id_ == 6:
            return MobModel(pos, id_, "IceHound", latest_screen_position)
        if id_ == 7:
            return MobModel(pos, id_, "FireHound", latest_screen_position)
        if id_ == 8:
            return MobModel(pos, id_, "Spider", latest_screen_position)
        if id_ == 9:
            return MobModel(pos, id_, "SpiderWarrior", latest_screen_position)
        if id_ == 10:
            return MobModel(pos, id_, "Tallbird", latest_screen_position)
        if id_ == 11:
            return MobModel(pos, id_, "Ghost", latest_screen_position)
        if id_ == 12:
            return MobModel(pos, id_, "GuardianPig", latest_screen_position)
        if id_ == 13:
            return MobModel(pos, id_, "Butterfly", latest_screen_position)
        if id_ == 14:
            return MobModel(pos, id_, "Merm", latest_screen_position)
        if id_ == 15:
            return MobModel(pos, id_, "BirdRed", latest_screen_position)
        if id_ == 16:
            return MobModel(pos, id_, "BirdBlack", latest_screen_position)
        if id_ == 17:
            return MobModel(pos, id_, "Rabbit", latest_screen_position)
        if id_ == 47:
            return MobModel(pos, id_, "Tentacle", latest_screen_position)
        if id_ == 48:
            return MobModel(pos, id_, "ClockRook", latest_screen_position)
        if id_ == 49:
            return MobModel(pos, id_, "ClockKnight", latest_screen_position)
        if id_ == 50:
            return MobModel(pos, id_, "ClockBishop", latest_screen_position)
        if id_ == 51:
            return MobModel(pos, id_, "CrawlingHorror", latest_screen_position)
        if id_ == 52:
            return MobModel(pos, id_, "Terrorbeak", latest_screen_position)
        if id_ == 53:
            return MobModel(pos, id_, "Werepig", latest_screen_position)
        if id_ == 54:
            return MobModel(pos, id_, "Mosquito", latest_screen_position)
        if id_ == 55:
            return MobModel(pos, id_, "BirdBlue", latest_screen_position)
        if id_ == 76:
            return MobModel(pos, id_, "Beefalo", latest_screen_position)
        if id_ == 104:
            return MobModel(pos, id_, "Gobbler", latest_screen_position)


factory = Factory()
