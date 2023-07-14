import pandas as pd

class YoloIdConverter:
    def __init__(self) -> None:
        self.important_classes_names = ["Wilson", "Hound", "Spider", "Grass", "Sapling", "Flint", "BerryBush", "Carrot"]
        self.obj_info = pd.read_csv('utility/objects_info.csv')
        # can be used to convert image_id to yolo_id
        self.important_classes = self.obj_info[self.obj_info["name"].isin(self.important_classes_names)]["image_id"].values
        # can be used to convert yolo_id to image_id
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