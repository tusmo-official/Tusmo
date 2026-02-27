# array_grammer_rule.py 

from compiler.frontend.parser.ast_nodes import (
    ArrayTypeNode, ArrayAssignmentNode, ArrayAccessNode, ArrayInitializationNode, ArrayTypeQueryNode, IdentifierNode
)

def p_type_specifier(p):
    '''type_specifier : primitive_type
                      | array_type'''
    
    p[0] = p[1]



def p_array_type(p):
    '''array_type : TIX COLON type_specifier
                  | TIX'''
    line = p.lineno(1)
    filename = p.lexer.filename  # Hel magaca faylka


    if len(p) == 4:
        # Now p[3] can be a primitive type (like 'tiro') OR another ArrayTypeNode
        p[0] = ArrayTypeNode(line, element_type=p[3], filename=filename) # Homogeneous
    else:
        p[0] = ArrayTypeNode(line, element_type=None, filename=filename) # Heterogeneous

def p_array_initialization(p):
    '''array_initialization : LBRACKET argument_list_opt RBRACKET'''

    line = p.lineno(1)
    filename = p.lexer.filename  # Hel magaca faylka

    p[0] = ArrayInitializationNode(line, p[2], filename)


def p_argument_list_opt(p):
    '''argument_list_opt : argument_list
                         | empty'''
    if p[1] is None:
        p[0] = []  # Haddii uu madhan yahay, soo celi liis madhan
    else:
        p[0] = p[1]



def p_array_access(p):
    '''array_access : expression LBRACKET expression RBRACKET'''
    line = p.lineno(2)
    filename = p.lexer.filename  # Hel magaca faylka


    p[0] = ArrayAccessNode(line, p[1], p[3], filename)

# Simpler array access for identifier[index] to reduce ambiguity
def p_array_access_simple(p):
    '''expression : IDENTIFIER LBRACKET expression RBRACKET'''
    line = p.lineno(2)
    filename = p.lexer.filename
    p[0] = ArrayAccessNode(line, IdentifierNode(p[1], line=line, filename=filename), p[3], filename)

def p_array_type_query(p):
    'array_type_query : IDENTIFIER LBRACKET RBRACKET'
    line = p.lineno(2)
    filename = p.lexer.filename
    p[0] = ArrayTypeQueryNode(line, p[1], filename)
