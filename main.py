import argparse
import json
import unittest
from pathlib import Path
from typing import Optional

from compiler.astnodes import Node
from compiler.compiler import Compiler

mode_help = (
    "Modes:\n"
    + "parse    - output AST in JSON format\n"
    + "tc       - output typechecked AST in JSON format\n"
    + "python   - output untyped Python 3 source code (default)\n"
    + "llvm     - output LLVM IR code\n"
)


def validate(parser, input: Optional[str]) -> Path:
    if input is None:
        parser.print_help()
        raise ValueError("must specify input file")

    input_path = Path(input)

    if input_path.suffix != ".py":
        raise ValueError("input file must end with .py")

    return input_path


def main():
    parser = argparse.ArgumentParser(
        description="Chocollvm - a ChocoPy compiler frontend",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        dest="mode",
        choices=["parse", "tc", "python", "llvm"],
        default="python",
        help=mode_help,
    )
    parser.add_argument(
        "--test", dest="test", action="store_true", help="run all test cases"
    )
    parser.add_argument(
        "input", nargs="?", type=str, help="ChocoPy file to process", default=None
    )
    args = parser.parse_args()

    if args.test:
        loader = unittest.TestLoader()
        start_dir = str(Path(__file__).parent.resolve())
        suite = loader.discover(start_dir)

        runner = unittest.TextTestRunner(verbosity=5)
        runner.run(suite)
        return

    infile = validate(parser, args.input)

    compiler = Compiler()
    astparser = compiler.parser
    tc = compiler.typechecker
    tree = compiler.parse(infile)

    if len(astparser.errors) > 0 or not isinstance(tree, Node):
        for e in astparser.errors:
            print(e)
        raise Exception("Encountered parse errors. Exiting.")
    elif args.mode != "parse":
        compiler.typecheck(tree)
        if len(tc.errors) > 0:
            for e in tc.errors:
                print(e)
            raise Exception("Encountered typecheck errors. Exiting.")

    if args.mode in {"parse", "tc"}:
        ast_json = tree.toJSON(False)
        print(json.dumps(ast_json, indent=2))
    elif args.mode == "python":
        builder = compiler.emitPython(tree)
        print(builder.emit())
    elif args.mode == "llvm":
        ir = compiler.emitLLVM(tree)
        print(ir.module)


if __name__ == "__main__":
    main()
