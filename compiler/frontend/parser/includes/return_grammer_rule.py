# return_grammer_rule.py (La cusboonaysiiyay)

from compiler.frontend.parser.ast_nodes import ReturnStatementNode

def p_return(p):
    '''statement_return : SOO_CELI expression SEMICOLON
                        | SOO_CELI SEMICOLON'''
    line = p.lineno(1)
    filename = p.lexer.filename
    
    if len(p) == 4:
        p[0] = ReturnStatementNode(p[2], line=line, filename=filename)
    else:
        p[0] = ReturnStatementNode(None, line=line, filename=filename)