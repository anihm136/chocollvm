from typing import List, Optional

from ..types.valuetype import ValueType
from .node import Node


class Expr(Node):
    def __init__(self, location: List[int], kind: str):
        super().__init__(location, kind)
        self.inferredType: Optional[ValueType] = None
        self.shouldBoxAsRef = False

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        if self.inferredType is not None:
            d["inferredType"] = self.inferredType.toJSON(dump_location)
        return d
