from collections import defaultdict
from typing import Dict, List, Optional

from compiler.astnodes import (
    AssignStmt,
    BinaryExpr,
    BooleanLiteral,
    CallExpr,
    ClassType,
    CompilerError,
    FuncDef,
    Identifier,
    IfExpr,
    IfStmt,
    IntegerLiteral,
    NoneLiteral,
    Program,
    ReturnStmt,
    StringLiteral,
    TypedVar,
    UnaryExpr,
    VarDef,
    WhileStmt,
)

from .types import (
    BoolType,
    ClassValueType,
    FuncType,
    IntType,
    NoneType,
    ObjectType,
    StrType,
    SymbolType,
    ValueType,
)
from .typesystem import TypeSystem
from .visitor import Node, Visitor


class TypeChecker(Visitor):
    def __init__(self, ts: TypeSystem):
        # typechecker attributes and their chocopy typing judgement analogues:
        # O : symbolTable
        # M : classes
        # C : currentClass
        # R : expReturnType

        # stack of hashtables representing scope
        # each table holds identifier->type mappings defined in that scppe
        self.symbolTables: List[Dict[str, Optional[SymbolType]]] = [
            defaultdict(lambda: None)
        ]

        # standard library functions
        self.symbolTables[0]["print"] = FuncType([ObjectType()], NoneType())
        self.symbolTables[0]["input"] = FuncType([], StrType())
        self.symbolTables[0]["len"] = FuncType([ObjectType()], IntType())
        self.symbolTables[0]["__assert__"] = FuncType([BoolType()], NoneType())
        self.symbolTables[0]["printf"] = FuncType(
            [StrType(), ObjectType()], IntType()
        )

        self.ts = ts

        self.errors = []  # list of errors encountered
        self.currentClass = None  # name of current class
        self.expReturnType = None  # expected return type of current function

        self.program = None
        self.addErrors = True

    def visit(self, node: Node):
        if isinstance(node, Program) or isinstance(node, FuncDef):
            return node.visit(self)
        else:
            return node.postorder(self)

    def funcParams(self, _: FuncDef):
        pass

    def enterScope(self):
        self.symbolTables.append(defaultdict(lambda: None))

    def exitScope(self):
        self.symbolTables.pop()

    # SYMBOL TABLE LOOKUPS

    def getType(self, var: str) -> Optional[SymbolType]:
        # get the type of an identifier in the current scope, or None if not found
        for table in self.symbolTables[::-1]:
            if var in table:
                return table[var]
        return None

    def getLocalType(self, var: str) -> Optional[SymbolType]:
        # get the type of an identifier in the current scope, or None if not found
        # ignore global variables
        for table in self.symbolTables[1:][::-1]:
            if var in table:
                return table[var]
        return None

    def getGlobal(self, var: str) -> Optional[SymbolType]:
        return self.symbolTables[0][var]

    def addType(self, var: str, t: SymbolType):
        self.symbolTables[-1][var] = t

    def defInCurrentScope(self, var: str) -> bool:
        # return if the name was defined in the current scope
        return self.symbolTables[-1][var] is not None

    # ERROR HANDLING

    def addError(self, node: Node, message: str):
        if self.addErrors:
            if node.errorMsg is not None:  # 1 error msg per node
                return
            message = f"{message}. Line {node.location[0]} Col {node.location[1]}"
            node.errorMsg = message
            self.program.errors.errors.append(CompilerError(node.location, message))
            self.errors.append(message)

    def binopError(self, node):
        self.addError(
            node,
            "Cannot use operator {} on types {} and {}".format(
                node.operator, node.left.inferredType, node.right.inferredType
            ),
        )

    # UTIL

    def getSignature(self, node: FuncDef) -> FuncType:
        rType = self.visit(node.returnType)
        return FuncType([self.visit(t) for t in node.params], rType)

    def Program(self, node: Program) -> None:
        self.program = node
        for d in node.declarations:
            identifier = d.getIdentifier()
            if self.defInCurrentScope(identifier.name) or self.ts.classExists(
                identifier.name
            ):
                self.addError(
                    identifier,
                    f"Duplicate declaration of identifier: {identifier.name}",
                )
            if isinstance(d, FuncDef):
                self.funcParams(d)
                self.addType(d.getIdentifier().name, self.getSignature(d))
            if isinstance(d, VarDef):
                self.addType(identifier.name, self.visit(d.var))
        for d in node.declarations:
            if d.getIdentifier().errorMsg is not None:
                continue
            self.visit(d)
        if len(self.errors) > 0:
            return
        for s in node.statements:
            self.visit(s)

    def VarDef(self, node: VarDef) -> ValueType:
        annotationType = self.visit(node.var)
        if not self.ts.canAssign(node.value.inferredType, annotationType):
            self.addError(
                node, f"Expected {annotationType}, got {node.value.inferredType}"
            )
        return annotationType

    def FuncDef(self, node: FuncDef) -> Optional[FuncType]:
        self.enterScope()
        funcName = node.getIdentifier().name
        funcType = self.getSignature(node)
        node.type = funcType
        self.expReturnType = funcType.returnType
        if not node.isMethod:  # top level function decl OR nested function
            if self.ts.classExists(funcName):
                self.addError(
                    node.getIdentifier(), f"Functions cannot shadow classes: {funcName}"
                )
                return
            if self.defInCurrentScope(funcName):
                self.addError(
                    node.getIdentifier(),
                    f"Function redeclared: {funcName}",
                )
                return
            self.addType(funcName, funcType)
        else:  # method decl
            if (
                len(node.params) == 0
                or node.params[0].identifier.name != "self"
                or (not isinstance(funcType.parameters[0], ClassValueType))
                or funcType.parameters[0].className != self.currentClass
            ):
                self.addError(
                    node.getIdentifier(), f"Missing self param in method: {funcName}"
                )
                return
        for p in node.params:
            t = self.visit(p)
            pName = p.identifier.name
            if self.defInCurrentScope(pName) or self.ts.classExists(pName):
                self.addError(p.identifier, f"Duplicate parameter name: {pName}")
                continue
            if t is not None:
                self.addType(pName, t)

        for d in node.declarations:
            identifier = d.getIdentifier()
            name = identifier.name
            if self.defInCurrentScope(name) or self.ts.classExists(name):
                self.addError(
                    identifier, f"Duplicate declaration of identifier: {name}"
                )
                continue
            if isinstance(d, FuncDef):
                self.funcParams(d)
                self.addType(name, self.getSignature(d))
            if isinstance(d, VarDef):
                self.addType(name, self.visit(d.var))
        rType = self.expReturnType
        for d in node.declarations:
            self.visit(d)
            self.expReturnType = rType
        hasReturn = False
        for s in node.statements:
            self.visit(s)
            if s.isReturn:
                hasReturn = True
        if (not hasReturn) and (not self.ts.canAssign(NoneType(), self.expReturnType)):
            self.addError(
                node.getIdentifier(),
                f"Expected return statement of type {self.expReturnType}",
            )
        self.expReturnType = None
        self.exitScope()
        return funcType

    # STATEMENTS (returns None) AND EXPRESSIONS (returns inferred type)

    def AssignStmt(self, node: AssignStmt):
        # variables can only be assigned to if they're defined in current scope
        for t in node.targets:
            if isinstance(t, Identifier) and not self.defInCurrentScope(t.name):
                self.addError(
                    t, f"Identifier not defined in current scope: {t.name}"
                )
                return
            if not self.ts.canAssign(node.value.inferredType, t.inferredType):
                self.addError(
                    node,
                    f"Expected {t.inferredType}, got {node.value.inferredType}",
                )
                return

    def IfStmt(self, node: IfStmt) -> None:
        # isReturn=True if there's >=1 statement in BOTH branches that have isReturn=True
        # if a branch is empty, isReturn=False
        if node.condition.inferredType != BoolType():
            self.addError(
                node.condition,
                f"Expected {BoolType()}, got {node.condition.inferredType}",
            )
            return
        thenBody = False
        elseBody = False
        for s in node.thenBody:
            if s.isReturn:
                thenBody = True
        for s in node.elseBody:
            if s.isReturn:
                elseBody = True
        node.isReturn = thenBody and elseBody

    def BinaryExpr(
        self, node: BinaryExpr
    ) -> Optional[ClassValueType]:
        operator = node.operator
        static_types = {IntType(), BoolType(), StrType()}
        leftType = node.left.inferredType
        rightType = node.right.inferredType

        # concatenation and addition
        if operator == "+":
            if leftType == rightType and leftType in {StrType(), IntType()}:
                node.inferredType = leftType
                return leftType
            else:
                self.binopError(node)

        # other arithmetic operators
        elif operator in {"-", "*", "//", "%"}:
            if leftType == IntType() and rightType == IntType():
                node.inferredType = IntType()
                return IntType()
            else:
                self.binopError(node)

        # relational operators
        elif operator in {"<", "<=", ">", ">="}:
            if leftType == IntType() and rightType == IntType():
                node.inferredType = BoolType()
                return BoolType()
            else:
                self.binopError(node)
        elif operator in {"==", "!="}:
            if leftType == rightType and leftType in static_types:
                node.inferredType = BoolType()
                return BoolType()
            else:
                self.binopError(node)
        elif operator == "is":
            if leftType not in static_types and rightType not in static_types:
                node.inferredType = BoolType()
                return BoolType()
            else:
                self.binopError(node)

        # logical operators
        elif operator in {"and", "or"}:
            if leftType == BoolType() and rightType == BoolType():
                node.inferredType = BoolType()
                return BoolType()
            else:
                self.binopError(node)

        else:
            node.inferredType = ObjectType()
            return ObjectType()

    def UnaryExpr(self, node: UnaryExpr):
        operandType = node.operand.inferredType
        if node.operator == "-":
            if operandType == IntType():
                node.inferredType = IntType()
                return IntType()
            else:
                self.addError(node, f"Expected int, got {operandType}")
        elif node.operator == "not":
            if operandType == BoolType():
                node.inferredType = BoolType()
                return BoolType()
            else:
                self.addError(node, f"Expected bool, got {operandType}")
        else:
            node.inferredType = ObjectType()
            return ObjectType()

    def CallExpr(self, node: CallExpr):
        fname = node.function.name
        t = None
        if self.ts.classExists(fname):
            # constructor
            node.isConstructor = True
            t = self.ts.getMethod(fname, "__init__")
            if len(t.parameters) != len(node.args) + 1:
                self.addError(
                    node, f"Expected {len(t.parameters) - 1} args, got {len(node.args)}"
                )
            else:
                for i in range(len(t.parameters) - 1):
                    if not self.ts.canAssign(
                        node.args[i].inferredType, t.parameters[i + 1]
                    ):
                        self.addError(
                            node,
                            f"Expected {t.parameters[i + 1]}, got {node.args[i].inferredType}",
                        )
                        continue
            node.inferredType = ClassValueType(fname)
        else:
            t = self.getType(fname)
            if not isinstance(t, FuncType):
                self.addError(node, f"Not a function: {fname}")
                node.inferredType = ObjectType()
                return ObjectType()
            if len(t.parameters) != len(node.args):
                self.addError(
                    node, f"Expected {len(t.parameters)} args, got {len(node.args)}"
                )
            else:
                for i in range(len(t.parameters)):
                    if not self.ts.canAssign(
                        node.args[i].inferredType, t.parameters[i]
                    ):
                        self.addError(
                            node,
                            f"Expected {t.parameters[i]}, got {node.args[i].inferredType}",
                        )
                        continue
            node.inferredType = t.returnType
        node.function.inferredType = t
        return node.inferredType

    def WhileStmt(self, node: WhileStmt):
        if node.condition.inferredType != BoolType():
            self.addError(
                node.condition,
                f"Expected {BoolType()}, got {node.condition.inferredType}",
            )
            return
        for s in node.body:
            if s.isReturn:
                node.isReturn = True

    def ReturnStmt(self, node: ReturnStmt):
        if self.expReturnType is None:
            self.addError(node, "Return statement outside of function definition")
        elif node.value is None:
            if not self.ts.canAssign(NoneType(), self.expReturnType):
                self.addError(node, f"Expected {self.expReturnType}, got {NoneType()}")
        elif not self.ts.canAssign(node.value.inferredType, self.expReturnType):
            self.addError(
                node, f"Expected {self.expReturnType}, got {node.value.inferredType}"
            )
        node.expType = self.expReturnType
        return

    def Identifier(self, node: Identifier):
        varType = None
        if self.expReturnType is None and self.currentClass is None:
            varType = self.getGlobal(node.name)
        else:
            varType = self.getType(node.name)
        if varType is not None and isinstance(varType, ValueType):
            node.inferredType = varType
        else:
            self.addError(node, f"Unknown identifier: {node.name}")
            node.inferredType = ObjectType()
        return node.inferredType

    def IfExpr(self, node: IfExpr):
        if node.condition.inferredType != BoolType():
            self.addError(f"Expected boolean, got {node.condition.inferredType}")
        node.inferredType = self.ts.join(
            node.thenExpr.inferredType, node.elseExpr.inferredType
        )
        return node.inferredType

    # LITERALS

    def BooleanLiteral(self, node: BooleanLiteral):
        node.inferredType = BoolType()
        return node.inferredType

    def IntegerLiteral(self, node: IntegerLiteral):
        node.inferredType = IntType()
        return node.inferredType

    def NoneLiteral(self, node: NoneLiteral):
        node.inferredType = NoneType()
        return node.inferredType

    def StringLiteral(self, node: StringLiteral):
        node.inferredType = StrType()
        return node.inferredType

    # TYPES

    def TypedVar(self, node: TypedVar):
        # return the type of the annotaton
        node.t = self.visit(node.type)
        return node.t

    def ClassType(self, node: ClassType):
        if node.className not in {"<None>", "<Empty>"} and not self.ts.classExists(
            node.className
        ):
            self.addError(node, f"Unknown class: {node.className}")
            return ObjectType()
        else:
            return ClassValueType(node.className)
