class TerrainTile:
    def __init__(self, type_ : int = None) -> None:
        self.type = type_
        self.detections = []
        if type_ is not None:
            self.detections.append(type_)
        self.MAX_QUEUE_SIZE = 10

    def add_detection(self, type_ : int):
        if len(self.detections) == self.MAX_QUEUE_SIZE:
            self.detections.pop(0)
        self.detections.append(type_)
        self.type = max(set(self.detections), key = self.detections.count)
