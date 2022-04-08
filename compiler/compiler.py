import ast
from pathlib import Path
from typing import Optional

from .llvm_backend import LLVMBackend

from .astnodes import *
from .parser import ParseError, Parser
from .python_backend import PythonBackend
from .typechecker import TypeChecker
from .types import *
from .typesystem import TypeSystem


class Compiler:
    def __init__(self):
        self.ts = TypeSystem()
        self.parser = Parser()
        self.typechecker = TypeChecker(self.ts)
        self.transformer = None

    def parse(self, infile: Path) -> Optional[Node]:
        astparser = self.parser
        # given an input file, parse it into an AST object
        lines = None
        fname = infile.name
        with open(infile, "r") as f:
            lines = "".join([line for line in f])
        try:
            tree = ast.parse(lines)
            return astparser.visit(tree)
        except SyntaxError as e:
            e.filename = fname
            message = "Syntax Error: {}. Line {:d} Col {:d}".format(
                str(e), e.lineno, e.offset
            )
            astparser.errors.append(ParseError(message))
            return None

    def typecheck(self, ast: Node):
        # given an AST object, typecheck it
        # typechecking mutates the AST, adding types and errors
        self.typechecker.visit(ast)
        return ast

    def emitPython(self, ast: Node):
        backend = PythonBackend()
        backend.visit(ast)
        return backend.builder

    def emitLLVM(self, ast: Node):
        backend = LLVMBackend()
        ir = backend.visit(ast)
        return ir
