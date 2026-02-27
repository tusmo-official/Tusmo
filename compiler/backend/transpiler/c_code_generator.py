# c_code_generator.py (Updated)

from compiler.frontend.parser.ast_nodes import *
from compiler.midend.symbol_table import SymbolTable
from compiler.midend.semanticanalyzer import SemanticChecker, SemanticError

from .keyd_generator import KeydGenerator
from .qor_generator import QorGenerator
from .hel_generator import HelGenerator
from .expression_generator import ExpressionGenerator
from .keyd_assignment_generator import Keyd_Assignment_Generator
from .condition_generator import ConditionGenerator
from .return_generator import ReturnGenerator
from .function_generator import FunctionGenerator
from .array_generator import ArrayGenerator
from .dictionary_generator import DictionaryGenerator
from .loop_generator import LoopGenerator
from .class_generator import ClassGenerator
from compiler.frontend.parser.ast_nodes import MethodCallNode
from compiler.frontend.parser.ast_nodes import ArrayTypeNode, EmbeddedCNode


class CCodeGenerator:
    # 1. The __init__ method is updated to accept 'semantic_checker'.
    def __init__(self, symbol_table: SymbolTable, semantic_checker: SemanticChecker, used_features):
        self.symbol_table = symbol_table
        # 2. The semantic_checker is stored as an attribute. This is what fixes the error.
        self.semantic_checker = semantic_checker

        self.c_code = ""
        self.temp_var_counter = 0
        self.function_definitions = ""
        self.class_definitions = ""
        self.current_class = None
        self.used_features = used_features
        self.embedded_c_chunks = []

        self.expr_generator = ExpressionGenerator(self)
        self.function_generator = FunctionGenerator(self, self.expr_generator)
        self.keyd_generator = KeydGenerator(self, self.expr_generator)
        self.keyd_assignment = Keyd_Assignment_Generator(self, self.expr_generator)
        self.qor_generator = QorGenerator(self, self.expr_generator)
        self.hel_generator = HelGenerator(self)
        self.condition_generator = ConditionGenerator(self, self.expr_generator)
        self.return_generator = ReturnGenerator(self, self.expr_generator)
        self.array_generator = ArrayGenerator(self, self.expr_generator)
        self.dictionary_generator = DictionaryGenerator(self, self.expr_generator)
        self.loop_generator = LoopGenerator(self, self.expr_generator)
        self.class_generator = ClassGenerator(self)

    def get_temp_var(self):
        self.temp_var_counter += 1
        return f"__tusmo_temp_{self.temp_var_counter}"
    
    # Add this method to the CCodeGenerator class in c_code_generator.py

    def _generate_methodcallnode(self, node: MethodCallNode):
        """Generate code for a method call as a statement."""
        object_type = self.semantic_checker.get_expression_type(node.object_node, skip_context_check=True)
        
        # Handle array methods specially
        if isinstance(object_type, ArrayTypeNode):
            method_call_c = self.array_generator.generate_method_call(node)
            if method_call_c: # Only add if code was generated
                self.c_code += f"    {method_call_c};\n"
        else:
            # For class methods, generate as an expression statement
            method_call_c = self.expr_generator.generate_expression(node)
            self.c_code += f"    {method_call_c};\n"

    def get_c_type(self, tusmo_type):
        if isinstance(tusmo_type, FunctionTypeNode):
            return_type = self.get_c_type(tusmo_type.return_type)
            param_types = [self.get_c_type(p) for p in tusmo_type.param_types]
            if not param_types:
                param_types.append("void")
            return f"{return_type} (*)({', '.join(param_types)})"
        if isinstance(tusmo_type, ArrayTypeNode):
            return self.array_generator.get_c_type_from_tusmo_type(tusmo_type)
        if isinstance(tusmo_type, str):
            type_info = self.symbol_table.get(tusmo_type)
            if type_info and type_info[1] == 'class_definition':
                return f"{tusmo_type}*"
            type_map = self.array_generator.get_c_type_map()
            return type_map.get(tusmo_type, "void*")
        return "void*"

    def generate(self, ast):
        self.c_code = ""
        self.function_definitions = ""
        self.class_definitions = ""
        self.embedded_c_chunks = []
        for node in ast:
            self._generate_node(node)
        header_include = '#include "tusmo_runtime.h"\n\n'
        embedded_section = ""
        if self.embedded_c_chunks:
            embedded_bodies = []
            for code, meta in self.embedded_c_chunks:
                comment = ""
                if meta.filename:
                    comment = f"/* Embedded C from {meta.filename}:{meta.line} */\n"
                body = code
                if not body.endswith("\n"):
                    body += "\n"
                embedded_bodies.append(f"{comment}{body}")
            embedded_section = "".join(embedded_bodies) + "\n"
        final_c_code = (
            f"{header_include}"
            f"{embedded_section}"
            f"{self.class_definitions}"
            f"{self.function_definitions}"
            f"int main(void) {{\n"
            f"    GC_INIT();\n"
            f"{self.c_code}"
            f"    return 0;\n"
            f"}}\n"
        )
        return final_c_code, self.used_features

    def _generate_node(self, node):
        if node is None: return
        if isinstance(node, list):
            for sub_node in node: self._generate_node(sub_node)
            return
        if isinstance(node, ClassNode):
            self._generate_classnode(node)
        elif isinstance(node, FunctionNode):
            self._generate_functionnode(node)
        else:
            method_name = f"_generate_{type(node).__name__.lower()}"
            method = getattr(self, method_name, self._unhandled_node)
            method(node)

    def _unhandled_node(self, node):
        if isinstance(node, ExpressionNode):
            expr_c = self.expr_generator.generate_expression(node)
            self.c_code += f"    {expr_c};\n"
        else:
            print(f"Digniin: Ma jiro hab-turjun loogu talagalay nooca '{type(node).__name__}' ee ku jira jirka ugu weyn.")

    def _generate_classnode(self, node: ClassNode):
        self.class_generator.generate(node)
    def _generate_functionnode(self, node: FunctionNode):
        self.function_generator.generate(node)
    
    def _generate_keydnode(self, node: KeydNode):
        self.keyd_generator.generate(node)
        

    def _generate_assignmentnode(self, node: AssignmentNode):
        self.keyd_assignment.generate(node)
    def _generate_qornode(self, node: QorNode):
        self.used_features.add("io")
        self.qor_generator.generate(node)
    def _generate_helnode(self, node: HelNode):
        self.used_features.add("io")
        self.hel_generator.generate(node)
    def _generate_ifnode(self, node: IfNode):
        self.condition_generator.generate(node)
    
    def _generate_returnstatementnode(self, node): self.return_generator.generate(node)
    def _generate_arrayassignmentnode(self, node: ArrayAssignmentNode):
        self.used_features.add("array")
        self.array_generator.generate_assignment(node)
    def _generate_dictionaryinitializationnode(self, node: DictionaryInitializationNode):
        self.used_features.add("dictionary")
        self.dictionary_generator.generate_initialization(node)
    def _generate_dictionaryassignmentnode(self, node: DictionaryAssignmentNode):
        self.used_features.add("dictionary")
        self.dictionary_generator.generate_assignment(node)
    def _generate_breaknode(self, node: BreakNode):
        self.c_code += "    break;\n"
    def _generate_continuenode(self, node: ContinueNode):
        self.c_code += "    continue;\n"
    def _generate_embeddedcnode(self, node: EmbeddedCNode):
        self.embedded_c_chunks.append((node.code, node))
    def _generate_whilenode(self, node: WhileNode): self.loop_generator.generate_while(node)
    def _generate_dowhilenode(self, node: DoWhileNode): self.loop_generator.generate_do_while(node)
    def _generate_forrangenode(self, node: ForRangeNode): self.loop_generator.generate_for_range(node)
    def _generate_foreachnode(self, node: ForEachNode): self.loop_generator.generate_for_each(node)
    def _generate_keennode(self, node: KeenNode): pass
