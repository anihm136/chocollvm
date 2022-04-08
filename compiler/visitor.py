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


class Visitor:
    def visit(self, node: Node):
        return node.visit(self)

    # TOP LEVEL & DECLARATIONS

    def Program(self, _: Program):
        pass

    def VarDef(self, _: VarDef):
        pass

    def FuncDef(self, _: FuncDef):
        pass

    # STATEMENTS

    def AssignStmt(self, _: AssignStmt):
        pass

    def IfStmt(self, _: IfStmt):
        pass

    def ExprStmt(self, _: ExprStmt):
        pass

    def BinaryExpr(self, _: BinaryExpr):
        pass

    def UnaryExpr(self, _: UnaryExpr):
        pass

    def CallExpr(self, _: CallExpr):
        pass

    def WhileStmt(self, _: WhileStmt):
        pass

    def ReturnStmt(self, _: ReturnStmt):
        pass

    def Identifier(self, _: Identifier):
        pass

    def IfExpr(self, _: IfExpr):
        pass

    # LITERALS

    def BooleanLiteral(self, _: BooleanLiteral):
        pass

    def IntegerLiteral(self, _: IntegerLiteral):
        pass

    def NoneLiteral(self, _: NoneLiteral):
        pass

    def StringLiteral(self, _: StringLiteral):
        pass

    # TYPES

    def TypedVar(self, _: TypedVar):
        pass

    def ClassType(self, _: ClassType):
        pass
