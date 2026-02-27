from compiler.frontend.parser.ast_nodes import EmbeddedCNode


def p_embedded_c_statement(p):
    '''statement : C_CODE LPAREN STRING RPAREN SEMICOLON'''
    line = p.lineno(1)
    filename = p.lexer.filename
    p[0] = EmbeddedCNode(p[3], line=line, filename=filename)
