from typing import List, Optional

from ..varinstance import VarInstance
from .expr import Expr


class Identifier(Expr):
    def __init__(self, location: List[int], name: str):
        super().__init__(location, "Identifier")
        self.name = name
        self.varInstance: Optional[VarInstance] = None

    def visit(self, visitor):
        return visitor.Identifier(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["name"] = self.name
        return d

    def copy(self):
        cpy = Identifier(self.location, self.name)
        cpy.inferredType = self.inferredType
        cpy.varInstance = self.varInstance
        return cpy
