# keyd_grammar_rule.py (Corrected - Based on Your Original)

from compiler.frontend.parser.ast_nodes import KeydNode, AssignmentNode
import sys

# This 'p_declaration' rule is your original one and remains unchanged.
def p_declaration(p):
    '''declaration : KEYD COLON type_specifier IDENTIFIER SEMICOLON
                   | KEYD COLON type_specifier IDENTIFIER EQUALS expression SEMICOLON
    '''
    line = p.lineno(1)
    filename = p.lexer.filename
    var_type = p[3]
    var_name = p[4]

    if len(p) == 6:
        p[0] = KeydNode(var_name, var_type, None, line, filename)
    elif len(p) == 8:
        p[0] = KeydNode(var_name, var_type, p[6], line, filename)
