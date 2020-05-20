import ply.lex as lex
import sys

tokens = (
    'LH1',
    'RH1',
    'TEXT',
    'PAR',
    'LH2',
    'RH2',
    'STRIKE',
    'STRONG',
    'EM',
    'HR',
    'CODE',
    'BR',
    'LOL',
    'RLIST',
    'LUL',
    'LLI',
    'RLI',
)
states = (
    ('ol', 'inclusive'),
    ('ul', 'inclusive'),
)
t_ignore = ' \t'

t_TEXT = r'[^\"\'<>]+'


def t_LOL(t):
    r'<ol>'
    t.lexer.begin('ol')
    t.value = '\n'
    return t


def t_RLIST(t):
    r'<\/(o|u)l>'
    t.lexer.begin('INITIAL')
    t.value = '\n'
    return t


def t_LUL(t):
    r'<ul>'
    t.lexer.begin('ul')
    t.value = '\n'
    return t


def t_ol_LLI(t):
    r'<li>'
    t.value = '1. '
    return t


def t_ul_LLI(t):
    r'<li>'
    t.value = '* '
    return t


def t_ANY_RLI(t):
    r'<\/li>'
    t.value = '\n'
    return t


def t_PAR(t):
    r'<\/?p>'
    t.value = '\n\n'
    return t


def t_LH2(t):
    r'<h2>'
    t.value = '\n'
    return t


def t_RH2(t):
    r'<\/h2>'
    t.value = '\n-----------'
    return t


def t_LH1(t):
    r'<h1>'
    t.value = '# '
    return t


def t_RH1(t):
    r'<\/h1>'
    t.value = '\n'
    return t


def t_EM(t):
    r'<\/?em>'
    t.value = '_'
    return t


def t_STRONG(t):
    r'<\/?strong>'
    t.value = '**'
    return t


def t_CODE(t):
    r'<\/?code>'
    t.value = '`'
    return t


def t_STRIKE(t):
    r'<\/?strike>'
    t.value = '~~'
    return t


def t_HR(t):
    r'<hr\/>'
    t.value = '---'
    return t


def t_BR(t):
    r'<br/>'
    t.value = '  \n'
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_error(t):
    print("line %d: illegal character '%s'" % (t.lineno, t.value[0]))
    t.lexer.skip(1)


lexer = lex.lex()
fh = None
try:
    fh = open(sys.argv[1] if len(sys.argv) > 1 else "file.html", "r")
    lexer.input(fh.read())
    print(''.join([token.value for token in lexer]))
    # for token in lexer:
    # print("line %d: %s(%s)" % (token.lineno, token.type, token.value))
except:
    print("open error\n")
