from perception.classes import get_class_names

class YoloIdConverter:
    def __init__(self) -> None:
        self.yolo_names_to_image_id = {
            "wilson": 0, 
            "frog": 4,
            "hound": 5, 
            "spider": 8, 
            "spider_warrior": 9,
            "tallbird": 10,
            "merm": 14,
            "grass": 21, 
            "grass_picked": 22, 
            "sapling": 23, 
            "sapling_picked": 24, 
            "seeds": 25,
            "flint": 26, 
            "monster_meat": 27,
            "tree_evergreen_1": 31,
            "tree_evergreen_2": 32,
            "tree_evergreen_3": 33,
            "spider_nest1": 34,
            "berry_bush": 35, 
            "berry_bush_harvested": 36, 
            "honey": 37,
            "frog_legs": 39,
            "rock1": 42,
            "meat": 43,
            "carrot_planted": 44,
            "clock_rook": 48,
            "clock_knight": 49,
            "clock_bishop": 50,
            "rocks": 56,
            "tree_evergreen_4": 57,
            "morsel": 69,
            "fish": 70,
            "rock2": 71,
            "log": 72,
            "gold_nugget": 73,
            "spider_nest2": 74,
            "spider_nest3": 75,
            "drumstick": 103,
            "gobbler": 104,
            "pig_head": 96,
            "pig_skin": 29,
        }
        # can be used to convert yolo_id to image_id
        self.important_classes = [self.yolo_names_to_image_id[n] for n in get_class_names()]
        
        # can be used to convert image_id to yolo_id
        self.reverse_important_classes = {}
        for i, class_id in enumerate(self.important_classes):
            self.reverse_important_classes[class_id] = i

    def yolo_to_actual_id(self, yolo_id : int) -> int:
        """Converts the YOLO id to the id used in perception (image_id)

        :param yolo_id: YOLO id
        :type yolo_id: int
        :return: image_id
        :rtype: int
        """
        return self.important_classes[yolo_id]

    def actual_to_yolo_id(self, actual_id : int) -> int:
        """Converts the id used in perception (image_id) to the YOLO id

        :param actual_id: image_id
        :type actual_id: int
        :return: YOLO id
        :rtype: int
        """
        return self.reverse_important_classes[actual_id]

yolo_id_converter = YoloIdConverter()