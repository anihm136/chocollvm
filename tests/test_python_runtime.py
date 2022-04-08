import ast
import subprocess
import traceback
from pathlib import Path
from typing import List
from unittest import TestCase

from compiler.compiler import Compiler

error_flags = {"error", "Error", "Exception", "exception", "Expected", "expected"}


class TestPythonRuntime(TestCase):
    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        self.parse_test_dir = (Path(__file__).parent / "parse").resolve()
        self.tc_test_dir = (Path(__file__).parent / "typecheck").resolve()
        self.runtime_test_dir = (Path(__file__).parent / "runtime").resolve()

    def get_test_files(self, dirs: List[Path]):
        for dir in dirs:
            for file in dir.glob("*.py"):
                yield file

    def test_python_emit(self):
        for file in self.get_test_files(
            [
                self.tc_test_dir,
            ]
        ):
            with self.subTest(file=file):
                if file.name.startswith("bad"):
                    continue

                try:
                    compiler = Compiler()
                    astparser = compiler.parser
                    chocopy_ast = compiler.parse(file)
                    self.assertFalse(len(astparser.errors) > 0)
                    compiler.typecheck(chocopy_ast)
                    builder = compiler.emitPython(chocopy_ast)
                    ast.parse(builder.emit())
                    self.assertTrue(True)
                except Exception as e:
                    print("Internal compiler error")
                    print(e)
                    print(traceback.format_exc())
                    self.assertTrue(False)

    def test_python_execute(self):
        for file in self.get_test_files(
            [
                self.runtime_test_dir,
            ]
        ):
            with self.subTest(file=file):
                try:
                    compiler = Compiler()
                    astparser = compiler.parser
                    chocopy_ast = compiler.parse(file)
                    self.assertFalse(len(astparser.errors) > 0)

                    compiler.typecheck(chocopy_ast)
                    builder = compiler.emitPython(chocopy_ast)
                    file_base_name = file.with_suffix("").name
                    name = f"./{file_base_name}.test.py"
                    with open(name, "w") as f:
                        f.write(builder.emit())

                    output = subprocess.check_output(
                        f"cd {str(Path(__file__).parent.parent.resolve())} && python3 {name}",
                        shell=True,
                    )
                    lines = output.decode().split("\n")
                    passed = True
                    for line in lines:
                        for e in error_flags:
                            if e in line:
                                passed = False
                                print(line)
                                break
                    self.assertTrue(passed)
                except subprocess.CalledProcessError as e:
                    print("Subprocess error")
                    print(e.output)
                    print(e)
                    self.assertTrue(False)
                except Exception as e:
                    print("Internal compiler error")
                    print(e)
                    print(traceback.format_exc())
                    self.assertTrue(False)

    def tearDown(self):
        subprocess.run(
            f"cd {str(Path(__file__).parent.parent.resolve())} && make -s clean",
            shell=True,
        )
