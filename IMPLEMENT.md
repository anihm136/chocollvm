# Project Objectives
This document covers the objectives of the project, and provides a brief overview on each of them.

- This project will focus on LLVM IR Code generation i.e, the final stage of a compiler frontend. The parser and typechecker will be provided, which will return a typechecked AST for a program, appropriately handling any parsing or type errors
- A reference implementation of a code generation backend is provided in [compiler/python_backend.py](./compiler/python_backend.py), which converts ChocoPy code to untyped python code. This implementation will help in understanding the approach to traverse the AST for code generation
- The LLVM code generation backend is provided in [compiler/llvm_backend.py](./compiler/llvm_backend.py). This file contains a code skeleton for implementing the backend, and also implements code generation for certain language features. This is also to serve as a reference for the project

## Language features to be implemented
### VarDef
Variable definitions are of the form `{id}:{type} = {value}`. Variable definitions only appear before all statements in the top-level of a program, and before all statements in a function definition. The value must be a constant i.e, variables cannot be initialized with the value of another variable.
### AssignStmt
Variable assignments may appear in the statements section of the top-level, as well as function definitions. An assignment is of the form `{targets} = {value}`. `{targets}` is a series of one or more variables that have been previously declared, and `{value}` may either be a constant value or an identifier to another variable.
### IfStmt
An `if` statement is of the form
```
if cond:
	stmts
elif cond2:
	stmts
else:
	stmts
```
`cond` is an expression that evaluates to a boolean value
_Hint_: The above example is converted by the parser into an equivalent structure:
```
if cond:
	stmts
else:
	if cond2:
		stmts
	else:
		stmts
```
Hence, you may not have to explicitly handle code generation for the `elif` statement.
### BinaryExpr
A binary expression is an expression containing two operands and an associated operator. Binary expressions may be arithmetic, logical or relational, and may take integers or booleans as arguments.
### IfExpr
An `if` expression is an expression of the form `a if cond else b`

_Note_: An `if` expression is different from an `if` statement. The `if` expression evaluates to a single value, which is determined by the condition `cond`
### Identifier
An identifier is a name that identifies an entity in the program. An entity may either be a variable or a function

### Implementation guide - WhileStmt
A `while` loop is of the form
```
while cond:
	stmts
```
`cond` is an expression that evaluates to a boolean value.
Please refer to the video resources [provided](https://drive.google.com/drive/folders/1Xc3tFMkWHIvOepwZyWj1mSYqwy-0RLWg?usp=sharing) for the implementation guide.

## Approach and tips
- When implementing code generation for a specific feature, start by writing a simple ChocoPy program that uses that feature (and ideally, does not use any other unimplemented feature)
- Run the typechecker on the program to see the structure of the AST. This will help in understanding how to traverse the tree, and how to handle various entities in the program. You can also refer to the various node definitions in [compiler/astnodes/](./compiler/astnodes/) to understand the information available in each node
- Refer to the [language specification](./SPEC.md) to understand the scope of each language feature, what needs to be implemented and what can be ignored
- The test suite contains a fairly comprehensive set of cases to ensure the compiler is working as expected. If your compiler passes the test suite, it is highly likely that it is functioning correctly
