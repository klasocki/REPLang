from typing import Union

tokens = [
    'EQ', 'NEQ', 'FLOAT', 'NUMBER', 'NAME', 'STRING'
]

literals = ['=', '+', '-', '*', '/', '(', ')', '^', '>', '<', ';']
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
    'true': 'TRUE',
    'false': 'FALSE',
    'tobool': '2BOOL',
    'tofloat': '2FLOAT',
    'toint': '2INT',
    'tostr': '2STR'
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
t_2STR = '->tostr'
t_2INT = '->toint'


def t_STRING(t):
    r'\"[^\"]*\"'
    t.value = t.value.lstrip('"').rstrip('"')
    return t


def t_FALSE(t):
    r'false'
    t.value = False
    return t


def t_TRUE(t):
    r'true'
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

# dictionary of names
values = {}
types = {}
str_to_type = {'int': int, 'float': float, 'str': str, 'bool': bool}


def p_statement_expr(p):
    'statement : expression'
    print(p[1])
    try:
        print(evaluate(p[1]))
    except Exception as e:
        print(type(e), e)


def p_convert(p):
    '''convert : 2INT
                | 2STR
                | 2FLOAT
                | 2BOOL'''
    p[0] = p[1]


def get_type(expr):
    if not type(expr) == tuple:
        return type(expr)
    else:
        return expr[1]


def p_expression_convert(p):
    'expression : convert expression'
    type_to_convert = str_to_type[p[1].lstrip('to')]
    p[0] = ('convert', type_to_convert, p[1], p[2])


def eval_convert(expr):
    val = evaluate(expr[3])
    to = expr[1]
    try:
        return to(val)
    except:
        raise TypeError(f'Cannot convert type {type(val)} to type {to}')


def p_expression_assign(p):
    'expression : NAME "=" expression'
    p[0] = ('assign', get_type(p[3]), p[1], p[3])


def eval_assign(expression):
    _, expr_type, name, val_expr = expression
    if name not in types.keys():
        raise LookupError(f"{name} undeclared")
    if types[name] != expr_type:
        raise TypeError(f"Expected type {types[name]} for {name}, got {expr_type}")
    val = evaluate(val_expr)
    values[name] = val
    return val


def p_type(p):
    '''type : STRING_TYPE
    | INT_TYPE
    | FLOAT_TYPE
    | BOOL_TYPE'''
    p[0] = p[1]


def p_expression_declare(p):
    'expression : type NAME "=" expression'
    p[0] = ('declare', str_to_type[p[1]], p[1], p[2], p[4])


def eval_declare(expr):
    _, type_class, _, name, val = expr
    if name in types.keys():
        raise RuntimeError(f"{name} already declared")
    if get_type(val) != type_class:
        raise TypeError(f"Expected type {type_class} for {name}, got {get_type(val)}")
    val = evaluate(val)
    types[name] = type_class
    values[name] = val
    return val


def p_error_expression(p):
    "expression : error ';' expression"
    p[0] = p[3]


def p_expression_semicolon(p):
    "expression : expression ';' expression"
    p[0] = ('sequence', get_type(p[3]), p[1], p[3])


def eval_sequence(expression):
    evaluate(expression[2])
    return evaluate(expression[3])


def p_expression_if(p):
    """expression : IF expression THEN expression else_expression"""
    if_type = type(None)
    if get_type(p[2]) == get_type(p[3]):
        if_type = get_type(p[2])
    elif are_numbers(get_type(p[2]), get_type(p[3])):
        if_type = float
    p[0] = ('if', if_type, p[2], p[4], p[5])


def eval_if(expr):
    _, _, condition, true_branch, false_branch = expr
    if get_type(condition) != bool:
        raise TypeError(f"Expected a boolean value for condition {condition}")
    if evaluate(condition):
        return evaluate(true_branch)
    else:
        return evaluate(false_branch)


def p_else_expression(p):
    """else_expression : ELSE expression
                        | empty"""
    p[0] = p[2] if len(p) > 2 else None


def p_expression_while(p):
    """expression : WHILE expression DO expression END"""
    # p[2] = bool(p[2])
    # while p[2]:
    #     p[0] = p[4]
    #     p[2] = bool(p[2])
    p[0] = ('while', get_type(p[4]), p[2], p[4])


def eval_while(expr):
    _, _, condition, body = expr
    if get_type(condition) != bool:
        raise TypeError(f"Expected a boolean value for condition {condition}")
    result = None
    while evaluate(condition):
        result = evaluate(body)
    return result


def p_expression_binop(p):
    '''expression : expression '+' expression
                  | expression '-' expression
                  | expression '*' expression
                  | expression '/' expression
                  | expression '^' expression
                  | expression EQ expression
                  | expression '>' expression
                  | expression '<' expression
                  | expression NEQ expression'''
    p[0] = ('binop', get_binop_type(p[1], p[3], p[2]), p[1], p[2], p[3])


def get_binop_type(val1, val2, op):
    if op in ['>', '<', '==', '!=']:
        return bool
    if op == '/' or (not get_type(val1) == get_type(val2) and op in ['-', '^']):
        return float
    if get_type(val1) == get_type(val2):
        return get_type(val1)
    if op == '*' and get_type(val1) in [str, int] and get_type(val2) in [str, int]:
        return str
    if op in ['+', '*'] and are_numbers(get_type(val1), get_type(val2)):
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
                type1 == int and type2 == str) or (type2 == int and type1 == int)
    elif op in ['>', '<']:
        assert are_numbers(type1, type2) or type1 == type2


def eval_binop(expr):
    _, _, val1, op, val2 = expr
    try:
        typecheck_binop(get_type(val1), get_type(val2), op)
    except AssertionError:
        raise TypeError(f"Unsupported operand {op} between instances of"
                        f"{get_type(val1)} and {get_type(val2)}")
    
    val1, val2 = evaluate(val1), evaluate(val2)
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
    p[0] = ('uminus', get_type(p[2]), p[2])


def eval_uminus(expr):
    if not are_numbers(expr[1]):
        raise TypeError(f"You can only negate numbers, got type {expr[1]}")
    return -evaluate(expr[1])


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
    p[0] = ('name', types[p[1]] if p[1] in types else type(None), p[1])


def eval_name(expr):
    try:
        return values[expr[2]]
    except LookupError:
        print("Undefined name '%s'" % expr[2])
        return None


eval_fun = {'assign': eval_assign, 'binop': eval_binop, 'uminus': eval_uminus, 'while': eval_while, 'if': eval_if,
            'sequence': eval_sequence, 'name': eval_name, 'declare': eval_declare, 'convert': eval_convert}


def evaluate(expression: Union[tuple, float, int]):
    if type(expression) == tuple:
        return eval_fun[expression[0]](expression)
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
    yacc.parse(s)
