# Welcome to REPLang
REPLang is a statically typed language programming language designed with working in REPL (read-evaluate-print loop) in mind. 
It is as easy to type as possible, tries to use fewest brackets possible, and everything can be written as an one-liner.

Please note that REPLang is not designed to be a fully-fledged programming language.
I tried to learn as much as possible during development, not make it as good as possible.
It is written in python using PLY, and only slightly optimized.
It is best used as a comfortable and easy to use calculator.

This repository also contains a converter from a subset of HTML to markdown language, and a RPN calculator,
which are covered after REPLang

# Using REPLang
REPLang was inspired by languages such as Scala and Haskell, however it is not a functional language -
it has variables and a while loop.

Everything in REPLang is an expression, even assignment, declaration and 'print', with one exception:
function definition.

Quick overview of REPLang constructs:

**Data types**
* int (Integer)
* float (Floating point number)
* str (String of characters)
* bool (True or False)

**Reserved keywords**
* 'while'
* 'do'
*   'end'
*    'if'
*    'then'
*    'else'
*    'int'
*   'float'
*   'str'
*   'bool'
*   'True'
*   'False'
*   'tobool'
*   'tofloat'
*   'toint'
*   'tostr'
*   'def'
*   'not'
*   'print'

**Operators**
* '+'  - addition
* '-' - subtraction and unary minus
* '*' - multiplication
* '/' - division
* '^' - power 
* '=' - assignment
* '==' / '!=' - comparison
* '>' / '<' - greater/less than

**The full precedence of operators and keywords**

The lower on the list, the higher priority / lower precedence.
Intuitively, operations lower on the list will be evaluated first.
The associativity means the order of same-level operations, e.g.

'/' has left associativity, so in `8 / 4 / 2` 
The evaluation order is `(8 / 4) / 2 == 1.0` instead of
`8 / (4 / 2) == 4`. Similarly '^' has right associativity, so `3^2^4` evaluates to `3^(2^4) == 3^16` instead of `9^4`  
*    ('left', 'if', 'else', 'then', 'while'),
*    ('left', ';'),
*    ('left', 'print'),
*    ('left', '==', '!=', '>', '<'),
*    ('left', 'not'),
*    ('left', '='),
*    ('right', 'toint', 'tofloat', 'tostr', 'tobool'),
*    ('left', '+', '-'),
*    ('left', '*', '/'),
*    ('right', '^'),
*    ('right', 'UMINUS'),

