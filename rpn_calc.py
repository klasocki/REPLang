tokens = (
    'NAME', 'FLOAT', 'NUMBER', 'EQ', 'NEQ'
)

literals = ['=', '+', '-', '*', '/', '(', ')', '^', '>', '<', ';']

# Tokens

t_NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
t_EQ = r'=='
t_NEQ = r'!='


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
    ('left', '+', '-'),
    ('left', '*', '/'),
    ('right', '^'),
    ('right', 'UMINUS'),
)

# dictionary of names
names = {}


def p_statement_assign(p):
    'statement : NAME "=" expression'
    names[p[1]] = p[3]

def p_error_expression(p):
    "expression : error ';' expression"
    p[0] = p[3]

def p_expression_semicolon(p):
    "expression : expression ';' expression"
    if type(p[3]) == list:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1], p[3]]


def p_statement_expr(p):
    'statement : expression'
    print(p[1])


def p_expression_binop(p):
    '''expression : expression expression '+'
                  | expression expression '-'
                  | expression expression '*'
                  | expression expression '/'
                  | expression expression '^'
                  | expression expression EQ
                  | expression expression '>'
                  | expression expression '<'
                  | expression expression NEQ'''
    if p[3] == '+':
        p[0] = p[1] + p[2]
    elif p[3] == '-':
        p[0] = p[1] - p[2]
    elif p[3] == '*':
        p[0] = p[1] * p[2]
    elif p[3] == '/':
        p[0] = p[1] / p[2]
    elif p[3] == '^':
        p[0] = p[1] ** p[2]
    elif p[3] == '^':
        p[0] = p[1] ** p[2]
    elif p[3] == '==':
        p[0] = p[1] == p[2]
    elif p[3] == '!=':
        p[0] = p[1] != p[2]
    elif p[3] == '>':
        p[0] = p[1] > p[2]
    elif p[3] == '<':
        p[0] = p[1] < p[2]


def p_expression_uminus(p):
    "expression : '-' expression %prec UMINUS"
    p[0] = -p[2]


def p_expression_group(p):
    "expression : '(' expression ')'"
    p[0] = p[2]


def p_expression_number(p):
    """expression : NUMBER
                    | FLOAT"""
    p[0] = p[1]


def p_expression_name(p):
    "expression : NAME"
    try:
        p[0] = names[p[1]]
    except LookupError:
        print("Undefined name '%s'" % p[1])
        p[0] = 0


def p_error(p):
    if p:
        print("Syntax error at '%s'" % p.value)
    else:
        print("Syntax error at EOF")


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
