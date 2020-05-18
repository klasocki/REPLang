from typing import Union

tokens = [
    'EQ', 'NEQ', 'FLOAT', 'NUMBER', 'NAME', 'STRING'
]

literals = ['=', '+', '-', '*', '/', '(', ')', '^', '>', '<', ';', ',', '{', '}']
reserved = {
    'while': 'WHILE',
    'then': 'THEN',
    'if': 'IF',
    'else': 'ELSE',
    'do': 'DO',
    'end': 'END',
    'int': 'INT_TYPE',
    'float': 'FLOAT_TYPE',
    'str': 'STRING_TYPE',
    'bool': 'BOOL_TYPE',
    'True': 'TRUE',
    'False': 'FALSE',
    'tobool': '2BOOL',
    'tofloat': '2FLOAT',
    'toint': '2INT',
    'tostr': '2STR',
    'def': 'DEF',
    'not': 'NOT',
    'print': 'PRINT',
}
tokens += reserved.values()

# Tokens
t_EQ = r'=='
t_NEQ = r'!='
t_BOOL_TYPE = 'bool'
t_INT_TYPE = 'int'
t_FLOAT_TYPE = 'float'
t_STRING_TYPE = 'str'
t_2BOOL = 'tobool'
t_2FLOAT = 'tofloat'
t_2STR = 'tostr'
t_2INT = 'toint'
t_DEF = 'def'
t_NOT = 'not'
t_PRINT = 'print'


def t_STRING(t):
    r'\"[^\"]*\"'
    t.value = t.value.lstrip('"').rstrip('"')
    return t


def t_FALSE(t):
    r'False'
    t.value = False
    return t


def t_TRUE(t):
    r'True'
    t.value = True
    return t


def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    if t.value in reserved:
        t.type = reserved[t.value]
    return t


def t_FLOAT(t):
    r'(\d+\.\d*)|(\.\d+)'
    t.value = float(t.value)
    return t


def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t


t_ignore = " \t"


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


# Build the lexer
import ply.lex as lex

lexer = lex.lex()

# Parsing rules

precedence = (
    ('left', 'IF', 'ELSE', 'THEN', 'WHILE'),
    ('left', ';'),
    ('left', 'PRINT'),
    ('left', 'EQ', 'NEQ', '>', '<'),
    ('left', 'NOT'),
    ('left', '='),
    ('right', '2INT', '2FLOAT', '2STR', '2BOOL'),
    ('left', '+', '-'),
    ('left', '*', '/'),
    ('right', '^'),
    ('right', 'UMINUS'),
)


class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.types = {}
        self.values = {}

    def is_name_declared(self, name: str):
        return name in self.types or (self.parent and self.parent.is_name_declared(name))

    def get_type(self, name: str):
        if name in self.types:
            return self.types[name]
        if self.parent:
            return self.parent.get_type(name)
        raise LookupError(f"Name {name} undefined")

    def get_value(self, name: str):
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get_value(name)
        raise LookupError(f"Name {name} undefined")

    def declare(self, name: str, type_class: type, expr: tuple):
        if name in self.types:
            raise RuntimeError(f"{name} already declared")
        self.types[name] = type_class
        self.values[name] = evaluate(expr, self)
        return self.values[name]

    def assign(self, name: str, expr: tuple):
        if not self.is_name_declared(name):
            raise LookupError(f"Name {name} undefined")
        if get_type(expr, self) != self.get_type(name):
            raise TypeError(f"Expected type {self.get_type(name)} for {name}, got {get_type(expr, self)}")
        self.values[name] = evaluate(expr, self)
        return self.values[name]


# storage for variables and functions
global_scope = Scope()
functions = {}
function_types = {}
arguments = {}
function_scopes = {}

str_to_type = {'int': int, 'float': float, 'str': str, 'bool': bool}

RUNNING_REPL = True


def p_statement_expr(p):
    'statement : expression'
    print(p[1])
    print(evaluate(p[1], global_scope))


