from __future__ import annotations
from typing import TYPE_CHECKING

from modeling.objects.ObjectWithSingleForm import ObjectWithSingleForm
if TYPE_CHECKING:
    from utility.Point2d import Point2d


class StructureModel(ObjectWithSingleForm):
    def __init__(self, position : Point2d, latest_screen_position : Point2d, id_ : int, name : str):
        super().__init__(False, position, latest_screen_position)
        self.id = id_
        self.name = name

    def update(self, change : str):
        pass

    def name_str(self) -> str:
        return self.name
