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
    ('left', 'EQ', 'NEQ', '>', '<'),
    ('left', '='),
    ('right', '2INT', '2FLOAT', '2STR', '2BOOL'),
    ('left', '+', '-'),
    ('left', '*', '/'),
    ('right', '^'),
    ('right', 'UMINUS'),
)


class Block:
    def __init__(self, parent=None):
        self.parent = parent
        self.types = {}
        self.values = {}

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
        if name not in self.types:
            raise LookupError(f"Name {name} undefined")
        if get_type(expr, self) != self.types[name]:
            raise TypeError(f"Expected type {self.types[name]} for {name}, got {get_type(expr, self)}")
        self.values[name] = evaluate(expr, self)
        return self.values[name]


# dictionary of functions
global_block = Block()
functions = {}
function_types = {}
arguments = {}
function_blocks = {}

str_to_type = {'int': int, 'float': float, 'str': str, 'bool': bool}


def p_statement_expr(p):
    'statement : expression'
    print(p[1])
    try:
        print(evaluate(p[1], global_block))
    except Exception as e:
        print(type(e), e)


def p_convert(p):
    '''convert : 2INT
                | 2STR
                | 2FLOAT
                | 2BOOL'''
    p[0] = p[1]


def get_type(expr, block):
    if not type(expr) == tuple:
        return type(expr)
    elif expr[0] == 'call':
        return function_types[expr[1]]
    elif expr[0] == 'name':
        return block.get_type(expr[1])
    elif expr[0] == 'binop':
        return get_binop_type(expr[2], expr[4], expr[3], block)
    else:
        return expr[1]


def p_expression_convert(p):
    'expression : convert expression'
    type_to_convert = str_to_type[p[1].lstrip('to')]
    p[0] = ('convert', type_to_convert, p[1], p[2])


def eval_convert(expr, block):
    val = evaluate(expr[3], block)
    to = expr[1]
    try:
        return to(val)
    except ValueError:
        raise TypeError(f'Cannot convert type {type(val)} to type {to}')


def p_expression_assign(p):
    'expression : NAME "=" expression'
    p[0] = ('assign', None, p[1], p[3])


def eval_assign(expression, block):
    _, _, name, val_expr = expression
    expr_type = get_type(val_expr, block)
    if block.get_type(name) != expr_type:
        raise TypeError(f"Expected type {block.get_type(name)} for {name}, got {expr_type}")
    return block.assign(name=name, expr=val_expr)


def p_type(p):
    '''type : STRING_TYPE
    | INT_TYPE
    | FLOAT_TYPE
    | BOOL_TYPE'''
    p[0] = str_to_type[p[1]]


def p_expression_declare(p):
    'expression : type NAME "=" expression'
    p[0] = ('declare', p[1], p[2], p[4])


def eval_declare(expr, block: Block):
    _, type_class, name, val = expr
    if get_type(val, block) != type_class:
        raise TypeError(f"Expected type {type_class} for {name}, got {get_type(val, block)}")
    return block.declare(name=name, type_class=type_class, expr=val)


def p_statement_def(p):
    """statement : DEF NAME args '-' '>' type '=' expression"""
    if p[2] in functions.keys():
        raise NameError(f"Function {p[1]} already exists")
    function_types[p[2]] = p[6]
    arguments[p[2]] = []
    function_block = Block(parent=global_block)
    function_blocks[p[2]] = function_block
    for arg_type, name in p[3]:
        arguments[p[2]].append(name)
        function_block.declare(name, arg_type, None)

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
    if len(p) == 2 and not p[1]:
        p[0] = []
    elif len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]


def eval_call(expr, block: Block):
    _, fun, args = expr
    if fun not in functions.keys():
        raise NameError(f"Function {fun} undefined")
    if len(args) != len(arguments[fun]):
        print(args, arguments[fun])
        raise ValueError(f"Expected {len(arguments[fun])} arguments for {fun}, got "
                         f"{len(args)}")
    for i, (arg, expected) in enumerate(zip(args, arguments[fun])):
        arg_type = function_blocks[fun].get_type(expected)
        if get_type(arg, block) != arg_type:
            raise TypeError(f"Argument {i} should be of type {arg_type}, got {get_type(arg, block)}")

    for name, value in zip(arguments[fun], args):
        function_blocks[fun].assign(name=name, expr=value)
    return evaluate(functions[fun], function_blocks[fun])


def p_error_expression(p):
    "expression : error ';' expression"
    p[0] = p[3]


def p_expression_semicolon(p):
    "expression : expression ';' expression"
    p[0] = ('sequence', None, p[1], p[3])


def eval_sequence(expression, block):
    evaluate(expression[2], block)
    return evaluate(expression[3], block)


def p_expression_block(p):
    """expression : '{' expression '}'"""
    p[0] = ('block', None, p[2])


def eval_block(expr, block):
    new_block = Block(parent=block)
    return evaluate(expr[2], new_block)


def p_expression_if(p):
    """expression : IF expression THEN expression else_expression"""
    p[0] = ('if', None, p[2], p[4], p[5])


def eval_if(expr, block: Block):
    _, _, condition, true_branch, false_branch = expr
    if_block = Block(parent=block)
    if get_type(condition, if_block) != bool:
        raise TypeError(f"Expected a boolean value for condition {condition}")
    if evaluate(condition, if_block):
        return evaluate(true_branch, if_block)
    else:
        return evaluate(false_branch, if_block)


def p_else_expression(p):
    """else_expression : ELSE expression
                        | empty"""
    p[0] = p[2] if len(p) > 2 else None


def p_expression_while(p):
    """expression : WHILE expression DO expression END"""
    p[0] = ('while', None, p[2], p[4])


def eval_while(expr, block):
    _, _, condition, body = expr
    if get_type(condition, block) != bool:
        raise TypeError(f"Expected a boolean value for condition {condition}")
    result = None
    while_block = Block(parent=block)
    while evaluate(condition, while_block):
        result = evaluate(body, while_block)
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
    p[0] = ('binop', None, p[1], p[2], p[3])


def get_binop_type(val1, val2, op, block):
    if op in ['>', '<', '==', '!=']:
        return bool
    if op == '/' or (not get_type(val1, block) == get_type(val2, block) and op in ['-', '^']):
        return float
    if get_type(val1, block) == get_type(val2, block):
        return get_type(val1, block)
    if op == '*' and get_type(val1, block) in [str, int] and get_type(val2, block) in [str, int]:
        return str
    if op in ['+', '*'] and are_numbers(get_type(val1, block), get_type(val2, block)):
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


def eval_binop(expr, block: Block):
    _, _, val1, op, val2 = expr
    try:
        typecheck_binop(get_type(val1, block), get_type(val2, block), op)
    except AssertionError:
        raise TypeError(f"Unsupported operand {op} between instances of "
                        f"{get_type(val1, block)} and {get_type(val2, block)}")

    val1, val2 = evaluate(val1, block), evaluate(val2, block)
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
    p[0] = ('uminus', None, p[2])


def eval_uminus(expr, block: Block):
    if not are_numbers(expr[1]):
        raise TypeError(f"You can only negate numbers, got type {expr[1]}")
    return -evaluate(expr[2], block)


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


def eval_name(expr, block):
    _, name = expr
    return block.get_value(name)


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
}


def evaluate(expression: Union[tuple, float, int], block: Block):
    if type(expression) == tuple:
        return eval_fun[expression[0]](expression, block)
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
