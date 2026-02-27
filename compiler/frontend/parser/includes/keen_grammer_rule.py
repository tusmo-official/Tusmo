# keen_grammer_rule.py 
from compiler.frontend.parser.ast_nodes import KeenNode

def p_keen(p):
    '''keen_import : KEEN STRING SEMICOLON'''
    line = p.lineno(1)
    
    # Kani waa magaca faylka la rabo in la soo dejiyo (tusaale, "math.tus")
    filename_to_import = p[2].strip('"\'')
    
    # Kani waa magaca faylka uu ku qoran yahay qoraalka 'keen' laftiisa
    source_filename = p.lexer.filename
    
    # Hadda waxaan u gudbinaynaa labada macluumaad ee loo baahan yahay
    p[0] = KeenNode(line, filename_to_import, source_filename)