def p_convert(p):
    '''convert : 2INT
                | 2STR
                | 2FLOAT
                | 2BOOL'''
    p[0] = p[1]


def get_type(expr, scope):
    if not type(expr) == tuple:
        return type(expr)
    elif expr[0] == 'call':
        return function_types[expr[1]]
    elif expr[0] == 'name':
        return scope.get_type(expr[1])
    elif expr[0] == 'binop':
        return get_binop_type(expr[1], expr[3], expr[2], scope)
    elif expr[0] == 'assign':
        return get_type(expr[2], scope)
    elif expr[0] == 'sequence':
        return get_type(expr[2], scope)
    elif expr[0] == 'block':
        return get_type(expr[1], scope)
    elif expr[0] == 'if':
        return get_if_type(expr, scope)
    elif expr[0] == 'while':
        return get_type(expr[2], scope)
    elif expr[0] == 'uminus':
        return get_type(expr[1], scope)
    else:
        return expr[1]


def p_expression_convert(p):
    'expression : convert expression'
    type_to_convert = str_to_type[p[1].lstrip('to')]
    p[0] = ('convert', type_to_convert, p[1], p[2])


def eval_convert(expr, scope):
    val = evaluate(expr[3], scope)
    to = expr[1]
    try:
        return to(val)
    except ValueError:
        raise TypeError(f'Cannot convert type {type(val)} to type {to}')


def p_expression_not(p):
    "expression : NOT expression"
    p[0] = ('not', p[2])


def eval_not(expr, scope):
    return not bool(evaluate(expr[1], scope))


def p_expression_print(p):
    "expression : PRINT expression"
    p[0] = ('print', p[2])


def eval_print(expr, scope):
    val = evaluate(expr[1], scope)
    print(val)
    return val


def p_expression_assign(p):
    'expression : NAME "=" expression'
    p[0] = ('assign', p[1], p[3])


def eval_assign(expression, scope):
    _, name, val_expr = expression
    expr_type = get_type(val_expr, scope)
    if scope.get_type(name) != expr_type:
        raise TypeError(f"Expected type {scope.get_type(name)} for {name}, got {expr_type}")
    return scope.assign(name=name, expr=val_expr)


def p_type(p):
    '''type : STRING_TYPE
    | INT_TYPE
    | FLOAT_TYPE
    | BOOL_TYPE'''
    p[0] = str_to_type[p[1]]


def p_expression_declare(p):
    'expression : type NAME "=" expression'
    p[0] = ('declare', p[1], p[2], p[4])


def eval_declare(expr, scope: Scope):
    _, type_class, name, val = expr
    if get_type(val, scope) != type_class:
        raise TypeError(f"Expected type {type_class} for {name}, got {get_type(val, scope)}")
    return scope.declare(name=name, type_class=type_class, expr=val)


def p_statement_def(p):
    """statement : DEF NAME args '-' '>' type '=' expression"""
    print(p[8])
    if p[2] in functions.keys():
        raise NameError(f"Function {p[1]} already exists")
    function_types[p[2]] = p[6]
    arguments[p[2]] = []
    function_scope = Scope(parent=global_scope)
    function_scopes[p[2]] = function_scope
    for arg_type, name in p[3]:
        arguments[p[2]].append(name)
        function_scope.declare(name, arg_type, None)

    functions[p[2]] = p[8]


def p_args(p):
    """args : empty
            | type NAME args"""
    if len(p) <= 2:
        p[0] = []
    else:
        p[0] = [(p[1], p[2])] + p[3]


def p_expression_call(p):
    """expression : NAME '(' call_args ')'"""
    p[0] = ('call', p[1], p[3])


def p_call_args(p):
    """call_args : empty
                | expression
                | expression ',' call_args"""
    if len(p) == 2 and p[1] is None:
        p[0] = []
    elif len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]


