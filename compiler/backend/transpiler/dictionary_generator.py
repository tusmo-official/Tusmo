# compiler/backend/transpiler/dictionary_generator.py

from compiler.frontend.parser.ast_nodes import (
    DictionaryInitializationNode, DictionaryAccessNode, DictionaryAssignmentNode,
    ArrayTypeNode
)

class DictionaryGenerator:
    def __init__(self, code_generator, expression_generator):
        self.code_generator = code_generator
        self.expr_generator = expression_generator

    def generate_initialization(self, node: DictionaryInitializationNode):
        dict_var = self.code_generator.get_temp_var()
        self.code_generator.c_code += f"    TusmoQaamuus* {dict_var} = tusmo_qaamuus_create();\n"

        for key_node, value_node in node.pairs:
            key_c = self.expr_generator.generate_expression(key_node)
            value_c, value_type = self._generate_tusmo_value(value_node)
            self.code_generator.c_code += f"    tusmo_qaamuus_set({dict_var}, {key_c}, {value_c});\n"
        
        return dict_var

    def generate_assignment(self, node: DictionaryAssignmentNode):
        dict_var_c = self.expr_generator.generate_expression(node.dictionary_access_node.dictionary_node)
        key_c = self.expr_generator.generate_expression(node.dictionary_access_node.key_node)
        value_c, _ = self._generate_tusmo_value(node.value_node)
        self.code_generator.c_code += f"    tusmo_qaamuus_set({dict_var_c}, {key_c}, {value_c});\n"

    def generate_access(self, node: DictionaryAccessNode):
        dict_var_c = self.expr_generator.generate_expression(node.dictionary_node)
        key_c = self.expr_generator.generate_expression(node.key_node)
        return f"tusmo_qaamuus_get({dict_var_c}, {key_c})"

    def _generate_tusmo_value(self, value_node):
        value_c = self.expr_generator.generate_expression(value_node)
        value_type = self.code_generator.semantic_checker.get_expression_type(value_node, skip_context_check=True)

        primitive_map = {
            "tiro": ("TUSMO_TIRO", f"(TusmoValue){{.type = TUSMO_TIRO, .value.as_tiro = {value_c}}}"),
            "jajab": ("TUSMO_JAJAB", f"(TusmoValue){{.type = TUSMO_JAJAB, .value.as_jajab = {value_c}}}"),
            "eray": ("TUSMO_ERAY", f"(TusmoValue){{.type = TUSMO_ERAY, .value.as_eray = {value_c}}}"),
            "miyaa": ("TUSMO_MIYAA", f"(TusmoValue){{.type = TUSMO_MIYAA, .value.as_miyaa = {value_c}}}"),
            "xaraf": ("TUSMO_XARAF", f"(TusmoValue){{.type = TUSMO_XARAF, .value.as_xaraf = {value_c}}}"),
        }

        # Primitive value
        if str(value_type) in primitive_map:
            tusmo_type_enum, tusmo_value_c = primitive_map[str(value_type)]
            return tusmo_value_c, tusmo_type_enum

        # Nested dictionary
        if str(value_type) == "qaamuus":
            return f"(TusmoValue){{.type = TUSMO_QAAMUUS, .value.as_qaamuus = {value_c}}}", "TUSMO_QAAMUUS"

        # Arrays (only mixed/qaamuus arrays map cleanly to TusmoValue today)
        if isinstance(value_type, ArrayTypeNode):
            elem_type = value_type.element_type
            if elem_type is None or str(elem_type) == "qaamuus":
                return f"(TusmoValue){{.type = TUSMO_TIX, .value.as_tix = {value_c}}}", "TUSMO_TIX"
        elif isinstance(value_type, str) and value_type in ("tix", "tix:qaamuus"):
            return f"(TusmoValue){{.type = TUSMO_TIX, .value.as_tix = {value_c}}}", "TUSMO_TIX"

        # Already a TusmoValue (e.g., coming from qaamuus_get or mixed array)
        if str(value_type) == "dynamic_value":
            return value_c, "dynamic_value"
        
        # Default for complex types (like other dictionaries or objects)
        return f"(TusmoValue){{.type = TUSMO_ERAY, .value.as_eray = \"<complex_object>\"}}", "TUSMO_ERAY"
