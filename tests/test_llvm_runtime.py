import ast
import subprocess
import traceback
from pathlib import Path
from typing import List
from unittest import TestCase

from compiler.compiler import Compiler

error_flags = {"error", "Error", "Exception", "exception", "Expected", "expected"}


class TestLLVMRuntime(TestCase):
    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        self.llvm_test_dir = (Path(__file__).parent / "llvm").resolve()

    def get_test_files(self, dirs: List[Path]):
        for dir in dirs:
            for file in dir.glob("*.py"):
                yield file

    def test_llvm_emit(self):
        for file in self.get_test_files(
            [
                self.llvm_test_dir,
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

    def test_llvm_execute(self):
        for file in self.get_test_files(
            [
                self.llvm_test_dir,
            ]
        ):
            with self.subTest(file=file):
                try:
                    compiler = Compiler()
                    astparser = compiler.parser
                    chocopy_ast = compiler.parse(file)
                    self.assertFalse(len(astparser.errors) > 0)

                    compiler.typecheck(chocopy_ast)
                    ir = compiler.emitLLVM(chocopy_ast)
                    file_base_name = file.with_suffix("").name
                    name = f"./{file_base_name}.test.ll"
                    with open(name, "w") as f:
                        f.write(str(ir.module))

                    output = subprocess.check_output(
                        f"cd {str(Path(__file__).parent.parent.resolve())} && lli {name}",
                        shell=True,
                    )
                    decoded = output.decode()

                    expected_result_file = file.with_suffix(".txt")
                    with open(expected_result_file) as e:
                        expected_result = e.read()
                        self.assertEqual(decoded, expected_result)

                    lines = decoded.split("\n")
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
