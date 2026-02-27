# compiler/backend/transpiler/__init__.py (Updated)

from .c_code_generator import CCodeGenerator
from compiler.midend.symbol_table import SymbolTable
from compiler.midend.semanticanalyzer import SemanticChecker

class Transpiler:
    # 1. The __init__ method is updated to accept 'semantic_checker'.
    def __init__(self, symbol_table: SymbolTable, semantic_checker: SemanticChecker):
        self.symbol_table = symbol_table
        # 2. The semantic_checker is passed down when creating CCodeGenerator.
        self.used_features = set() 
        self.code_generator = CCodeGenerator(symbol_table, semantic_checker, self.used_features)
        
    def transpile(self, ast):
        return self.code_generator.generate(ast)