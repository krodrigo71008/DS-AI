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
from modeling.objects.Rock import Rock
from modeling.mobs.MobModel import MobModel
from modeling.ObjectsInfo import objects_info


class Factory:
    def __init__(self):
        pass

    # receives image id and returns an object
    @staticmethod
    def create_object(id_, pos, update_function=None):
        obj_id = objects_info.get_item_info(info="obj_id", image_id=id_)
        if obj_id == 1:
            return TallbirdNest(pos)
        if obj_id == 2:
            return TallbirdEgg(pos)
        if obj_id == 3:
            return Flower(pos)
        if obj_id == 4:
            return Grass(pos, id_, update_function)
        if obj_id == 5:
            return Sapling(pos, id_, update_function)
        if obj_id == 6:
            return PickableObjectModel(pos, id_, "Seeds")
        if obj_id == 7:
            return PickableObjectModel(pos, id_, "Flint")
        if obj_id == 8:
            return PickableObjectModel(pos, id_, "MonsterMeat")
        if obj_id == 9:
            return PickableObjectModel(pos, id_, "HoundTooth")
        if obj_id == 10:
            return PickableObjectModel(pos, id_, "PigSkin")
        if obj_id == 11:
            return Ashes(pos, update_function)
        if obj_id == 12:
            return TreeEvergreen(pos, id_, update_function)
        if obj_id == 13:
            return SpiderNest(pos, id_, update_function)
        if obj_id == 14:
            return BerryBush(pos, id_, update_function)
        if obj_id == 15:
            return PickableObjectModel(pos, id_, "Honey")
        if obj_id == 16:
            return PickableObjectModel(pos, id_, "Stinger")
        if obj_id == 17:
            return PickableObjectModel(pos, id_, "FrogLegs")
        if obj_id == 18:
            return PickableObjectModel(pos, id_, "Blueprint")
        if obj_id == 19:
            return PickableObjectModel(pos, id_, "Silk")
        if obj_id == 20:
            return Rock(pos)
        if obj_id == 21:
            return PickableObjectModel(pos, id_, "Meat")
        if obj_id == 22:
            return PickableObjectModel(pos, id_, "Carrot")
        if obj_id == 23:
            return Campfire(pos, id_, update_function)
        if obj_id == 24:
            return PickableObjectModel(pos, id_, "SpiderGland")
        if obj_id == 25:
            return PickableObjectModel(pos, id_, "Rocks")
        if obj_id == 26:
            return PickableObjectModel(pos, id_, "Axe")
        if obj_id == 27:
            return PickableObjectModel(pos, id_, "Pickaxe")
        if obj_id == 28:
            return PickableObjectModel(pos, id_, "Shovel")
        if obj_id == 29:
            return PickableObjectModel(pos, id_, "Hammer")
        if obj_id == 30:
            return PickableObjectModel(pos, id_, "Razor")
        if obj_id == 31:
            return PickableObjectModel(pos, id_, "Torch")
        if obj_id == 32:
            return PickableObjectModel(pos, id_, "CutGrass")
        if obj_id == 33:
            return PickableObjectModel(pos, id_, "Twigs")
        if obj_id == 34:
            return PickableObjectModel(pos, id_, "Rot")
        if obj_id == 35:
            return PickableObjectModel(pos, id_, "RottenEgg")

    @staticmethod
    def create_mob(id_, pos):
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
            return MobModel(pos, id_, "TentacleGround")
        if id_ == 49:
            return MobModel(pos, id_, "Tentacle")
        if id_ == 50:
            return MobModel(pos, id_, "ClockRook")
        if id_ == 51:
            return MobModel(pos, id_, "ClockKnight")
        if id_ == 52:
            return MobModel(pos, id_, "ClockBishop")
        if id_ == 53:
            return MobModel(pos, id_, "CrawlingHorror")
        if id_ == 54:
            return MobModel(pos, id_, "Terrorbeak")
        if id_ == 55:
            return MobModel(pos, id_, "Werepig")
        if id_ == 56:
            return MobModel(pos, id_, "Mosquito")
        if id_ == 57:
            return MobModel(pos, id_, "BirdBlue")


factory = Factory()
