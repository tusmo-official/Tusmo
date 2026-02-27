import ply.lex as lex

reserved = {
    'keyd': 'KEYD', 'tiro': 'TIRO', 'eray': 'ERAY', 'xaraf': 'XARAF', 'miyaa': 'MIYAA',
    'jajab': 'JAJAB', 'tix': 'TIX', 'qaamuus': 'QAAMUUS', 'tix_cayiman':'TIX_CAYIMAN', 'run': 'RUN', 'haa': 'HAA', 
    'been': 'BEEN', 'maya': 'MAYA', 'hel': 'HEL', 'qor': 'QOR', 'show':'SHOW',
    'haddii': 'HADDII', 'ama_haddii': 'AMA_HADDII', 'haddii_kale': 'HADDII_KALE', 'hawl': 'HAWL', 'shaqo': 'SHAQO', 
    'soo_celi': 'SOO_CELI', 'inta': 'INTA', 'ay': 'AY', 'samay': 'SAMAY', 'soco': 'SOCO', 
    'laga': 'LAGA', 'bilaabo': 'BILAABO', 'kasta': 'KASTA', 'helo': 'HELO', 'joog': 'JOOG', 'kasoco':'KASOCO', 
    'ahayn': 'AHAYN', 'iyo': 'IYO', 'lamid': 'LAMID', 'weyn': 'WEYN', 'yar': 'YAR',
    'koox': 'KOOX', 'cusub': 'CUSUB', 'kan': 'KAN', 'dhis': 'DHIS', 'burbur': 'BURBUR', 'gali': 'GALI',
     'ama':'AMA', 'keen':'KEEN', 'waxbo':'WAXBO', '___c__call_': 'C_CALL', '___c__code_': 'C_CODE', 'nooc':'NOOC', 'dherer':'DHERER',
     'dhaxlaya': 'DHAXLAYA', 'waalid': 'WAALID'
}


tokens = [
    'IDENTIFIER', 'NUMBER', 'FLOAT_LITERAL', 'STRING', 'FSTRING', 'CHAR_LITERAL',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE','QUESTION', 'EQUALS', 'COLON', 'SEMICOLON', 'COMMA',
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET', 'DOT',
    'LAMID_MAAHA', 'WEYN_LAMID', 'YAR_LAMID', 'DOTDOT','MODULO','MEMBER_ACCESS','ARROW',
    'AMPERSANDAMPERSAND','BARBAR'
] + list(reserved.values())

# Regular expression rules for simple tokens
t_LAMID_MAAHA = r'!='
t_QUESTION = r'\?'
t_WEYN_LAMID = r'>='
t_YAR_LAMID = r'<='
t_LAMID = r'=='
t_EQUALS = r'='
t_WEYN = r'>'
t_ARROW = r'=>'
t_YAR = r'<'
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'{'
t_RBRACE = r'}'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_COLON = r':'
t_SEMICOLON = r';'
t_COMMA = r','
t_DOT = r'\.'
t_DOTDOT = r'\.\.'
t_MODULO = r'%'
t_ignore = ' \t'
t_AMPERSANDAMPERSAND = r'&&'
t_BARBAR = r'\|\|'

# Token Functions
def t_COMMENT(t): r'//.*'; pass

def t_FLOAT_LITERAL(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_ML_STRING(t):
    r'"""(.|\n)*?"""'
    content = t.value[3:-3]
    decoded = bytes(content, "utf-8").decode("unicode_escape")
    t.lexer.lineno += decoded.count('\n')
    t.value = decoded
    t.type = 'STRING'
    return t

def _parse_fstring_content(content):
    # Parse the f-string content to extract expressions
    parts = []
    i = 0
    while i < len(content):
        if content[i] == '{' and i + 1 < len(content) and content[i+1] != '{':
            # Start of an expression
            j = i + 1
            brace_count = 1
            while j < len(content) and brace_count > 0:
                if content[j] == '{':
                    brace_count += 1
                elif content[j] == '}':
                    brace_count -= 1
                j += 1
            
            if brace_count == 0:
                # Extract the expression
                expr = content[i+1:j-1]
                parts.append(('expr', expr))
                i = j
            else:
                # Unmatched brace, treat as literal
                parts.append(('text', content[i]))
                i += 1
        elif content[i] == '{' and i + 1 < len(content) and content[i+1] == '{':
            # Escaped brace
            parts.append(('text', '{'))
            i += 2
        elif content[i] == '}' and i + 1 < len(content) and content[i+1] == '}':
            # Escaped brace
            parts.append(('text', '}'))
            i += 2
        else:
            # Regular text
            parts.append(('text', content[i]))
            i += 1
    return parts

def t_FSTRING(t):
    r'\$"""(.|\n)*?"""|\$"([^"\\]|\\.)*"'
    raw = t.value
    if raw.startswith('$"""'):
        content = raw[4:-3]
        t.lexer.lineno += content.count('\n')
    else:
        content = raw[2:-1]
    decoded = bytes(content, "utf-8").decode("unicode_escape")
    t.value = _parse_fstring_content(decoded)
    return t

def t_STRING(t):
    r'"([^\\"]|\\.)*"'
    raw = t.value[1:-1]
    t.value = bytes(raw, "utf-8").decode("unicode_escape")
    return t

def t_CHAR_LITERAL(t):
    r"'.'"
    # Sadarkan wuxuu ka saarayaa xigashada hore (') iyo tan dambe (')
    t.value = t.value[1:-1]
    return t
    
def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

def t_newline(t): r'\n+'; t.lexer.lineno += len(t.value)

# def t_error(t): print(f"Calaamad aan la aqoon: '{t.value[0]}' sadarka {t.lineno}"); t.lexer.skip(1)

def t_error(t):
    filename = getattr(t.lexer, 'filename', '<fayl aan la aqoon>')
    print(f"Cilad Erayeed (Lexical): Xaraf aan la oggolayn '{t.value[0]}' oo ku jira '{filename}' safka {t.lineno}")
    t.lexer.skip(1)



# Build the lexer
lexer = lex.lex()
