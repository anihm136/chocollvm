from typing import List, Optional

from ..varinstance import VarInstance
from .identifier import Identifier
from .node import Node
from .typeannotation import TypeAnnotation


class TypedVar(Node):
    def __init__(
        self, location: List[int], identifier: Identifier, typ: TypeAnnotation
    ):
        super().__init__(location, "TypedVar")
        self.identifier = identifier
        self.type = typ
        self.t = None  # the typechecked type goes here
        self.varInstance: Optional[VarInstance] = None

    def visit(self, visitor):
        return visitor.TypedVar(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["identifier"] = self.identifier.toJSON(dump_location)
        d["type"] = self.type.toJSON(dump_location)
        return d
