from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modeling.objects.ObjectModel import ObjectModel

class SlamIndexManager:
    def __init__(self) -> None:
        self.index_mapping = {}

    def register(self, object_ : ObjectModel, index : int):
        self.index_mapping[object_] = index

    def get_index(self, object_ : ObjectModel):
        return self.index_mapping[object_]

    def remove_object(self, object_ : ObjectModel):
        obj_index = self.index_mapping[object_]
        del self.index_mapping[object_]
        for obj, idx in self.index_mapping.items():
            if idx > obj_index:
                self.index_mapping[obj] = idx-2
