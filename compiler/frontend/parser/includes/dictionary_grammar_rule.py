# compiler/frontend/parser/includes/dictionary_grammar_rule.py

from ..ast_nodes import (
    DictionaryTypeNode,
    DictionaryInitializationNode,
    KeyValuePairNode,
    DictionaryAccessNode
)

# --- Dictionary Type ---
def p_dictionary_type(p):
    '''dictionary_type : QAAMUUS'''
    p[0] = DictionaryTypeNode(line=p.lineno(1), filename=p.lexer.filename)

# --- Dictionary Literal ---
def p_expression_dictionary_literal(p):
    '''dictionary_initialization : LBRACE dictionary_pairs_opt RBRACE'''
    p[0] = DictionaryInitializationNode(line=p.lineno(1), pairs=p[2], filename=p.lexer.filename)

def p_dictionary_pairs_opt(p):
    '''dictionary_pairs_opt : dictionary_pairs
                           | empty'''
    p[0] = p[1] if p[1] else []

def p_dictionary_pairs(p):
    '''dictionary_pairs : dictionary_pairs COMMA dictionary_pair
                       | dictionary_pair'''
    if len(p) == 4:
        p[1].append(p[3])
        p[0] = p[1]
    else:
        p[0] = [p[1]]

def p_dictionary_pair(p):
    '''dictionary_pair : STRING COLON expression'''
    # For now, keys are only strings
    key_node = p[1]
    value_node = p[3]
    p[0] = KeyValuePairNode(key=key_node, value=value_node, line=p.lineno(1), filename=p.lexer.filename)
