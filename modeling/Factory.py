from modeling.objects.TallbirdNest import TallbirdNest
from modeling.objects.TallbirdEgg import TallbirdEgg
from modeling.objects.Flower import Flower
from modeling.objects.Grass import Grass
from modeling.objects.Sapling import Sapling
from modeling.objects.Ashes import Ashes
from modeling.objects.TreeEvergreen import TreeEvergreen
from modeling.objects.SpiderNest import SpiderNest
from modeling.objects.PickableObjectModel import PickableObjectModel
from modeling.objects.BerryBush import BerryBush
from modeling.objects.Campfire import Campfire
from modeling.objects.NitreRock import NitreRock
from modeling.mobs.MobModel import MobModel
from modeling.objects.ObjectModel import ObjectModel
from modeling.ObjectsInfo import objects_info
from utility.Point2d import Point2d
from utility.Clock import Clock


class Factory:
    def __init__(self):
        pass

    # receives image id and returns an object
    @staticmethod
    def create_object(image_id : int, pos : Point2d, latest_screen_position : Point2d, update_queue : list[float, int, int, str]=None, clock : Clock=None) -> ObjectModel:
        """Create object described by image_id

        :param image_id: image_id from Perception
        :type image_id: int
        :param pos: position in the world
        :type pos: Point2d
        :param latest_screen_position: latest screen position of the object
        :type latest_screen_position: Point2d
        :param update_queue: priority queue with (time, object_id, index, change), defaults to None
        :type update_queue: list[float, int, int, str], optional
        :param clock: WorldModel's clock, defaults to None
        :type clock: Clock, optional
        :return: requested object
        :rtype: ObjectModel
        """
        obj_id = objects_info.get_item_info(info="obj_id", image_id=image_id)
        if obj_id == 1:
            return TallbirdNest(pos, latest_screen_position)
        if obj_id == 2:
            return TallbirdEgg(pos, latest_screen_position)
        if obj_id == 3:
            return Flower(pos, latest_screen_position)
        if obj_id == 4:
            return Grass(pos, latest_screen_position, image_id, update_queue, clock)
        if obj_id == 5:
            return Sapling(pos, latest_screen_position, image_id, update_queue, clock)
        if obj_id == 6:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Seeds")
        if obj_id == 7:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Flint")
        if obj_id == 8:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "MonsterMeat")
        if obj_id == 9:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "HoundTooth")
        if obj_id == 10:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "PigSkin")
        if obj_id == 11:
            return Ashes(pos, latest_screen_position, update_queue, clock)
        if obj_id == 12:
            return TreeEvergreen(pos, latest_screen_position, image_id, update_queue, clock)
        if obj_id == 13:
            return SpiderNest(pos, latest_screen_position, image_id, update_queue, clock)
        if obj_id == 14:
            return BerryBush(pos, latest_screen_position, image_id, update_queue, clock)
        if obj_id == 15:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Honey")
        if obj_id == 16:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Stinger")
        if obj_id == 17:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "FrogLegs")
        if obj_id == 18:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Blueprint")
        if obj_id == 19:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Silk")
        if obj_id == 20:
            return NitreRock(pos, latest_screen_position)
        if obj_id == 21:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Meat")
        if obj_id == 22:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Carrot")
        if obj_id == 23:
            return Campfire(pos, latest_screen_position, image_id, update_queue, clock)
        if obj_id == 24:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "SpiderGland")
        if obj_id == 25:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Rocks")
        if obj_id == 26:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Axe")
        if obj_id == 27:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Pickaxe")
        if obj_id == 28:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Shovel")
        if obj_id == 29:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Hammer")
        if obj_id == 30:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Razor")
        if obj_id == 31:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Torch")
        if obj_id == 32:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "CutGrass")
        if obj_id == 33:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Twigs")
        if obj_id == 34:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Rot")
        if obj_id == 35:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "RottenEgg")
        if obj_id == 36:
            return PickableObjectModel(pos, latest_screen_position, obj_id, "Berries")

    @staticmethod
    def create_mob(id_ : int, pos : Point2d) -> MobModel:
        """Create mob described by id_

        :param id_: image_id
        :type id_: int
        :param pos: position in the world
        :type pos: Point2d
        :return: requested mob
        :rtype: MobModel
        """
        if id_ == 2:
            return MobModel(pos, id_, "Treeguard")
        if id_ == 3:
            return MobModel(pos, id_, "Bee")
        if id_ == 4:
            return MobModel(pos, id_, "KillerBee")
        if id_ == 5:
            return MobModel(pos, id_, "Frog")
        if id_ == 6:
            return MobModel(pos, id_, "Hound")
        if id_ == 7:
            return MobModel(pos, id_, "IceHound")
        if id_ == 8:
            return MobModel(pos, id_, "FireHound")
        if id_ == 9:
            return MobModel(pos, id_, "Spider")
        if id_ == 10:
            return MobModel(pos, id_, "SpiderWarrior")
        if id_ == 11:
            return MobModel(pos, id_, "Tallbird")
        if id_ == 12:
            return MobModel(pos, id_, "Ghost")
        if id_ == 13:
            return MobModel(pos, id_, "GuardianPig")
        if id_ == 14:
            return MobModel(pos, id_, "Butterfly")
        if id_ == 15:
            return MobModel(pos, id_, "Merm")
        if id_ == 16:
            return MobModel(pos, id_, "BirdRed")
        if id_ == 17:
            return MobModel(pos, id_, "BirdBlack")
        if id_ == 18:
            return MobModel(pos, id_, "Rabbit")
        if id_ == 48:
            return MobModel(pos, id_, "Tentacle")
        if id_ == 49:
            return MobModel(pos, id_, "ClockRook")
        if id_ == 50:
            return MobModel(pos, id_, "ClockKnight")
        if id_ == 51:
            return MobModel(pos, id_, "ClockBishop")
        if id_ == 52:
            return MobModel(pos, id_, "CrawlingHorror")
        if id_ == 53:
            return MobModel(pos, id_, "Terrorbeak")
        if id_ == 54:
            return MobModel(pos, id_, "Werepig")
        if id_ == 55:
            return MobModel(pos, id_, "Mosquito")
        if id_ == 56:
            return MobModel(pos, id_, "BirdBlue")


factory = Factory()
