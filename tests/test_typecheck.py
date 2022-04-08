import json
import traceback
from pathlib import Path
from typing import List
from unittest import TestCase

from compiler.compiler import Compiler


class TestTypechecker(TestCase):
    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        self.parse_test_dir = (Path(__file__).parent / "parse").resolve()
        self.tc_test_dir = (Path(__file__).parent / "typecheck").resolve()
        self.runtime_test_dir = (Path(__file__).parent / "runtime").resolve()

    def get_test_files(self, dirs: List[Path]):
        for dir in dirs:
            for file in dir.glob("*.py"):
                yield file

    def test_tc(self):
        for file in self.get_test_files(
            [
                self.tc_test_dir,
            ]
        ):
            with self.subTest(file=file):
                try:
                    compiler = Compiler()
                    astparser = compiler.parser
                    ast = compiler.parse(file)
                    self.assertFalse(len(astparser.errors) > 0)
                    compiler.typecheck(ast)
                    ast_json = ast.toJSON(True)
                    with file.with_suffix(".py.ast.typed").open("r") as f:
                        correct_json = json.load(f)
                        self.assertTrue(ast_equals(ast_json, correct_json))
                except Exception as e:
                    print("Internal compiler error")
                    print(e)
                    print(traceback.format_exc())
                    self.assertTrue(False)

        for file in self.get_test_files(
            [
                self.runtime_test_dir,
            ]
        ):
            with self.subTest(file=file):
                try:
                    compiler = Compiler()
                    astparser = compiler.parser
                    ast = compiler.parse(file)
                    self.assertFalse(len(astparser.errors) > 0)
                    compiler.typecheck(ast)
                    self.assertFalse(len(ast.errors.errors) > 0)
                except Exception as e:
                    print("Internal compiler error")
                    print(e)
                    print(traceback.format_exc())
                    self.assertTrue(False)


def ast_equals(d1, d2) -> bool:
    # precondition: the input dict must represent a well-formed AST
    # d1 is the correct AST, d2 is the AST output by this compiler
    if isinstance(d1, dict) and isinstance(d2, dict):
        for k, v in d1.items():
            if k not in d2 and k != "inferredType":
                print("Expected field: " + k)
                return False
            # only check starting line of node
            if k == "location":
                if d1[k][0] != d2[k][0]:
                    print(
                        "Expected starting line {:d}, got {:d}".format(
                            d1[k][0], d2[k][0]
                        )
                    )
                    return False
            # check number of errors, not the messages
            elif k == "errors":
                if len(d1[k]["errors"]) != len(d2[k]["errors"]):
                    print(
                        "Expected {:d} errors, got {:d}".format(
                            len(d1[k]["errors"]), len(d2[k]["errors"])
                        )
                    )
                    return False
            elif k == "errorMsg":
                pass  # only check presence of message, not content
            elif k == "inferredType":
                if k in d2 and not ast_equals(v, d2[k]):
                    return False
            elif not ast_equals(v, d2[k]):
                return False
        for k in d2.keys():
            if k not in d1 and k != "inferredType":
                print("Unxpected field: " + k)
                return False
        return True
    if isinstance(d1, list) and isinstance(d2, list):
        if len(d1) != len(d2):
            print("Expected list of length {:s}, got {:s}".format(len(d1), len(d2)))
            return False
        for i in range(len(d1)):
            if not ast_equals(d1[i], d2[i]):
                return False
        return True
    if d1 != d2:
        print("Expected {:s}, got {:s}".format(str(d1), str(d2)))
    return d1 == d2