# Getting started with REPLang
REPLang depends on [PLY](https://www.dabeaz.com/ply/) and python 3.x. First, PLY should be installed and this repo cloned:

```
pip install ply
git clone https://github.com/klasocki/REPLang.git & cd REPLang
```

Then, you can use REPLang in REPL mode, with parsing tree visualization (as tuples) by:

`python3 repl.py`

or have it execute a program from a file, specified as an argument:

`python3 repl.py program.repl`

'program.repl' is an example program provided with this repository.

When running program from a file, each expression, except the last one
 (last in the program, if, while or function) must end with a ';'. 
REPLang is whitespace insensitive, you can format your code in any way that looks good to you.


**Main instruction types with examples**
* Statement: Expression

This is the base instruction for everything other than function definition. The expression is evaluated, and
if running in REPL mode, REPLang will first print the syntax tree (if the expression is not a simple value)
, and then the value of the expression.
```
REPLang > "hello world"
hello world
```
Floating point numbers can be written in any correct form:
```
REPLang > 3.5     
3.5
REPLang > 3.
3.0
REPLang > .5
0.5
```
* Expression: variable definition
```
REPLang > int x = 3
('declare', <class 'int'>, 'x', 3)
3
REPLang > bool y = True
('declare', <class 'bool'>, 'y', True)
True
REPLang > int x = 4
<class 'RuntimeError'> x already declared
```
Now we can see a bit of the inner workings of REPLang - 
the declarations are parsed as a 'declare' expression,
followed by the type of the variable, name, and value. 
Each of these is required - each variable needs to have a type 
and an initializer at definition time. The type cannot be changed, but the value is mutable

* Expression: name 
```
REPLang > x 
('name', 'x')
3
REPLang > y
('name', 'y')
<class 'LookupError'> Name y undefined
```
Value of the variable in the **current scope** (more on that later) is retrieved
* Expression: binop (Binary operation)
```
REPLang > x + 4
('binop', ('name', 'x'), '+', 4)
7
REPLang > (x + 2) * 3 > 15
('binop', ('binop', ('binop', ('name', 'x'), '+', 2), '*', 3), '>', 15)
False
REPLang > x / -1 * x ^ -1 == -1
('binop', ('binop', ('binop', ('name', 'x'), '/', -1), '*', ('binop', ('name', 'x'), '^', -1)), '==', -1)
True
```
Binary operations have the format of 'expression' operator 'expression'.

The expression can be anything - also another binop which we see in the examples.

The operation priority is handled correctly - boolean operations (==, >, <) take much of the input as an argument,
while the unary '-' operator is the strongest, binding only the following expression and evaluated immediately.

Desired order of calculations can be enforced using parenthesis.

The operators are overloaded to work correctly with different types, 
and typechecking is performed at each operation:
```
REPLang > "hello" + " " + "world"
hello world
REPLang > "hello " * 3
hello hello hello 
REPLang > True - 4
<class 'TypeError'> Unsupported operand - between instances of <class 'bool'> and <class 'int'>
```
* Expression: assignment
```
REPLang > x = 4
('assign', 'x', 4)
4
REPLang > int y = x = x + 1
('declare', <class 'int'>, 'y', ('assign', 'x', ('binop', ('name', 'x'), '+', 1)))
5
REPLang > y
('name', 'y')
5
REPLang > y = "random string"
<class 'TypeError'> Expected type <class 'int'> for y, got <class 'str'>
```
Declared variables can be reassigned, but only with expressions of matching type.

The second example here is particularly interesting - 
it can be read as `int y = (x = x + 1)`. Assignment (and declaration) are perfectly valid expressions,
meaning that you can assign them to variables, use in instructions like binop etc.
They assign a value to a variable, and then return it

* Expression: convert

```
REPLang > tobool 3
True
REPLang > tobool 0
False
REPLang > tobool ""
False
REPLang > not tobool "a"
('not', True)
False
REPLang > tobool 3.1
True
REPLang > toint True
1
REPLang > tofloat False
0.0
REPLang > 4 + "you" 
<class 'TypeError'> Unsupported operand + between instances of <class 'int'> and <class 'str'>
REPLang > (tostr 4) + "you"
4you
REPLang > tofloat "1e-1"
0.1
REPLang > tofloat "1.42fa4"     
<class 'TypeError'> Cannot convert type <class 'str'> to type <class 'float'>
```
* Expression: sequence

Expressions can be joined by the ';' operator - 
each is evaluated, and the value of the last expression is returned.
If there is a syntax error in any of the expressions, REPLang will evaluate
all the expressions after the erroneous one.
```
REPLang > int x = 3; x + 4
('sequence', ('declare', <class 'int'>, 'x', 3), ('binop', ('name', 'x'), '+', 4))
7
REPLang > ind x = 3; 3 + 4
Syntax error at 'x'
LexToken(=,'=',1,6)
LexToken(NUMBER,3,1,8)
LexToken(;,';',1,9)
7
7
```
Sequences is also how you can write multiline programs in a file -
in that case, each line but the last one should end with semicolon

WARNING! Please take a look at the 'Dead code removal' 
section in Optimizations

* Expression: print

This expression prints, and then returns a given expression:
```
REPLang > print 3; 4
('sequence', ('print', 3), 4)
3
4
REPLang > 3; 4    
4
REPLang > bool printVar = print True
('declare', <class 'bool'>, 'printVar', ('print', True))
True
True
REPLang > printVar
('name', 'printVar')
True
```
We can see that print is a proper expression, and can be assigned to variables.
* Expression: block

Code can be organized to blocks using brackets. 
Each block has it's own scope, distinct from the global program scope:
```
REPLang > int x = 3; { int x = 4; { int y = x - 4} } 
('sequence', ('declare', <class 'int'>, 'x', 3), ('block', ('sequence', ('declare', <class 'int'>, 'x', 4), ('block', ('declare', <class 'int'>, 'y', ('binop', ('name', 'x'), '-', 4))))))
0
REPLang > x
('name', 'x')
3
REPLang > y
('name', 'y')
<class 'LookupError'> Name y undefined
REPLang > {x = 5; print x}; x
('sequence', ('block', ('sequence', ('assign', 'x', 5), ('print', ('name', 'x')))), ('name', 'x'))
5
3
```
We can see that it is possible to shadow name x with a different value and 
redeclare it (even with a different type). Everyting comes back to normal
after you exit the scope when you changed / redeclared a variable

* Expression: if

If lets you control the program flow and have conditional evaluation

```
REPLang > if 1 then 2 else 3
('if', 1, 2, 3)
<class 'TypeError'> Expected a boolean value for condition 1
REPLang > if tobool 1 then 2 else 3
('if', True, 2, 3)
2
REPLang > if True then if False then "not gonna happen" else "gonna happen"
('if', True, ('if', False, 'not gonna happen', 'gonna happen'), None)
gonna happen
REPLang > if False then 4
('if', False, 4, None)
None
```
If always returns a value - if condition is false, and no else branch is provided,
that value is None

* Expression: while

While is the one and only loop in REPLang - and also an expression!
If it doesn't get to run it returns None, else it returns the last value of its expression
```
REPLang > int x = 0; int whileValue = while x < 4 do print x = x + 1 end
('sequence', ('declare', <class 'int'>, 'x', 0), ('declare', <class 'int'>, 'whileValue', ('while', ('binop', ('name', 'x'), '<', 4), ('print', ('assign', 'x', ('binop', ('name', 'x'), '+', 1))))))
1
2
3
4
4
REPLang > whileValue
('name', 'whileValue')
4
REPLang > int tryToAssignNone = while whileValue < 4 do whileValue = 1 end        
('declare', <class 'int'>, 'tryToAssignNone', ('while', ('binop', ('name', 'whileValue'), '<', 4), ('assign', 'whileValue', 1)))
None
REPLang > tryToAssignNone
('name', 'tryToAssignNone')
None
``` 
* Statement: def (Function definition) and Expression: call

Last but not least, is our only not-expression in REPLang:
Function definition. It's closely tied to the call expression, which
 returns a function value, similarly to the name expression. 
 
 REPLang is pass-by-value - you cannot modifications done to arguments are only visible
 in the function scope. You can modify global variables from inside a function, 
 but this modification is only visible inside a function.
 
 Note that it's impossible in REPLang to have a void function (procedure)
 Let's see some examples
```
REPLang > def fun -> bool = True
['def', 'fun', [], '-', '>', <class 'bool'>, '=', True]

REPLang > fun()    
('call', 'fun', [])
True

REPLang > def add int x int y -> int = x + y
['def', 'add', [(<class 'int'>, 'x'), (<class 'int'>, 'y')], '-', '>', <class 'int'>, '=', ('binop', ('name', 'x'), '+', ('name', 'y'))]

REPLang > add(3, 4.5)
('call', 'add', [3, 4.5])
7

REPLang > def factorial int n -> int = if n < 2 then 1 else n * factorial(n - 1)
['def', 'factorial', [(<class 'int'>, 'n')], '-', '>', <class 'int'>, '=', ('if', ('binop', ('name', 'n'), '<', 2), 1, ('binop', ('name', 'n'), '*', ('call', 'factorial', [('binop', ('name', 'n'), '-', 1)])))]

REPLang > factorial(5)
('call', 'factorial', [5])
120

REPLang > add(factorial(factorial(3)), add(0, -100))
('call', 'add', [('call', 'factorial', [('call', 'factorial', [3])]), ('call', 'add', [0, -100])])
620

REPLang > fun(1)
('call', 'fun', [1])
[1] []
<class 'ValueError'> Expected 0 arguments for fun, got 1

REPLang > factorial("hello")
('call', 'factorial', ['hello'])
<class 'TypeError'> Argument 0 should be of type <class 'int'>, got <class 'str'>

```
A few main takeaways:
1. Functions are defined as: 'def' NAME type ARG1_NAME ... '->' type '=' expression
1. Functions are called using parenthesis, as in: NAME(expression, ...)
1. Arguments are automatically converted to desired type if possible (3.5 to 3 in the example)
1. Number and type of arguments is checked
1. Recursion and nested function calls are fully supported,
but it is not possible to declare a function inside a function

# Optimizations
REPLang is not heavily optimized, however some basic ones have been made:
* Compile time evaluation

All the operations on constants are evaluated at compile time:
```
REPLang > int x = 2
('declare', <class 'int'>, 'x', 2)
2
REPLang > -2^4 == -(2^4)
False
REPLang > -x^4 == -(x^4)
('binop', ('binop', ('uminus', ('name', 'x')), '^', 4), '==', ('uminus', ('binop', ('name', 'x'), '^', 4)))
False
```
The whole `-2^4 == -(2^4)` expression is simplified to `False` at compile time,
before the program even starts its execution.
* Mathematical identities
```
REPLang > x
('name', 'x')
2
REPLang > x + 0
('name', 'x')
2
REPLang > x * 1
('name', 'x')
2
REPLang > x * 2
('binop', ('name', 'x'), '+', ('name', 'x'))
4
```
Some operators are changed to 'cheaper' at compile time -
`2 * x` to `x + x`, and neutral elements (0 for addition, 1 for multiplication)
are discarded
* Dead code removal

Since REPLang is designed for REPL it never knows when a
variable or a function definition can be used, so it's tricky to
remove unused ones. One simple optimization that could be performed is 
discarding unused values in a sequence. It is done if the first expression in a sequence
has no side effects - that is, when it is one of:
1. 'binop'
 1. 'uminus'
  1. 'name'
   1. 'convert'
   1. 'call'
   1. Primitive value
```
REPLang > factorial(125245133426); 3 + 4
7
REPLang > (x = x ^ 13665125) + 1; x
('name', 'x')
2
REPLang > 
```
WARNING! The second example here actually has side effects -
in fact each of the 'discardable' expression types could have side effects,
since assignment and declaration can be used in place of any expression in REPLang.
However, taking advantage of that fact in these particular expressions is 
not recommended, and thus these types of expressions will be removed 

# Other included programs
Follow the steps from REPLang's getting started guide first

**rpn_calc.py**

It's a Reverse Polish Notation calculator, also written using PLY, 
supporting only
basic arithmetic operations (+, -, *, /, ^). It can be run via `python3 rpn_calc.py`
```
calc > 3 4 + 7 / 3 * 
3.0
calc > 4 .5 ^ 2. ^
4.0
```

**markdown_to_html_lex.py**

It's a PLY lexer, which reads HTML tokens from a file,
 and outputs markdown tokens to standard output. 
 It can be run as 
 
 ` python3 markdown_to_html_lex.py file.html > file.md`
 
 file.html and file.md are provided with this repository,
 so you can inspect the conversion results yourself.
 
 Supported html tags:
 * h1, h2
 * p
 * br
 * em
 * strong
 * code
 * hr
 * strike
 * ul, li, ol
 