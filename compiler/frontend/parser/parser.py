import ply.yacc as yacc
from compiler.frontend.lexer.lexer import tokens, lexer
from compiler.frontend.parser.grammar_rules import *



def p_error(p):
    # XALKA WAA KAN: Isticmaal 'p.lexer' halkii aad ka isticmaali lahayd 'parser.lexer'
    if p:
        # Kiiska 1: Ciladdu waxay leedahay calaamad (token) gaar ah.
        # Waxaan ka helaynaa magaca faylka 'lexer'-ka ku xiran calaamaddan.
        filename = getattr(p.lexer, 'filename', '<fayl aan la aqoon>')
        print(f"Khalad Naxwe: Khalad Ayaa Laga Helay Faylkan '{filename}' saddarka {p.lineno}: Lama Aqooonsano '{p.value}'")
        sys.exit(1)
    else:
        # Kiiska 2: Dhammaad fayl lama filaan ah. 'p' waa None.
        # Halkan, waxaan isku dayeynaa inaan ka helno magaca faylka shayga 'lexer' ee caalamiga ah (global).
        filename = getattr(lexer, 'filename', '<fayl aan la aqoon>')
        print(f"Khalad Naxwe: Waxaa Laga Helay Dhammaadka '{filename}':  faylkan")
        sys.exit(1)

# Build the parser
parser = yacc.yacc(debug=True)