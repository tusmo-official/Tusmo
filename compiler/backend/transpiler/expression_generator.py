# expression_generator.py (Corrected and Final)

from compiler.frontend.parser.ast_nodes import (
    TernaryOpNode, StringNode, NumberNode, FloatNode,
    CharNode, IdentifierNode, BinaryOpNode, FStringNode, BooleanNode,
    FunctionCallNode, ArrayAccessNode, ArrayTypeNode, MethodCallNode,
    ClassInstantiationNode, MemberAccessNode, ThisNode, WaalidNode, ArrayInitializationNode, ArrayTypeQueryNode,
    ASTNode, CCallNode, DictionaryInitializationNode, FunctionTypeNode, NamedArgument, TypeLiteralNode
)

from compiler.midend.built_in_fn import functions_ as built_in_functions

class Cilad(Exception):

    pass
class ExpressionGenerator:
    def __init__(self, main_generator):
        self.main_generator = main_generator
        self.symbol_table = main_generator.symbol_table

    def get_expression_type(self, node):
        if isinstance(node, WaalidNode):
             if self.main_generator.current_class and self.main_generator.current_class.parent_name:
                 return self.main_generator.current_class.parent_name
             return None
        return self.main_generator.semantic_checker.get_expression_type(node, skip_context_check=True)

    def generate_expression(self, node):
        if not isinstance(node, ASTNode):
            raise Cilad(f"Generator Error: generate_expression received '{type(node).__name__}' instead of an AST node")

        if isinstance(node, NumberNode):
            return str(node.value)
        elif isinstance(node, FloatNode):
            return str(node.value)
        elif isinstance(node, StringNode):
            return self._escape_c_string_literal(node.value)
        elif isinstance(node, CharNode):
            return f"'{node.value}'"
        elif isinstance(node, BooleanNode):
            return "true" if node.value else "false"
        elif isinstance(node, IdentifierNode):
            return node.name
        elif isinstance(node, ThisNode):
            return "kan"
        elif isinstance(node, WaalidNode):
            # 'waalid' refers to the parent struct embedded in 'kan' (this).
            # We return its address to treat it as a pointer to the parent class.
            return "&kan->parent"
        elif isinstance(node, BinaryOpNode):
            return self._generate_binary_op(node)
        elif isinstance(node, TernaryOpNode):
            return self._generate_ternary_op(node)
        elif isinstance(node, FStringNode):
            return self._generate_fstring(node)
        elif isinstance(node, ArrayInitializationNode):
            return self._generate_array_initialization(node)
        elif isinstance(node, DictionaryInitializationNode):
            self.main_generator.used_features.add("dictionary")
            return self.main_generator.dictionary_generator.generate_initialization(node)

        # Consolidated Access Logic for [...] syntax
        elif isinstance(node, ArrayAccessNode):
            base_type = self.get_expression_type(node.array_name_node)
            base_expr_c = self.generate_expression(node.array_name_node)
            index_c = self.generate_expression(node.index_expression)
            index_type = self.get_expression_type(node.index_expression)

            # Case 1: It's a direct dictionary variable. Generate a get() call.
            if str(base_type) == 'qaamuus':
                self.main_generator.used_features.add("dictionary")
                return f"tusmo_qaamuus_get({base_expr_c}, {index_c})"

            # Case 2: It's a value from a mixed array. Unwrap it, then do a get() call.
            elif str(base_type) == 'dynamic_value':
                temp_var = self.main_generator.get_temp_var()
                # Evaluate once so we can branch based on runtime type
                self.main_generator.c_code += f"    TusmoValue {temp_var} = {base_expr_c};\n"
                if str(index_type) == 'eray':
                    self.main_generator.used_features.add("dictionary")
                    return f"tusmo_qaamuus_get({temp_var}.value.as_qaamuus, {index_c})"
                else:
                    self.main_generator.used_features.add("array")
                    return f"({temp_var}.value.as_tix->data[tusmo_bounds_check({index_c}, {temp_var}.value.as_tix->size)])"

            # Case 3: It's a string. Generate C string indexing.
            elif str(base_type) == 'eray':
                return f"{base_expr_c}[{index_c}]"

            # Case 4: It's a standard, typed Tusmo array.
            else:
                return self.main_generator.array_generator.generate_access(node)

        elif isinstance(node, ClassInstantiationNode):
            return self._generate_class_instantiation(node)
        elif isinstance(node, MemberAccessNode):
            object_c = self.generate_expression(node.object_node)
            object_type = self.get_expression_type(node.object_node)
            
            # Resolve inheritance depth
            class_info = self.symbol_table.get(str(object_type))
            depth = 0
            if class_info and class_info[1] == 'class_definition':
                current_class = class_info[0]
                while current_class:
                    if any(m.var_name == node.member_name for m in current_class.members):
                        break
                    if getattr(current_class, 'parent_class', None):
                        current_class = current_class.parent_class
                        depth += 1
                    else:
                        break
            
            # Build access string
            if depth == 0:
                return f"{object_c}->{node.member_name}"
            else:
                 parents = ".parent" * depth
                 # object_c is pointer, so ->parent gives the first parent struct. 
                 # subsequent parents are inside that struct, so .parent.
                 return f"{object_c}->{parents[1:]}.{node.member_name}"
                 
        elif isinstance(node, MethodCallNode):
            return self._generate_method_call(node)
        elif isinstance(node, FunctionCallNode):
            return self._generate_function_call(node)
        elif isinstance(node, CCallNode):
            return self._generate_ccall(node)
        elif isinstance(node, TypeLiteralNode):
            return f'"{node.type_name}"'
        else:
            raise Cilad(f"Generator Error: No C code generation logic for expression node '{type(node).__name__}'")

    def _generate_array_initialization(self, node: ArrayInitializationNode):
        array_type = self.get_expression_type(node)
        return self.main_generator.array_generator._generate_recursive_initializer(array_type, node.elements)

    def _generate_class_instantiation(self, node: ClassInstantiationNode):
        creator_func = f"_create_{node.class_name}"
        args = self._unwrap_args(getattr(node, "ordered_args", None), node.constructor_args)
        arg_exprs = [self.generate_expression(arg) for arg in args]
        return f"{creator_func}({', '.join(arg_exprs)})"

    def _generate_method_call(self, node: MethodCallNode):
        object_type = self.get_expression_type(node.object_node)
        if isinstance(object_type, ArrayTypeNode):
            return self.main_generator.array_generator.generate_method_call(node)
        
        if str(object_type) == 'qaamuus':
            self.main_generator.used_features.add("dictionary")
            object_c = self.generate_expression(node.object_node)
            args = self._unwrap_args(getattr(node, "ordered_args", None), node.args_list)
            
            if node.method_name == 'kasaar':
                key_c = self.generate_expression(args[0])
                return f"tusmo_qaamuus_delete({object_c}, {key_c})"
            
            if node.method_name == 'majiraa':
                key_c = self.generate_expression(args[0])
                return f"tusmo_qaamuus_has_key({object_c}, {key_c})"
        object_c = self.generate_expression(node.object_node)
        
        # Use recorded source class for name mangling
        source_class = getattr(node, 'method_source_class', None)
        if source_class:
            class_name = source_class.name
        else:
            class_name = str(object_type)
            
        mangled_name = f"{class_name}_{node.method_name}"
        
        # If the method is inherited, we need to cast 'kan' (object_c) to the parent type.
        # However, in our C implementation, we use &child->parent for waalid access.
        # For an inherited call b.s(), we want A_s(&b->parent).
        # We need to find the depth of inheritance.
        
        cast_object_c = object_c
        if source_class and source_class.name != str(object_type):
            # Calculate depth from child to source parent
            child_info = self.symbol_table.get(str(object_type))
            if child_info and child_info[1] == 'class_definition':
                current = child_info[0]
                depth = 0
                while current and current.name != source_class.name:
                    current = getattr(current, 'parent_class', None)
                    depth += 1
                
                if depth > 0:
                    parents = ".parent" * depth
                    # object_c is pointer, so ->parent gives the first parent struct.
                    # We need the ADDRESS of that parent struct to pass as the new 'kan' (pointer).
                    cast_object_c = f"&({object_c}->{parents[1:]})"

        args = self._unwrap_args(getattr(node, "ordered_args", None), node.args_list)
        arg_exprs = [cast_object_c] + [self.generate_expression(arg) for arg in args]
        return f"{mangled_name}({', '.join(arg_exprs)})"

    def _generate_binary_op(self, node):
        left_c = self.generate_expression(node.left)
        right_c = self.generate_expression(node.right)
        left_type = self.get_expression_type(node.left)
        right_type = self.get_expression_type(node.right)
        if node.op == '+' and str(left_type) == 'eray':
            self.main_generator.used_features.add("string")
            right_c_converted = self._ensure_string_operand(right_c, right_type)
            return f"tusmo_concat_cstr({left_c}, {right_c_converted})"
        if node.op in ('==', '!=') and ('eray' in (str(left_type), str(right_type))):
            self.main_generator.used_features.add("string")
            cmp = f"strcmp({left_c}, {right_c})"
            if node.op == '==':
                return f"({cmp} == 0)"
            else:
                return f"({cmp} != 0)"
        op_map = {'+': '+', '-': '-', '*': '*', '/': '/', '%': '%',
                  'iyo': '&&', 'ama': '||', '==': '==', '!=': '!=',
                  '>': '>', '<': '<', '>=': '>=', '<=': '<='}
        
        # Handle Type Comparison (e.g., n == tiro)
        if node.op in ('==', '!='):
            lt_str = str(left_type)
            rt_str = str(right_type)
            
            if lt_str.startswith("nooc:") or rt_str.startswith("nooc:"):
                # One of them is a type literal
                if lt_str.startswith("nooc:"):
                    type_name = lt_str[5:]
                    other_c = right_c
                    other_type = rt_str
                else:
                    type_name = rt_str[5:]
                    other_c = left_c
                    other_type = lt_str
                
                is_equal = node.op == '=='
                
                # Case 1: Other side is a dynamic value
                if other_type == "dynamic_value":
                    self.main_generator.used_features.add("conversion")
                    self.main_generator.used_features.add("string")
                    res = f'(strcmp(tusmo_type_of({other_c}), "{type_name}") == 0)'
                    return res if is_equal else f"(!{res})"
                
                # Case 2: Other side is already a string (e.g. nooc(x) == tiro)
                elif other_type == "eray":
                    self.main_generator.used_features.add("string")
                    res = f'(strcmp({other_c}, "{type_name}") == 0)'
                    return res if is_equal else f"(!{res})"
                
                # Case 3: Other side is another type literal
                elif other_type.startswith("nooc:"):
                    other_type_name = other_type[5:]
                    res = "true" if type_name == other_type_name else "false"
                    return res if is_equal else ("false" if res == "true" else "true")
                
                # Case 4: Static type resolve
                else:
                    res = "true" if type_name == other_type else "false"
                    return res if is_equal else ("false" if res == "true" else "true")

        c_op = op_map.get(node.op)
        if c_op:
            return f"({left_c} {c_op} {right_c})"
        else:
            raise Cilad(f"Generator Error: Hawl-wadeen aan la aqoon {node.op}")

    def _generate_ternary_op(self, node):
        condition_c = self.generate_expression(node.condition)
        if_true_c = self.generate_expression(node.if_true)
        if_false_c = self.generate_expression(node.if_false)
        return f"({condition_c} ? {if_true_c} : {if_false_c})"

    def _escape_c_string_literal(self, s):
        s = s.replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        s = s.replace('\n', '\\n')
        s = s.replace('\r', '\\r')
        s = s.replace('\t', '\\t')
        return f'"{s}"'

    def _generate_fstring(self, node: FStringNode):
        self.main_generator.used_features.add("string")
        segments = []
        for part_type, part_value in node.parts:
            if part_type == "text":
                if part_value:
                    segments.append(self._escape_c_string_literal(part_value))
            elif part_type == "expr":
                expr_node = part_value if isinstance(part_value, ASTNode) else StringNode(str(part_value), line=node.line, filename=node.filename)
                expr_code = self.generate_expression(expr_node)
                expr_type = self.get_expression_type(expr_node)
                segments.append(self._ensure_string_operand(expr_code, expr_type))
        if not segments:
            return '""'
        result = segments[0]
        for segment in segments[1:]:
            result = f"tusmo_concat_cstr({result}, {segment})"
        return result

    def _generate_ccall(self, node):
        '''Registering c call fn'''
        c_function_name = node.c_function_name
        if c_function_name in ["tusmo_init_random", "tusmo_random_int", "tusmo_random_double"]:
            self.main_generator.used_features.add("nasiib")
        
        elif "tusmo_time" in c_function_name or "tusmo_get" in c_function_name:
            self.main_generator.used_features.add("wakhti")
        
        elif "tusmo_os" in c_function_name:
            self.main_generator.used_features.add("os")
            if c_function_name == "tusmo_os_list_dir":
                self.main_generator.used_features.add("array")
        elif "tusmo_http" in c_function_name:
            self.main_generator.used_features.add("http")
            if c_function_name == "tusmo_http_server_accept":
                self.main_generator.used_features.add("dictionary")
            if c_function_name == "tusmo_http_qaamuus_to_json":
                self.main_generator.used_features.add("dictionary")
        elif "tusmo_socket" in c_function_name:
            self.main_generator.used_features.add("socket")
        elif "tusmo_ws" in c_function_name:
            self.main_generator.used_features.add("websocket")
            self.main_generator.used_features.add("socket")  # WebSocket needs socket
            self.main_generator.used_features.add("dictionary")  # For decode_frame result
        c_args = [self.generate_expression(arg) for arg in node.args]

        return f'{c_function_name}({", ".join(c_args)})'

    def _ensure_string_operand(self, expr_code, expr_type):
        expr_type_str = str(expr_type)
        if expr_type_str == 'eray':
            return expr_code
        if expr_type_str == 'xaraf':
            self.main_generator.used_features.add("string")
            return f'tusmo_str_format("%c", {expr_code})'
        if expr_type_str == 'tiro':
            self.main_generator.used_features.add("string")
            return f'tusmo_str_format("%d", {expr_code})'
        if expr_type_str == 'jajab':
            self.main_generator.used_features.add("string")
            return f'tusmo_str_format("%f", {expr_code})'
        if expr_type_str == 'miyaa':
            return f"(({expr_code}) ? \"run\" : \"been\")"
        raise Cilad("F-string expressions must evaluate to 'eray', 'xaraf', 'tiro', 'jajab', or 'miyaa'.")

    def _generate_function_call(self, node: FunctionCallNode):
        # Handle Type Casting Functions
        if node.name in ["eray", "tiro", "jajab", "miyaa"]:
            self.main_generator.used_features.add("conversion")
            args = self._unwrap_args(getattr(node, "ordered_args", None), node.params)
            if len(args) != 1:
                raise Cilad(f"Khalad: Hawsha '{node.name}' waxay filaysaa 1 parameter, laakiin waxaa lasiiyay {len(args)}")
            
            arg_node = args[0]
            arg_c = self.generate_expression(arg_node)
            arg_type = self.get_expression_type(arg_node)

            # If the argument is already a TusmoValue (dynamic array element), pass it straight through.
            if str(arg_type) == "dynamic_value":
                c_func_name = f"tusmo_to_{node.name}"
                return f"{c_func_name}({arg_c})"

            # Create a TusmoValue struct on the stack
            val_var = self.main_generator.get_temp_var()
            self.main_generator.c_code += f"    TusmoValue {val_var};\n"
            self.main_generator.c_code += f"    {val_var}.type = {self._get_tusmo_type_enum(arg_type)};\n"
            self.main_generator.c_code += f"    {val_var}.value.{self._get_union_member(arg_type)} = {arg_c};\n"

            c_func_name = f"tusmo_to_{node.name}"
            return f"{c_func_name}({val_var})"

        if node.name in built_in_functions:
            feature = built_in_functions[node.name].get("feature")
            if feature:
                self.main_generator.used_features.add(feature)
        if node.name == 'dherer':
            if len(node.params) != 1:
                raise Cilad(f"Khalad: dherer Waxa uu filayaa kaliya 1 parameter, laakiin waxaa lasiiyay {len(node.params)} ")
            arg_expr = self.generate_expression(node.params[0])
            arg_type = self.main_generator.semantic_checker.get_expression_type(node.params[0], skip_context_check=True)
            if str(arg_type) == 'eray':
                return f"strlen({arg_expr})"
            elif isinstance(arg_type, ArrayTypeNode):
                return f"{arg_expr}->size"
            else:
                raise Cilad(f"Generator Error: dherer does not support type {arg_type}")
        if node.name == 'nooc':
            if len(node.params) != 1:
                raise Cilad("Generator Error: nooc expects exactly 1 parameter")
            arg_node = node.params[0]
            # Special case: nooc(arr[]) asks for the element type of a tix.
            if isinstance(arg_node, ArrayTypeQueryNode):
                base_type = self.main_generator.semantic_checker.get_expression_type(arg_node, skip_context_check=True)
                if not isinstance(base_type, ArrayTypeNode):
                    raise Cilad("Generator Error: nooc(arr[]) requires a tix variable.")
                self.main_generator.used_features.add("array")
                elem_type = base_type.element_type
                type_str = "tix:dynamic" if elem_type is None else f"tix:{elem_type}"
                return f'"{type_str}"'

            arg_type = self.main_generator.semantic_checker.get_expression_type(arg_node, skip_context_check=True)
            if isinstance(arg_type, ArrayTypeNode):
                self.main_generator.used_features.add("array")
            # If it's a mixed-array element (dynamic_value), ask the runtime for the actual tag.
            if str(arg_type) == "dynamic_value":
                self.main_generator.used_features.add("conversion")
                arg_expr = self.generate_expression(arg_node)
                return f"tusmo_type_of({arg_expr})"
            type_str = str(arg_type)
            return f'"{type_str}"'
        if node.name == 'tix_cayiman':
            self.main_generator.used_features.add("array")
            raise Cilad("Generator Error: tix_cayiman can only be used in variable declarations or assignments.")
        
        func_info = self.symbol_table.get(node.name)
        if not func_info:
            # This should have been caught by the semantic analyzer, but as a safeguard:
            raise Cilad(f"hawashan '{node.name}' Ma ahan mid jirta.")

        # Check if it's a direct function call or an indirect call through a variable
        if isinstance(func_info[1], FunctionTypeNode):
            # Indirect call through a variable
            c_func_name = node.name
            args = self._unwrap_args(getattr(node, "ordered_args", None), node.params)
            arg_exprs = [self.generate_expression(arg) for arg in args]
            return f"{c_func_name}({', '.join(arg_exprs)})"
        else:
            # Direct function call
            func_node = func_info[0]
            args = self._unwrap_args(getattr(node, "ordered_args", None), node.params)

            arg_exprs = [self.generate_expression(arg) for arg in args]
            
            num_provided_args = len(arg_exprs)
            num_required_params = len(func_node.params)

            if num_provided_args < num_required_params:
                for i in range(num_provided_args, num_required_params):
                    param = func_node.params[i]
                    if param.default_value:
                        arg_exprs.append(self.generate_expression(param.default_value))
                    else:
                        # This should also be caught by the semantic analyzer
                        raise Cilad(f"Generator Error: Missing argument for parameter '{param.name}' with no default value.")

            c_func_name = node.name
            return f"{c_func_name}({', '.join(arg_exprs)})"

    def _get_tusmo_type_enum(self, type_str):
        type_map = {
            "tiro": "TUSMO_TIRO",
            "jajab": "TUSMO_JAJAB",
            "eray": "TUSMO_ERAY",
            "miyaa": "TUSMO_MIYAA",
            "xaraf": "TUSMO_XARAF",
        }
        return type_map.get(str(type_str), "TUSMO_ERAY") # Default to string for unknown

    def _get_union_member(self, type_str):
        member_map = {
            "tiro": "as_tiro",
            "jajab": "as_jajab",
            "eray": "as_eray",
            "miyaa": "as_miyaa",
            "xaraf": "as_xaraf",
        }
        return member_map.get(str(type_str), "as_eray")

    def _unwrap_args(self, ordered, raw_list):
        if ordered is not None:
            return ordered
        result = []
        for a in raw_list:
            if isinstance(a, NamedArgument):
                result.append(a.value)
            else:
                result.append(a)
        return result
