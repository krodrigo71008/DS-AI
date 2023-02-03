class ImageObject:
    def __init__(self, class_id : int, score : float, box : tuple[int, int, int, int]):
        self.id = class_id
        self.score = score
        self.box = box
