from typing import List

from .expr import Expr
from .stmt import Stmt


class ReturnStmt(Stmt):
    def __init__(self, location: List[int], value: Expr):
        super().__init__(location, "ReturnStmt")
        self.value = value
        self.isReturn = True
        self.expType = None

    def postorder(self, visitor):
        if self.value is not None:
            visitor.visit(self.value)
        return visitor.ReturnStmt(self)

    def preorder(self, visitor):
        visitor.ReturnStmt(self)
        if self.value is not None:
            visitor.visit(self.value)
        return self

    def visit(self, visitor):
        return visitor.ReturnStmt(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        if self.value is not None:
            d["value"] = self.value.toJSON(dump_location)
        else:
            d["value"] = None
        return d
