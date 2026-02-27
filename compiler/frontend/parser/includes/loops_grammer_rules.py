# loops_grammer_rules.py (Fixed Indices)

from compiler.frontend.parser.ast_nodes import (
    WhileNode,
    DoWhileNode,
    ForRangeNode,
    ForEachNode,
    BreakNode,
    ContinueNode
)

def p_statement_while(p):
    '''statement : INTA AY LPAREN expression RPAREN body_statements'''
    line = p.lineno(1)
    filename = p.lexer.filename
    # FIXED: p[4] is the expression, p[6] is the body
    p[0] = WhileNode(line, p[4], p[6], filename)

def p_statement_do_while(p):
    '''statement : SAMAY body_statements INTA AY LPAREN expression RPAREN SEMICOLON'''
    line = p.lineno(1)
    filename = p.lexer.filename
    # FIXED: p[6] is the expression
    p[0] = DoWhileNode(line, p[2], p[6], filename)

def p_statement_for_range(p):
    '''statement : SOCO IDENTIFIER LAGA BILAABO expression DOTDOT expression body_statements'''
    line = p.lineno(1)
    filename = p.lexer.filename
    p[0] = ForRangeNode(line, p[2], p[5], p[7], p[8], filename)

def p_statement_for_each(p):
    '''statement : SOCO IDENTIFIER KASTA LAGA HELO expression body_statements'''
    line = p.lineno(1)
    filename = p.lexer.filename
    p[0] = ForEachNode(line, p[2], p[6], p[7], filename)

def p_statement_break(p):
    '''statement : JOOG SEMICOLON'''
    line = p.lineno(1)
    filename = p.lexer.filename
    p[0] = BreakNode(line, filename)

def p_statement_continue(p):
    '''statement : KASOCO SEMICOLON'''
    line = p.lineno(1)
    filename = p.lexer.filename
    p[0] = ContinueNode(line, filename)
