# grammar_rules.py (Corrected Formatting)

import sys

# Your existing imports
from .includes.keyd_grammar_rule import *
from .includes.qor_grammar_rule import *
from .includes.hel_grammer_rule import *
from .includes.condition_grammar_rule import *
from .includes.return_grammer_rule import *
from .includes.function_grammer_rule import *
from .includes.built_in_fn_grammer_rules import *
from .includes.loops_grammer_rules import *
from .includes.array_grammer_rule import *
from .includes.keen_grammer_rule import *
from .includes.class_grammer_rule import *
from .includes.embedded_c_grammar_rule import *


from .ast_nodes import (
    NumberNode, FloatNode, IdentifierNode, StringNode, CharNode,
    BinaryOpNode, FStringNode, BooleanNode, TernaryOpNode,
    ThisNode, DictionaryInitializationNode,
    FunctionTypeNode, TypeLiteralNode
)

# Start rule
start = 'program'

# --- Program Structure ---
def p_program(p):
    '''program : statement_list'''
    p[0] = p[1]

def p_statement_list(p):
    '''statement_list : statement_list top_level_item
                      | top_level_item
                      | empty'''
    if len(p) == 3:
        if p[2] is not None: p[1].append(p[2])
        p[0] = p[1]
    elif len(p) == 2 and p[1] is not None: p[0] = [p[1]]
    else: p[0] = []

def p_top_level_item(p):
    '''top_level_item : statement
                      | function_declaration
                      | class_declaration'''
    p[0] = p[1]

def p_body_statements(p):
    '''body_statements : LBRACE statement_list RBRACE'''
    p[0] = p[2]

def p_empty(p):
    'empty :'
    p[0] = None

# --- Statements ---
def p_statement(p):
    '''statement : declaration
                 | qor_statement
                 | hel
                 | assignment_statement
                 | condition_statement
                 | statement_return
                 | expression SEMICOLON
                 | keen_import
    '''
    p[0] = p[1]


def p_assignment_statement(p):
    '''assignment_statement : expression EQUALS expression SEMICOLON'''
    # This now handles variable, array, and dictionary assignments
    p[0] = AssignmentNode(p[1], p[2], p[3], p.lineno(2), p.lexer.filename)


# --- Type Specifiers ---
def p_type_specifier(p):
    '''type_specifier : primitive_type
                      | array_type
                      | function_type
                      | QAAMUUS
                      | IDENTIFIER'''
    p[0] = p[1]

def p_function_type(p):
    '''function_type : HAWL LPAREN param_type_list RPAREN COLON type_specifier'''
    p[0] = FunctionTypeNode(p.lineno(1), p[3], p[6], p.lexer.filename)

def p_param_type_list(p):
    '''param_type_list : param_type_list COMMA type_specifier
                       | type_specifier
                       | empty'''
    if len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    elif len(p) == 2 and p[1] is not None:
        p[0] = [p[1]]
    else:
        p[0] = []

# V V V --- FIX 1: EXPANDED TO MULTIPLE LINES --- V V V
def p_primitive_type(p):
    '''primitive_type : TIRO
                      | ERAY
                      | XARAF
                      | MIYAA
                      | JAJAB
                      | WAXBO'''
    p[0] = p[1]


# --- Expressions ---
precedence = (
    ('left', 'AMA', 'BARBAR'),
    ('left', 'IYO', 'AMPERSANDAMPERSAND'),
    ('left', 'LAMID', 'LAMID_MAAHA'),
    ('left', 'WEYN', 'YAR', 'WEYN_LAMID', 'YAR_LAMID'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MODULO'),
    ('right', 'CUSUB'),
    ('left', 'DOT'),
    ('right', 'AHAYN'),
    ('right', 'QUESTION'),
    ('left', 'LPAREN', 'RPAREN', 'LBRACKET')
)

# V V V --- FIX 2: EXPANDED TO MULTIPLE LINES --- V V V
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression MODULO expression
                  | expression WEYN expression
                  | expression YAR expression
                  | expression WEYN_LAMID expression
                  | expression YAR_LAMID expression
                  | expression LAMID expression
                  | expression LAMID_MAAHA expression
                  | expression IYO expression
                  | expression AMA expression
                  | expression AMPERSANDAMPERSAND expression
                  | expression BARBAR expression
                  | expression AHAYN expression'''
    p[0] = BinaryOpNode(p[1], p[2], p[3], line=p.lineno(2), filename=p.lexer.filename)

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

# V V V --- FIX 3: EXPANDED TO MULTIPLE LINES --- V V V
def p_expression(p):
    '''expression : simple_expression
                  | array_initialization
                  | dictionary_initialization
                  | array_access
                  | array_type_query
                  | builtin_function_call
                  | function_call
                  | c_call_expression'''
    p[0] = p[1]

# V V V --- FIX 4: EXPANDED TO MULTIPLE LINES --- V V V
def p_simple_expression(p):
    '''simple_expression : NUMBER
                         | FLOAT_LITERAL
                         | IDENTIFIER
                         | STRING
                         | CHAR_LITERAL
                         | RUN
                         | BEEN
                         | HAA
                         | MAYA
                         | KAN'''
    line, filename, slice_type = p.lineno(1), p.lexer.filename, p.slice[1].type
    if slice_type == "NUMBER": p[0] = NumberNode(p[1], line=line, filename=filename)
    elif slice_type == "FLOAT_LITERAL": p[0] = FloatNode(p[1], line=line, filename=filename)
    elif slice_type == "IDENTIFIER": p[0] = IdentifierNode(p[1], line=line, filename=filename)
    elif slice_type == "STRING": p[0] = StringNode(p[1], line=line, filename=filename)
    elif slice_type == "CHAR_LITERAL": p[0] = CharNode(p[1], line=line, filename=filename)
    elif slice_type in ("RUN", "HAA"): p[0] = BooleanNode(True, line=line, filename=filename)
    elif slice_type in ("BEEN", "MAYA"): p[0] = BooleanNode(False, line=line, filename=filename)
    elif slice_type == "KAN": p[0] = ThisNode(line=line, filename=filename)

def p_simple_expression_type(p):
    '''simple_expression : primitive_type
                         | QAAMUUS'''
    p[0] = TypeLiteralNode(p[1], line=p.lineno(1), filename=p.lexer.filename)

def p_expression_fstring(p):
    'expression : FSTRING'
    p[0] = FStringNode(p[1], line=p.lineno(1), filename=p.lexer.filename)

def p_expression_ternary(p):
    '''expression : expression QUESTION expression COLON expression'''
    p[0] = TernaryOpNode(p[1], p[3], p[5], line=p.lineno(2), filename=p.lexer.filename)

# --- Dictionary Rules ---
def p_dictionary_initialization(p):
    '''dictionary_initialization : LBRACE key_value_pairs RBRACE
                               | LBRACE empty RBRACE'''
    p[0] = DictionaryInitializationNode(p.lineno(1), p[2] or [], p.lexer.filename)

def p_key_value_pairs(p):
    '''key_value_pairs : key_value_pairs COMMA key_value_pair
                       | key_value_pair'''
    if len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    else:
        p[0] = [p[1]]

def p_key_value_pair(p):
    '''key_value_pair : expression COLON expression'''
    p[0] = (p[1], p[3])
