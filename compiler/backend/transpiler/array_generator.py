from compiler.frontend.parser.ast_nodes import (
 ArrayTypeNode, 
    ArrayAccessNode, MethodCallNode, ArrayAssignmentNode, NamedArgument
)
from compiler.midend.symbol_table import SymbolTable

class ArrayGenerator:
    def __init__(self, main_generator, expr_generator):
        self.main_generator = main_generator
        self.expr_generator = expr_generator
        self.symbol_table = main_generator.symbol_table


    def get_c_type_map(self):
        return {'tiro': 'int', 'jajab': 'double', 'eray': 'char*', 'miyaa': 'bool', 'xaraf': 'char', 'waxbo': 'void', 'qaamuus': 'TusmoQaamuus*'}

    def get_tix_struct_name(self, element_type_str):
        # --- FIX #1 IS HERE ---
        # If the element type string is None or 'None', it's a dynamic array.
        if element_type_str is None or element_type_str == 'None':
            return "TusmoTixMixed"
            
        type_map = {'tiro': 'Tiro', 'jajab': 'Jajab', 'eray': 'Eray', 'miyaa': 'Miyaa', 'qaamuus': 'Mixed'}
        return f"TusmoTix{type_map.get(element_type_str)}"

    def get_c_type_from_tusmo_type(self, tusmo_type_node):
        if not isinstance(tusmo_type_node, ArrayTypeNode):
            return self.get_c_type_map().get(str(tusmo_type_node), "void*")
        
        element_type = tusmo_type_node.element_type
        if isinstance(element_type, ArrayTypeNode):
            return "TusmoTixGeneric*"
        else:
            struct_name = self.get_tix_struct_name(str(element_type))
            return f"{struct_name}*"

    def _generate_recursive_initializer(self, type_node, element_nodes):
        self.main_generator.used_features.add("array")
        temp_var = self.main_generator.get_temp_var()
        c_type = self.get_c_type_from_tusmo_type(type_node)
        capacity = len(element_nodes) if element_nodes else 8

        if isinstance(type_node.element_type, ArrayTypeNode):
            create_func = "tusmo_tix_generic_create"
            append_func = "tusmo_tix_generic_append"
            self.main_generator.c_code += f"    {c_type} {temp_var} = {create_func}({capacity});\n"
            for sub_array_literal_node in element_nodes:
                sub_array_type = type_node.element_type
                sub_array_elements = sub_array_literal_node.elements
                sub_init_var = self._generate_recursive_initializer(sub_array_type, sub_array_elements)
                self.main_generator.c_code += f"    {append_func}({temp_var}, {sub_init_var});\n"
        
        # --- FIX #2 IS HERE ---
        # Handle dynamic vs. homogeneous arrays
        else:
            element_type_str = str(type_node.element_type)

            # Check if we are creating a dynamic (mixed-type) array
            if element_type_str == 'None' or element_type_str == 'qaamuus':
                create_func = "tusmo_tix_mixed_create"
                append_func = "tusmo_tix_mixed_append"
                self.main_generator.c_code += f"    {c_type} {temp_var} = {create_func}({capacity});\n"
                
                # For mixed arrays, each element must be wrapped in a TusmoValue struct
                for element_node in element_nodes:
                    self.generate_mixed_append_call(temp_var, element_node)
            
            # Otherwise, it's a normal homogeneous array
            else:
                create_func = f"tusmo_hp_tix_{element_type_str}_create"
                append_func = f"tusmo_hp_tix_{element_type_str}_append"
                self.main_generator.c_code += f"    {c_type} {temp_var} = {create_func}({capacity});\n"
                for primitive_node in element_nodes:
                    element_c_code = self.expr_generator.generate_expression(primitive_node)
                    self.main_generator.c_code += f"    {append_func}({temp_var}, {element_c_code});\n"
                
        return temp_var

    def generate_access(self, node: ArrayAccessNode):
        self.main_generator.used_features.add("array")
        base_expr_c = self.expr_generator.generate_expression(node.array_name_node)
        index_c = self.expr_generator.generate_expression(node.index_expression)
        base_tusmo_type = self.expr_generator.get_expression_type(node.array_name_node)
        checked_index = f"tusmo_bounds_check({index_c}, {base_expr_c}->size)"

        # Accessing a dynamic array returns a TusmoValue, not a primitive
        if isinstance(base_tusmo_type, ArrayTypeNode) and base_tusmo_type.element_type is None:
            return f"({base_expr_c}->data[{checked_index}])"

        if isinstance(base_tusmo_type, ArrayTypeNode) and isinstance(base_tusmo_type.element_type, ArrayTypeNode):
            element_tusmo_type = base_tusmo_type.element_type
            element_c_type = self.get_c_type_from_tusmo_type(element_tusmo_type)
            return f"(({element_c_type})({base_expr_c}->data[{checked_index}]))"
        else:
            return f"({base_expr_c}->data[{checked_index}])"

    def generate_assignment(self, node: ArrayAssignmentNode):
        access_c = self.generate_access(node.array_access_node)
        value_c = self.expr_generator.generate_expression(node.value_expression)
        self.main_generator.c_code += f"    {access_c} = {value_c};\n"
        
    # In array_generator.py, replace the generate_method_call method with this:
    def generate_method_call(self, node: MethodCallNode):
        self.main_generator.used_features.add("array")
        object_c = self.expr_generator.generate_expression(node.object_node)
        object_type = self.expr_generator.get_expression_type(node.object_node)
        args = node.args_list # Use raw args list as we handle named args manually

        if node.method_name == 'gali':
            if len(args) == 2:
                # Insert: gali(boos=i, value)
                # First arg is boos=i (NamedArgument)
                index_node = args[0].value
                value_node = args[1]
                self.generate_insert_call(object_c, object_type, index_node, value_node)
            else:
                # Append: gali(value)
                self.generate_append_call(object_c, object_type, args[0])
            return ""

        if node.method_name == 'kasaar':
            arg = args[0]
            if isinstance(arg, NamedArgument) and arg.name == 'boos':
                # Pop: kasaar(boos=i)
                return self.generate_pop_call(object_c, object_type, arg.value)
            else:
                # Remove: kasaar(value)
                return self.generate_remove_call(object_c, object_type, arg)
        
        return ""

    def generate_append_call(self, array_c_name, array_type_node, element_node):
        element_type = array_type_node.element_type
        
        if element_type is None:
            self.generate_mixed_append_call(array_c_name, element_node)
        elif isinstance(element_type, ArrayTypeNode): # Nested array
            element_c_code = self.expr_generator.generate_expression(element_node)
            self.main_generator.c_code += f"    tusmo_tix_generic_append({array_c_name}, {element_c_code});\n"
        elif not isinstance(element_type, ArrayTypeNode):
            element_c_code = self.expr_generator.generate_expression(element_node)
            append_func = f"tusmo_hp_tix_{element_type}_append"
            self.main_generator.c_code += f"    {append_func}({array_c_name}, {element_c_code});\n"

    def generate_insert_call(self, array_c_name, array_type_node, index_node, element_node):
        element_type = array_type_node.element_type
        index_c = self.expr_generator.generate_expression(index_node)
        
        if element_type is None:
            self.generate_mixed_insert_call(array_c_name, index_c, element_node)
        elif isinstance(element_type, ArrayTypeNode): # Nested array
            element_c_code = self.expr_generator.generate_expression(element_node)
            self.main_generator.c_code += f"    tusmo_tix_generic_insert({array_c_name}, {index_c}, {element_c_code});\n"
        elif not isinstance(element_type, ArrayTypeNode):
            element_c_code = self.expr_generator.generate_expression(element_node)
            insert_func = f"tusmo_hp_tix_{element_type}_insert"
            self.main_generator.c_code += f"    {insert_func}({array_c_name}, {index_c}, {element_c_code});\n"

    def generate_pop_call(self, array_c_name, array_type_node, index_node):
        element_type = array_type_node.element_type
        index_c = self.expr_generator.generate_expression(index_node)
        
        if element_type is None:
            return f"tusmo_tix_mixed_pop({array_c_name}, {index_c})"
        elif isinstance(element_type, ArrayTypeNode): # Nested array
             # Return type needs cast to appropriate generic type, or just void*
             # But compiler expects valid C expr.
             # The correct return type for tix:tix:tiro is TusmoTixTiro*.
             # generic_pop returns void*. We need to cast it.
             # We can't easily determine the exact C struct name here without recursion logic, 
             # but get_c_type_from_tusmo_type does that.
             ret_type = self.get_c_type_from_tusmo_type(element_type)
             return f"(({ret_type})tusmo_tix_generic_pop({array_c_name}, {index_c}))"
        elif not isinstance(element_type, ArrayTypeNode):
            pop_func = f"tusmo_hp_tix_{element_type}_pop"
            return f"{pop_func}({array_c_name}, {index_c})"
        return "0" 

    def generate_remove_call(self, array_c_name, array_type_node, element_node):
        element_type = array_type_node.element_type
        
        if element_type is None:
            return self.generate_mixed_remove_call(array_c_name, element_node)
        elif isinstance(element_type, ArrayTypeNode): # Nested array
            element_c_code = self.expr_generator.generate_expression(element_node)
            return f"tusmo_tix_generic_remove({array_c_name}, (void*){element_c_code})"
        elif not isinstance(element_type, ArrayTypeNode):
            element_c_code = self.expr_generator.generate_expression(element_node)
            remove_func = f"tusmo_hp_tix_{str(element_type).lower()}_remove"
            return f"{remove_func}({array_c_name}, {element_c_code})"
        return "false"

    def _generate_tusmo_value(self, element_node):
        """Helper to generate a TusmoValue struct initialization code."""
        element_c_code = self.expr_generator.generate_expression(element_node)
        element_tusmo_type = self.expr_generator.get_expression_type(element_node)
        
        type_enum_map = {'tiro': 'TUSMO_TIRO', 'eray': 'TUSMO_ERAY', 'jajab': 'TUSMO_JAJAB', 'miyaa': 'TUSMO_MIYAA', 'xaraf': 'TUSMO_XARAF', 'qaamuus': 'TUSMO_QAAMUUS'}
        union_member_map = {'tiro': 'as_tiro', 'eray': 'as_eray', 'jajab': 'as_jajab', 'miyaa': 'as_miyaa', 'xaraf': 'as_xaraf', 'qaamuus': 'as_qaamuus'}
        
        type_str = str(element_tusmo_type)
        temp_var = self.main_generator.get_temp_var()
        
        self.main_generator.c_code += f"    TusmoValue {temp_var};\n"
        self.main_generator.c_code += f"    {temp_var}.type = {type_enum_map.get(type_str, 'TUSMO_WAXBA')};\n"
        if type_str in union_member_map:
            self.main_generator.c_code += f"    {temp_var}.value.{union_member_map[type_str]} = {element_c_code};\n"
            
        return temp_var

    def generate_mixed_append_call(self, array_c_name, element_node):
        temp_var = self._generate_tusmo_value(element_node)
        self.main_generator.c_code += f"    tusmo_tix_mixed_append({array_c_name}, {temp_var});\n"

    def generate_mixed_insert_call(self, array_c_name, index_c, element_node):
        temp_var = self._generate_tusmo_value(element_node)
        self.main_generator.c_code += f"    tusmo_tix_mixed_insert({array_c_name}, {index_c}, {temp_var});\n"

    def generate_mixed_remove_call(self, array_c_name, element_node):
        # For remove, we need to pass the value to check against
        # But _generate_tusmo_value emits statements, so we can't use it directly in an expression.
        # We need to emit the setup code and then call the function.
        # Since this method is expected to return an expression string (bool),
        # we might need to use a statement expression or pre-calculate.
        # However, generate_remove_call is called where an expression is expected.
        # This is tricky in C if we need multiple statements.
        # Solution: Use the comma operator or a statement expression if GCC extension is allowed.
        # Or better: generate the setup code BEFORE the current expression context?
        # The expression generator expects a string return.
        # If we are inside a larger expression, we can't easily emit statements.
        # BUT `generate_method_call` is usually called as a statement (for void methods) or expression.
        # `kasaar` returns a bool, so it's an expression.
        # We can use the GCC statement expression extension `({ ... })` which is standard in many C compilers including GCC/Clang.
        
        temp_var = self.main_generator.get_temp_var()
        element_c_code = self.expr_generator.generate_expression(element_node)
        element_tusmo_type = self.expr_generator.get_expression_type(element_node)
        type_str = str(element_tusmo_type)
        
        type_enum_map = {'tiro': 'TUSMO_TIRO', 'eray': 'TUSMO_ERAY', 'jajab': 'TUSMO_JAJAB', 'miyaa': 'TUSMO_MIYAA', 'xaraf': 'TUSMO_XARAF', 'qaamuus': 'TUSMO_QAAMUUS'}
        union_member_map = {'tiro': 'as_tiro', 'eray': 'as_eray', 'jajab': 'as_jajab', 'miyaa': 'as_miyaa', 'xaraf': 'as_xaraf', 'qaamuus': 'as_qaamuus'}
        
        setup_code = f"TusmoValue {temp_var}; {temp_var}.type = {type_enum_map.get(type_str, 'TUSMO_WAXBA')};"
        if type_str in union_member_map:
            setup_code += f" {temp_var}.value.{union_member_map[type_str]} = {element_c_code};"
            
        return f"({{ {setup_code} tusmo_tix_mixed_remove({array_c_name}, {temp_var}); }})"