def eval_call(expr, scope: Scope):
    _, fun, args = expr
    if fun not in functions.keys():
        raise NameError(f"Function {fun} undefined")
    if len(args) != len(arguments[fun]):
        print(args, arguments[fun])
        raise ValueError(f"Expected {len(arguments[fun])} arguments for {fun}, got "
                         f"{len(args)}")
    parent_scope = function_scopes[fun] if scope == global_scope else scope
    new_scope = Scope(parent=parent_scope)
    arg_values = [arg for arg in args]
    for i, (arg, expected) in enumerate(zip(args, arguments[fun])):
        arg_type = function_scopes[fun].get_type(expected)
        arg_values[i] = evaluate(arg, new_scope)
        if type(arg_values[i]) != arg_type:
            try:
                arg_values[i] = arg_type(arg_values[i])
            except (TypeError, ValueError):
                raise TypeError(f"Argument {i} should be of type {arg_type}, got {type(arg_values[i])}")

    for name, value in zip(arguments[fun], arg_values):
        if new_scope.is_name_declared(name):
            new_scope.assign(name=name, expr=value)
        else:
            new_scope.declare(name, type(value), value)
    return evaluate(functions[fun], new_scope)


def p_error_expression(p):
    "expression : error ';' expression"
    p[0] = p[3]


def p_expression_semicolon(p):
    "expression : expression ';' expression"
    first_expr = p[1]
    no_side_effect_constructs = ['binop', 'uminus', 'name', 'convert']
    if type(first_expr) != tuple or first_expr[0] in no_side_effect_constructs:
        p[0] = p[3]
    else:
        p[0] = ('sequence', p[1], p[3])


def eval_sequence(expression, scope):
    evaluate(expression[1], scope)
    return evaluate(expression[2], scope)


def p_expression_block(p):
    """expression : '{' expression '}'"""
    p[0] = ('block', p[2])


def eval_block(expr, scope):
    new_scope = Scope(parent=scope)
    return evaluate(expr[1], new_scope)


def p_expression_if(p):
    """expression : IF expression THEN expression else_expression"""
    p[0] = ('if', p[2], p[4], p[5])


def get_if_type(expr, scope):
    _, _, true_branch, false_branch = expr
    true_type = get_type(true_branch, scope)
    false_type = get_type(false_branch, scope)
    if true_type == false_type:
        return true_type
    elif are_numbers(true_type, false_type):
        return float
    else:
        return None


def eval_if(expr, scope: Scope):
    _, condition, true_branch, false_branch = expr
    if_scope = Scope(parent=scope)
    if get_type(condition, if_scope) != bool:
        raise TypeError(f"Expected a boolean value for condition {condition}")
    if evaluate(condition, if_scope):
        return evaluate(true_branch, if_scope)
    else:
        return evaluate(false_branch, if_scope)


def p_else_expression(p):
    """else_expression : ELSE expression
                        | empty"""
    p[0] = p[2] if len(p) > 2 else None


def p_expression_while(p):
    """expression : WHILE expression DO expression END"""
    p[0] = ('while', p[2], p[4])


def eval_while(expr, scope):
    _, condition, body = expr
    if get_type(condition, scope) != bool:
        raise TypeError(f"Expected a boolean value for condition {condition}")
    result = None
    while_scope = Scope(parent=scope)
    while evaluate(condition, while_scope):
        result = evaluate(body, while_scope)
    return result


def p_expression_binop(p):
    """expression : expression '+' expression
                  | expression '-' expression
                  | expression '*' expression
                  | expression '/' expression
                  | expression '^' expression
                  | expression EQ expression
                  | expression '>' expression
                  | expression '<' expression
                  | expression NEQ expression"""
    val1, op, val2 = p[1:]
    if (val1 == 0 and op == '+') or (val1 == 1 and op == '*'):
        p[0] = val2
    elif (val2 == 0 and op in ['+', '-']) or (val2 == 1 and op in ['*', '/']):
        p[0] = val1
    elif val1 == 2 and op == '*':
        p[0] = ('binop', val2, '+', val2)
    elif val2 == 2 and op == '*':
        p[0] = ('binop', val1, '+', val1)
    else:
        p[0] = ('binop', val1, op, val2)


