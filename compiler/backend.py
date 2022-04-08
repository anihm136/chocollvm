from .astnodes import (
    AssignStmt,
    BinaryExpr,
    BooleanLiteral,
    CallExpr,
    ClassType,
    ExprStmt,
    FuncDef,
    Identifier,
    IfExpr,
    IfStmt,
    IntegerLiteral,
    Node,
    NoneLiteral,
    Program,
    ReturnStmt,
    StringLiteral,
    TypedVar,
    UnaryExpr,
    VarDef,
    WhileStmt,
)
from .visitor import Visitor


class Backend(Visitor):
    def __init__(self):
        pass

    def visit(self, node: Node):
        return node.visit(self)

    # TOP LEVEL & DECLARATIONS
    def Program(self, _: Program) -> None:
        raise NotImplementedError()

    def VarDef(self, _: VarDef) -> None:
        raise NotImplementedError()

    def FuncDef(self, _: FuncDef) -> None:
        raise NotImplementedError()

    # STATEMENTS
    def AssignStmt(self, _: AssignStmt) -> None:
        raise NotImplementedError()

    def IfStmt(self, _: IfStmt) -> None:
        raise NotImplementedError()

    def ExprStmt(self, _: ExprStmt) -> None:
        raise NotImplementedError()

    def BinaryExpr(self, _: BinaryExpr) -> None:
        raise NotImplementedError()

    def UnaryExpr(self, _: UnaryExpr) -> None:
        raise NotImplementedError()

    def CallExpr(self, _: CallExpr) -> None:
        raise NotImplementedError()

    def WhileStmt(self, _: WhileStmt) -> None:
        raise NotImplementedError()

    def ReturnStmt(self, _: ReturnStmt) -> None:
        raise NotImplementedError()

    def Identifier(self, _: Identifier) -> None:
        raise NotImplementedError()

    def IfExpr(self, _: IfExpr) -> None:
        raise NotImplementedError()

    # LITERALS
    def BooleanLiteral(self, _: BooleanLiteral) -> None:
        raise NotImplementedError()

    def IntegerLiteral(self, _: IntegerLiteral) -> None:
        raise NotImplementedError()

    def NoneLiteral(self, _: NoneLiteral) -> None:
        raise NotImplementedError()

    def StringLiteral(self, _: StringLiteral) -> None:
        raise NotImplementedError()

    # TYPES
    def TypedVar(self, _: TypedVar) -> None:
        raise NotImplementedError()

    def ClassType(self, _: ClassType) -> None:
        raise NotImplementedError()
