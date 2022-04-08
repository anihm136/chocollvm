import json

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
from .backend import Backend


class Builder:
    def __init__(self, name: str):
        self.name = name
        self.lines = []
        self.indentation = 0

    def newLine(self, line=""):
        self.lines.append((self.indentation * "    ") + line)
        return self

    def addText(self, text=""):
        if len(self.lines) == 0:
            self.newLine()
        self.lines[-1] = self.lines[-1] + text
        return self

    def indent(self):
        self.indentation += 1
        return self

    def unindent(self):
        self.indentation -= 1
        return self

    def emit(self) -> str:
        return "\n".join(self.lines)


class PythonBackend(Backend):
    def __init__(self):
        self.builder = Builder("PythonBuilder")

    def visit(self, node: Node):
        return node.visit(self)

    # TOP LEVEL & DECLARATIONS

    def Program(self, node: Program):
        for d in node.declarations:
            self.visit(d)
        for s in node.statements:
            self.visit(s)

    def VarDef(self, node: VarDef):
        self.builder.newLine()
        self.visit(node.var)
        self.builder.addText(" = ")
        self.visit(node.value)

    def FuncDef(self, node: FuncDef):
        self.builder.newLine("def ")
        self.visit(node.name)
        self.builder.addText("(")
        for i in range(len(node.params)):
            self.visit(node.params[i])
            if i != len(node.params) - 1:
                self.builder.addText(", ")
        self.builder.addText("):")
        self.builder.indent()
        for d in node.declarations:
            self.visit(d)
        for s in node.statements:
            self.visit(s)
        if len(node.declarations) == 0 and len(node.statements) == 0:
            self.builder.addText("pass")
        self.builder.unindent()
        self.builder.newLine()

    # STATEMENTS

    def AssignStmt(self, node: AssignStmt):
        if len(node.targets) == 1:
            self.builder.newLine()
            self.visit(node.targets[0])
            self.builder.addText(" = ")
            self.visit(node.value)
        else:
            self.builder.newLine("__x = ")
            self.visit(node.value)
            for t in node.targets:
                self.builder.newLine()
                self.visit(t)
                self.builder.addText(" = __x")

    def IfStmt(self, node: IfStmt):
        self.builder.newLine("if ")
        self.visit(node.condition)
        self.builder.addText(":")
        self.builder.indent()
        for s in node.thenBody:
            self.visit(s)
        if len(node.thenBody) == 0:
            self.builder.addText("pass")
        self.builder.unindent()
        self.builder.newLine("else:")
        self.builder.indent()
        for s in node.elseBody:
            self.visit(s)
        if len(node.elseBody) == 0:
            self.builder.addText("pass")
        self.builder.unindent()

    def ExprStmt(self, node: ExprStmt):
        self.builder.newLine()
        self.visit(node.expr)

    def BinaryExpr(self, node: BinaryExpr):
        self.builder.addText("(")
        self.visit(node.left)
        self.builder.addText(" " + node.operator + " ")
        self.visit(node.right)
        self.builder.addText(")")

    def UnaryExpr(self, node: UnaryExpr):
        self.builder.addText("(")
        self.builder.addText(node.operator + " ")
        self.visit(node.operand)
        self.builder.addText(")")

    def visitArg(self, node, funcType, paramIdx: int, argIdx: int):
        arg = node.args[argIdx]
        if isinstance(arg, Identifier) and arg.varInstance is None:
            self.visit(arg)
            return
        argIsRef = False
        paramIsRef = paramIdx in funcType.refParams
        if argIsRef and paramIsRef and arg.varInstance == funcType.refParams[paramIdx]:
            # ref arg and ref param, pass ref arg
            self.builder.addText(arg.name)
        elif paramIsRef:
            # non-ref arg and ref param, or do not pass ref arg
            self.builder.addText("[")
            self.visit(arg)
            self.builder.addText("]")
        else:  # non-ref param, maybe unwrap
            self.visit(arg)

    def CallExpr(self, node: CallExpr):
        # special case for builtins - always unwrap
        if node.function.name == "__assert__":
            self.builder.addText("assert ")
            self.visit(node.args[0])
            return
        elif node.function.name in {"print", "len"}:
            self.visit(node.function)
            self.builder.addText("(")
            self.visit(node.args[0])
            self.builder.addText(")")
            return
        self.visit(node.function)
        self.builder.addText("(")
        for i in range(len(node.args)):
            if node.isConstructor:
                self.visitArg(node, node.function.inferredType, i + 1, i)
            else:
                self.visitArg(node, node.function.inferredType, i, i)
            if i != len(node.args) - 1:
                self.builder.addText(", ")
        self.builder.addText(")")

    def WhileStmt(self, node: WhileStmt):
        self.builder.newLine("while ")
        self.visit(node.condition)
        self.builder.addText(":")
        self.builder.indent()
        for b in node.body:
            self.visit(b)
        if len(node.body) == 0:
            self.builder.addText("pass")
        self.builder.unindent()

    def ReturnStmt(self, node: ReturnStmt):
        self.builder.newLine("return ")
        if node.value is not None:
            self.visit(node.value)

    def Identifier(self, node: Identifier):
        if node.varInstance is None:
            self.builder.addText(node.name)
        else:
            self.builder.addText(node.name)

    def IfExpr(self, node: IfExpr):
        self.builder.addText("(")
        self.visit(node.thenExpr)
        self.builder.addText(" if ")
        self.visit(node.condition)
        self.builder.addText(" else ")
        self.visit(node.elseExpr)
        self.builder.addText(")")

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        self.builder.addText(str(node.value))

    def IntegerLiteral(self, node: IntegerLiteral):
        self.builder.addText(str(node.value))

    def NoneLiteral(self, node: NoneLiteral):
        self.builder.addText(str(node.value))

    def StringLiteral(self, node: StringLiteral):
        self.builder.addText(json.dumps(node.value))

    # TYPES

    def TypedVar(self, node: TypedVar):
        self.builder.addText(node.identifier.name)

    def ClassType(self, node: ClassType):
        self.builder.addText(node.className)
