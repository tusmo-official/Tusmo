# condition_grammar_rule.py (La cusboonaysiiyay)

from compiler.frontend.parser.ast_nodes import IfNode

def p_condition_statement(p):
    '''
    condition_statement : if_clause optional_elifs optional_else
    '''
    line = p.lineno(1)
    filename = p.lexer.filename
    all_cases = p[1] + p[2]
    p[0] = IfNode(all_cases, p[3], line, filename)

def p_if_clause(p):
    '''if_clause : HADDII LPAREN expression RPAREN LBRACE program RBRACE'''
    p[0] = [(p[3], p[6])]

def p_optional_elifs(p):
    '''optional_elifs : elif_clauses
                      | empty'''
    if p[1] is None:
        p[0] = []
    else:
        p[0] = p[1]

def p_elif_clauses(p):
    '''elif_clauses : elif_clauses elif_clause
                    | elif_clause'''
    if len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    else:
        p[0] = [p[1]]

def p_elif_clause(p):
    '''elif_clause : AMA_HADDII LPAREN expression RPAREN LBRACE program RBRACE'''
    p[0] = (p[3], p[6])

def p_optional_else(p):
    '''optional_else : HADDII_KALE LBRACE program RBRACE
                     | empty'''
    if len(p) > 2:
        p[0] = p[3]
    else:
        p[0] = None