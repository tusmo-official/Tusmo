from compiler.frontend.parser.ast_nodes import (
    MethodCallNode, FunctionCallNode, CCallNode
)

def p_built_in_fn_names(p):
    '''fn_name : GALI
               | TIX_CAYIMAN
               | DHERER
               | ERAY
               | TIRO
               | JAJAB
               | MIYAA
    '''
    p[0] = p[1]


#this will be used like this: eg: my_list.gali(20) etc this function call needs before identifier and dot
def p_statement_method_call(p):
    '''statement : expression DOT fn_name LPAREN argument_list RPAREN SEMICOLON'''
    line = p.lineno(2)
    filename = p.lexer.filename
    p[0] = MethodCallNode(line, p[1], p[3], p[5], filename)

# this will be used like this: eg: tix_cayiman(5) etc this is really a function call
def p_builtin_function_call(p):
    '''builtin_function_call : fn_name LPAREN argument_list RPAREN'''
    line = p.lineno(2)
    filename = p.lexer.filename
    p[0] = FunctionCallNode(p[1], p[3], line, filename)

def p_nooc_call(p):
    '''expression : NOOC LPAREN expression RPAREN'''
    line = p.lineno(1)
    filename = p.lexer.filename
    p[0] = FunctionCallNode("nooc", [p[3]], line, filename)

def p_c_call_expression(p):
    '''c_call_expression : C_CALL LPAREN STRING RPAREN
                         | C_CALL LPAREN STRING COMMA argument_list RPAREN'''
    if len(p) == 5:
        p[0] = CCallNode(p[3], [], line=p.lineno(1), filename=p.lexer.filename)
    else:
        p[0] = CCallNode(p[3], p[5], line=p.lineno(1), filename=p.lexer.filename)
