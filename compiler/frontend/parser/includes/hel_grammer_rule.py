# hel_grammer_rule.py (La cusboonaysiiyay)

import sys
from compiler.frontend.parser.ast_nodes import HelNode

def p_hel_statement(p):
    '''hel : HEL LPAREN IDENTIFIER RPAREN SEMICOLON'''
    line = p.lineno(1)
    filename = p.lexer.filename
    var_name = p[3]
    p[0] = HelNode(line, var_name, filename)