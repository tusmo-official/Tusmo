# compiler/frontend/parser/includes/shared_grammar.py

# This file contains grammar rules that are shared across different parts of the parser.

def p_argument_list(p):
    '''argument_list : argument_list COMMA expression
                     | expression'''
    if len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    else:
        p[0] = [p[1]]

def p_argument_list_opt(p):
    '''argument_list_opt : argument_list
                         | empty'''
    p[0] = p[1] if p[1] else []