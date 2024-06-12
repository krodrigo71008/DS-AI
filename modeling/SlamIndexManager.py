from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modeling.objects.ObjectModel import ObjectModel

class SlamIndexManager:
    def __init__(self) -> None:
        self.index_mapping = {}

    def register(self, object : ObjectModel, index : int):
        self.index_mapping[object] = index

    def get_index(self, object : ObjectModel):
        return self.index_mapping[object]

    def remove_object(self, object : ObjectModel):
        obj_index = self.index_mapping[object]
        del self.index_mapping[object]
        for obj, idx in self.index_mapping.items():
            if idx > obj_index:
                self.index_mapping[obj] = idx-2
