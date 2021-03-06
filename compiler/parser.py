from ast import List, Name, NodeVisitor, Str
from typing import List as ListAnnotation

from .astnodes import (
    AssignStmt,
    BinaryExpr,
    BooleanLiteral,
    CallExpr,
    ClassType,
    Declaration,
    Errors,
    Expr,
    ExprStmt,
    FuncDef,
    Identifier,
    IfExpr,
    IfStmt,
    IntegerLiteral,
    Literal,
    NoneLiteral,
    Program,
    ReturnStmt,
    Stmt,
    StringLiteral,
    TypeAnnotation,
    TypedVar,
    UnaryExpr,
    VarDef,
    WhileStmt,
)


class ParseError(Exception):
    # for AST structures that are legal in Python 3 but not in Chocopy
    def __init__(self, message, node=None):
        if node is not None:
            if hasattr(node, "lineno"):
                super().__init__(
                    message
                    + ". Line {:d} Col {:d}".format(node.lineno, node.col_offset)
                )
                return
        super().__init__(message + ".")


class Parser(NodeVisitor):
    def __init__(self):
        self.errors = []

    # reduce a list of >2 expressions separated by a
    # left-associative operator into a BinaryExpr tree
    def binaryReduce(self, op: str, values: ListAnnotation[Expr]) -> Expr:
        current = BinaryExpr(values[0].location, values[0], op, values[1])
        for v in values[2:]:
            current = BinaryExpr(values[0].location, current, op, v)
        return current

    def getLocation(self, node) -> ListAnnotation[int]:
        # input is Python AST node
        # get 2 item list corresponding to AST node starting location
        # make columns 1-indexed
        return [node.lineno, node.col_offset + 1]

    def visit(self, node):
        try:
            return super().visit(node)
        except ParseError as e:
            self.errors.append(e)
            return

    # process python AST nodes into chocopy type annotations
    def getTypeAnnotation(self, node) -> TypeAnnotation:
        location = self.getLocation(node)
        if isinstance(node, List):
            raise ParseError("Unsupported List type annotation", node)
        elif isinstance(node, Name):
            return ClassType(location, node.id)
        elif isinstance(node, Str):
            return ClassType(location, node.s)
        else:
            raise ParseError("Unsupported type annotation", node)

    # see https://greentreesnakes.readthedocs.io/en/latest/nodes.html
    # and https://docs.python.org/3/library/ast.html

    def visit_Module(self, node):
        location = [1, 1]
        if hasattr(node, "type_ignores") and node.type_ignores:
            raise ParseError("Cannot ignore type", node)
        body = [self.visit(b) for b in node.body]
        declarations = []
        statements = []
        decl = True
        for i in range(len(body)):
            b = body[i]
            if isinstance(b, Declaration):
                if isinstance(b, VarDef):
                    if not isinstance(b.value, Literal):
                        raise ParseError(
                            "Global variables can only be initialized with literals",
                            node.body[i],
                        )
                if decl == False:
                    raise ParseError(
                        "All declarations must come before statements", node.body[i]
                    )
                declarations.append(b)
            elif b is None or isinstance(b, Stmt):
                statements.append(b)
                decl = False
            else:
                raise ParseError("Expected declaration or statement", node.body[i])
        if declarations:
            location = declarations[0].location
        return Program(location, declarations, statements, Errors([0, 0], []))

    def visit_FunctionDef(self, node):
        if node.decorator_list:
            raise ParseError("Unsupported decorator list", node.decorator_list[0])
        location = self.getLocation(node)
        functionName = Identifier([location[0], location[1] + 4], node.name)
        arguments = self.visit(node.args)
        body = [self.visit(b) for b in node.body]
        declarations = []
        statements = []
        decl = True
        for i in range(len(body)):
            b = body[i]
            if isinstance(b, Declaration):
                if isinstance(b, FuncDef):
                    raise ParseError("Nested definitions are unsupported", node.body[i])
                if decl == False:
                    raise ParseError(
                        "All declarations must come before statements", node.body[i]
                    )
                declarations.append(b)
            elif b is None or isinstance(b, Stmt):
                statements.append(b)
                decl = False
            else:
                raise ParseError("Expected declaration or statement", node.body[i])
        returns = None
        if node.name == "__init__" and node.returns is not None:
            raise ParseError("__init__ cannot have a return type", node)
        if node.returns is None:
            returns = ClassType(location, "<None>")
        else:
            returns = self.getTypeAnnotation(node.returns)
        return FuncDef(
            location, functionName, arguments, returns, declarations, statements
        )

    def visit_Return(self, node):
        location = self.getLocation(node)
        if node.value == None:
            return ReturnStmt(location, None)
        else:
            return ReturnStmt(location, self.visit(node.value))

    def visit_Assign(self, node):
        location = self.getLocation(node)
        targets = [self.visit(t) for t in node.targets]
        return AssignStmt(location, targets, self.visit(node.value))

    def visit_AnnAssign(self, node):
        if not node.value:
            raise ParseError("Expected initializing value", node)
        if not hasattr(node, "annotation") or not node.annotation:
            raise ParseError("Missing type annotation", node)
        if not node.simple:
            raise ParseError("Expected variable", node.target)
        location = self.getLocation(node)
        var = TypedVar(
            self.getLocation(node.target),
            self.visit(node.target),
            self.getTypeAnnotation(node.annotation),
        )
        value = self.visit(node.value)
        if not isinstance(value, Literal):
            raise ParseError("Expected literal value", node.value)
        return VarDef(location, var, value)

    def visit_While(self, node):
        location = self.getLocation(node)
        if node.orelse:
            raise ParseError("Cannot have else in while", node)
        condition = self.visit(node.test)
        body = [self.visit(b) for b in node.body]
        for s in body:
            if isinstance(s, Declaration):
                raise ParseError("Cannot declare variables in loop", node)
        return WhileStmt(location, condition, body)

    def visit_For(self, node):
        raise ParseError("Unsupported", node)
        location = self.getLocation(node)
        if node.orelse:
            raise ParseError("Cannot have else in for", node)
        identifier = self.visit(node.target)
        iterable = self.visit(node.iter)
        body = [self.visit(b) for b in node.body]
        for s in body:
            if isinstance(s, Declaration):
                raise ParseError("Cannot declare variables in loop", node)
        return ForStmt(location, identifier, iterable, body)

    def visit_If(self, node):
        location = self.getLocation(node)
        condition = self.visit(node.test)
        then_body = [self.visit(b) for b in node.body]
        if not node.orelse:
            node.orelse = []
        else_body = [self.visit(o) for o in node.orelse]
        for s in then_body + else_body:
            if isinstance(s, Declaration):
                raise ParseError("Cannot declare variables in condition", node)
        return IfStmt(location, condition, then_body, else_body)

    def visit_Expr(self, node):
        # this is a Stmt that evaluates an Expr
        location = self.getLocation(node)
        val = self.visit(node.value)
        return ExprStmt(location, val)

    def visit_Pass(self, _):
        # removed by any AST constructors that take in [Stmt]
        return None

    def visit_BoolOp(self, node):
        values = [self.visit(v) for v in node.values]
        op = self.visit(node.op)
        return self.binaryReduce(op, values)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        location = self.getLocation(node)
        return BinaryExpr(location, left, self.visit(node.op), right)

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        location = self.getLocation(node)
        return UnaryExpr(location, self.visit(node.op), operand)

    def visit_IfExp(self, node):
        location = self.getLocation(node)
        condition = self.visit(node.test)
        then_body = self.visit(node.body)
        else_body = self.visit(node.orelse)
        return IfExpr(location, condition, then_body, else_body)

    def visit_Call(self, node):
        location = self.getLocation(node)
        function = self.visit(node.func)
        if node.keywords:
            raise ParseError("Keyword args are not supported", node)
        arguments = [self.visit(a) for a in node.args]
        if isinstance(function, Identifier):
            return CallExpr(location, function, arguments)
        raise ParseError("Invalid receiver of call", node.func)

    def visit_Constant(self, node):
        # support for Python 3.8
        location = self.getLocation(node)
        if isinstance(node.value, bool):
            return BooleanLiteral(location, node.value)
        elif isinstance(node.value, int):
            return IntegerLiteral(location, node.value)
        elif isinstance(node.value, str) and node.kind == None:
            return StringLiteral(location, node.value)
        elif node.value is None:
            return NoneLiteral(location)
        else:
            raise ParseError("Unsupported constant", node)

    def visit_Compare(self, node):
        if len(node.ops) > 1 or len(node.comparators) > 1:
            raise ParseError("Unsupported compare between > 2 things", node)
        location = self.getLocation(node)
        left = self.visit(node.left)
        operator = self.visit(node.ops[0])
        right = self.visit(node.comparators[0])
        return BinaryExpr(location, left, operator, right)

    def visit_Subscript(self, node):
        raise ParseError("Unsupported index operation", node)

    def visit_Name(self, node):
        location = self.getLocation(node)
        return Identifier(location, node.id)

    def visit_Num(self, node):
        location = self.getLocation(node)
        if not isinstance(node.n, int):
            raise ParseError("Only integers are supported", node)
        return IntegerLiteral(location, node.n)

    def visit_Str(self, node):
        location = self.getLocation(node)
        return StringLiteral(location, node.s)

    def visit_List(self, node):
        raise ParseError("Unsupported", node)

    def visit_NameConstant(self, node):
        location = self.getLocation(node)
        if node.value == None:
            return NoneLiteral(location)
        elif isinstance(node.value, bool):
            return BooleanLiteral(location, node.value)
        else:
            raise ParseError("Unsupported name constant", node)

    def visit_Index(self, node):
        raise ParseError("Unsupported", node)
        # return self.visit(node.value)

    def visit_arguments(self, node):
        if node.vararg:
            raise ParseError("Variable arguments are unsupported", node.vararg)
        if node.kwarg:
            raise ParseError("Keyword arguments are unsupported", node.kwarg)
        if node.defaults or node.kw_defaults:
            raise ParseError("Default arguments are unsupported", node)
        args = []
        if hasattr(node, "posonlyargs"):
            args = node.posonlyargs
        args = args + node.args
        args = [self.visit(a) for a in args]
        return args

    def visit_arg(self, node):
        # type annotation is either Str(s) or Name(id)
        if not hasattr(node, "annotation") or not node.annotation:
            raise ParseError("Missing type annotation", node)
        location = self.getLocation(node)
        identifier = Identifier(location, node.arg)
        annotation = self.getTypeAnnotation(node.annotation)
        return TypedVar(location, identifier, annotation)

    # operators

    def visit_And(self, _):
        return "and"

    def visit_Or(self, _):
        return "or"

    def visit_Add(self, _):
        return "+"

    def visit_Sub(self, _):
        return "-"

    def visit_Mult(self, _):
        return "*"

    def visit_Mod(self, _):
        return "%"

    def visit_FloorDiv(self, _):
        return "//"

    def visit_USub(self, _):
        return "-"

    def visit_Not(self, _):
        return "not"

    def visit_Eq(self, _):
        return "=="

    def visit_NotEq(self, _):
        return "!="

    def visit_Lt(self, _):
        return "<"

    def visit_LtE(self, _):
        return "<="

    def visit_Gt(self, _):
        return ">"

    def visit_GtE(self, _):
        return ">="

    def visit_Is(self, _):
        return "is"

    # Unsupported nodes
    def visit_Global(self, node):
        raise ParseError("Unsupported", node)

    def visit_ClassDef(self, node):
        raise ParseError("Unsupported", node)

    def visit_Attribute(self, node):
        raise ParseError("Unsupported", node)

    def visit_Nonlocal(self, node):
        raise ParseError("Unsupported", node)

    def visit_Expression(self, node):
        raise ParseError("Unsupported", node)

    def visit_AsyncFunctionDef(self, node):
        raise ParseError("Unsupported", node)

    def visit_Delete(self, node):
        raise ParseError("Unsupported", node)

    def visit_AsyncFor(self, node):
        raise ParseError("Unsupported", node)

    def visit_AugAssign(self, node):
        raise ParseError("Unsupported", node)

    def visit_With(self, node):
        raise ParseError("Unsupported", node)

    def visit_AsyncWith(self, node):
        raise ParseError("Unsupported", node)

    def visit_Raise(self, node):
        raise ParseError("Unsupported", node)

    def visit_Try(self, node):
        raise ParseError("Unsupported", node)

    def visit_Assert(self, node):
        raise ParseError("Unsupported", node)

    def visit_Import(self, node):
        raise ParseError("Unsupported", node)

    def visit_ImportFrom(self, node):
        raise ParseError("Unsupported", node)

    def visit_Break(self, node):
        raise ParseError("Unsupported", node)

    def visit_Continue(self, node):
        raise ParseError("Unsupported", node)

    def visit_Lambda(self, node):
        raise ParseError("Unsupported", node)

    def visit_Dict(self, node):
        raise ParseError("Unsupported", node)

    def visit_Set(self, node):
        raise ParseError("Unsupported", node)

    def visit_Bytes(self, node):
        raise ParseError("Unsupported", node)

    def visit_Ellipses(self, node):
        raise ParseError("Unsupported", node)

    def visit_ListComp(self, node):
        raise ParseError("Unsupported", node)

    def visit_SetComp(self, node):
        raise ParseError("Unsupported", node)

    def visit_DictComp(self, node):
        raise ParseError("Unsupported", node)

    def visit_GeneratorExp(self, node):
        raise ParseError("Unsupported", node)

    def visit_Await(self, node):
        raise ParseError("Unsupported", node)

    def visit_Yield(self, node):
        raise ParseError("Unsupported", node)

    def visit_YieldFrom(self, node):
        raise ParseError("Unsupported", node)

    def visit_FormattedValue(self, node):
        raise ParseError("Unsupported", node)

    def visit_JoinedStr(self, node):
        raise ParseError("Unsupported", node)

    def visit_Starred(self, node):
        raise ParseError("Unsupported", node)

    def visit_Tuple(self, node):
        raise ParseError("Unsupported", node)

    def visit_AugLoad(self, node):
        raise ParseError("Unsupported", node)

    def visit_AugStore(self, node):
        raise ParseError("Unsupported", node)

    def visit_MatMult(self, _):
        raise ParseError("Unsupported operator: @")

    def visit_Div(self, _):
        raise ParseError("Unsupported operator: /")

    def visit_Slice(self, _):
        raise ParseError("Unsupported slice")

    def visit_ExtSlice(self, _):
        raise ParseError("Unsupported slice")

    def visit_Pow(self, _):
        raise ParseError("Unsupported operator: **")

    def visit_LShift(self, _):
        raise ParseError("Unsupported operator: <<")

    def visit_RShift(self, _):
        raise ParseError("Unsupported operator: >>")

    def visit_BitOr(self, _):
        raise ParseError("Unsupported operator: |")

    def visit_BitXor(self, _):
        raise ParseError("Unsupported operator: ^")

    def visit_BitAnd(self, _):
        raise ParseError("Unsupported operator: &")

    def visit_UAdd(self, _):
        raise ParseError("Unsupported operator: unary +")

    def visit_Invert(self, _):
        raise ParseError("Unsupported operator: ~")

    def visit_IsNot(self, _):
        raise ParseError("Unsupported operator: is not")

    def visit_In(self, _):
        raise ParseError("Unsupported operator: in")

    def visit_NotIn(self, _):
        raise ParseError("Unsupported operator: not in")

    def visit_ExceptHandlerattributes(self, node):
        raise ParseError("Unsupported", node)

    def visit_TypeIgnore(self, node):
        raise ParseError("Unsupported", node)

    def visit_FunctionType(self, node):
        raise ParseError("Unsupported", node)

    def visit_Suite(self, node):
        raise ParseError("Unsupported", node)

    def visit_Interactive(self, node):
        raise ParseError("Unsupported", node)

    def visit_alias(self, node):
        raise ParseError("Unsupported", node)

    def visit_keyword(self, node):
        raise ParseError("Unsupported", node)

    def visit_comprehension(self, node):
        raise ParseError("Unsupported", node)

    def visit_withitem(self, node):
        raise ParseError("Unsupported", node)

    def visit_NamedExpr(self, node):
        raise ParseError("Unsupported", node)

    # expression contexts - do nothing

    def visit_Load(self, _):
        pass

    def visit_Store(self, _):
        pass

    def visit_Del(self, _):
        pass

    def visit_Param(self, _):
        pass