def get_binop_type(val1, val2, op, scope):
    if op in ['>', '<', '==', '!=']:
        return bool
    if op == '/' or (not get_type(val1, scope) == get_type(val2, scope) and op in ['-', '^']):
        return float
    if get_type(val1, scope) == get_type(val2, scope):
        return get_type(val1, scope)
    if op == '*' and get_type(val1, scope) in [str, int] and get_type(val2, scope) in [str, int]:
        return str
    if op in ['+', '*'] and are_numbers(get_type(val1, scope), get_type(val2, scope)):
        return float


def are_numbers(val1, val2=int):
    return (type(val1) in [float, int] and type(val2) in [float, int]) or \
           (val1 in [float, int] and val2 in [float, int])


def typecheck_binop(type1, type2, op):
    if op in ['-', '/', '^']:
        assert are_numbers(type1, type2)
    elif op == '+':
        assert are_numbers(type1, type2) or type1 == type2 == str
    elif op == '*':
        assert are_numbers(type1, type2) or (
                type1 == int and type2 == str) or (type2 == int and type1 == str)
    elif op in ['>', '<']:
        assert are_numbers(type1, type2) or type1 == type2


def eval_binop(expr, scope: Scope):
    _, val1, op, val2 = expr
    try:
        typecheck_binop(get_type(val1, scope), get_type(val2, scope), op)
    except AssertionError:
        raise TypeError(f"Unsupported operand {op} between instances of "
                        f"{get_type(val1, scope)} and {get_type(val2, scope)}")

    val1, val2 = evaluate(val1, scope), evaluate(val2, scope)
    if op == '+':
        return val1 + val2
    elif op == '-':
        return val1 - val2
    elif op == '*':
        return val1 * val2
    elif op == '/':
        return val1 / val2
    elif op == '^':
        return val1 ** val2
    elif op == '==':
        return val1 == val2
    elif op == '!=':
        return val1 != val2
    elif op == '>':
        return val1 > val2
    elif op == '<':
        return val1 < val2


def p_expression_uminus(p):
    "expression : '-' expression %prec UMINUS"
    p[0] = ('uminus', p[2])


def eval_uminus(expr, scope: Scope):
    val_type = get_type(expr[1], scope)
    if not are_numbers(val_type):
        raise TypeError(f"You can only negate numbers, got type {val_type}")
    return -evaluate(expr[1], scope)


def p_expression_group(p):
    "expression : '(' expression ')'"
    p[0] = p[2]


def p_expression_value(p):
    """expression : NUMBER
                    | FLOAT
                    | STRING
                    | TRUE
                    | FALSE"""
    p[0] = p[1]


def p_expression_name(p):
    "expression : NAME"
    p[0] = ('name', p[1])


def eval_name(expr, scope):
    _, name = expr
    return scope.get_value(name)


eval_fun = {
    'assign': eval_assign,
    'binop': eval_binop,
    'uminus': eval_uminus,
    'while': eval_while,
    'if': eval_if,
    'sequence': eval_sequence,
    'name': eval_name,
    'convert': eval_convert,
    'call': eval_call,
    'declare': eval_declare,
    'block': eval_block,
    'print': eval_print,
    'not': eval_not,
}


def evaluate(expression: Union[tuple, float, int], scope: Scope):
    if type(expression) == tuple:
        return eval_fun[expression[0]](expression, scope)
    else:
        return expression


def p_error(p):
    if p:
        print("Syntax error at '%s'" % p.value)
        # Read ahead looking for a terminating ";"
        while True:
            tok = p.lexer.token()
            print(tok)
            if not tok or tok.type == ';':
                break
        parser.restart()

        # Return ; to the parser as the next lookahead token
        return tok
    else:
        print("Syntax error at EOF")
        parser.restart()


def p_empty(p):
    'empty :'
    p[0] = None


import ply.yacc as yacc

parser = yacc.yacc()

while True:
    try:
        s = input('calc > ')
    except (EOFError, KeyboardInterrupt):
        break
    if not s:
        continue
    try:
        yacc.parse(s)
    except Exception as e:
        print(type(e), e)
