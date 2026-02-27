from compiler.frontend.parser.ast_nodes import ArrayTypeNode, MemberAccessNode, ThisNode, ArrayAccessNode, DictionaryAccessNode

class QorGenerator:
    def __init__(self, main_generator, expr_generator):
        self.main_generator = main_generator
        self.expr_generator = expr_generator

    def _get_type_as_string(self, type_info):
        """
        Converts the type information (which could be a string or an ASTNode)
        into a consistent string representation.
        """
        if type_info is None:
            return "unknown"
        if isinstance(type_info, str):
            return type_info
        if isinstance(type_info, ArrayTypeNode):
            if type_info.element_type:
                return f"tix:{type_info.element_type}"
            else:
                return "tix"
        return "unknown"

    def _get_expression_type_enhanced(self, expr):
        """
        Enhanced type detection that handles special cases like kan.member access.
        """
        # Special handling for kan.member access
        if isinstance(expr, MemberAccessNode) and isinstance(expr.object_node, ThisNode):
            # Look up 'kan' in symbol table to get the class type
            kan_info = self.main_generator.symbol_table.get('kan')
            if kan_info:
                class_name = kan_info[1]
                class_info = self.main_generator.symbol_table.get(class_name)
                if class_info:
                    class_node = class_info[0]
                    # Find the member type
                    for member in class_node.members:
                        if member.var_name == expr.member_name:
                            return str(member.var_type)
        
        # Special handling for mixed array access - they return TusmoValue
        if isinstance(expr, ArrayAccessNode):
            array_type = self.expr_generator.get_expression_type(expr.array_name_node)
            if isinstance(array_type, ArrayTypeNode) and array_type.element_type is None:
                # This is a mixed array access - returns TusmoValue
                return "dynamic_value"
        
        # Normal case - use the expression generator
        raw_type = self.expr_generator.get_expression_type(expr)
        return self._get_type_as_string(raw_type)

    def generate(self, node):
        format_parts = []
        arg_parts = []

        def flush_printf_batch():
            """
            Generates a C printf call for all the simple types collected so far.
            """
            nonlocal format_parts, arg_parts
            if not format_parts:
                return

            # Build format string and arguments
            fmt = "".join(format_parts)
            args = ", ".join(arg_parts)
            self.main_generator.c_code += f'    printf("{fmt}"{", " + args if args else ""} \n);\n'
            self.main_generator.c_code += "    fflush(stdout);\n"

            # Reset batch
            format_parts = []
            arg_parts = []

        for expr in node.expressions:
            # LAST ATTEMPT: HARDCODED FIX
            if isinstance(expr, DictionaryAccessNode) and isinstance(expr.dictionary_node, ArrayAccessNode):
                flush_printf_batch()
                array_access_c = self.expr_generator.generate_expression(expr.dictionary_node)
                key_c = self.expr_generator.generate_expression(expr.key_node)
                unwrapped_dict = f"({array_access_c}).value.as_qaamuus"
                get_call = f"tusmo_qaamuus_get({unwrapped_dict}, {key_c})"
                self.main_generator.c_code += f'    tusmo_qor_dynamic_value({get_call});\n'
                self.main_generator.c_code += "    fflush(stdout);\n"
                continue

            # Get the type using enhanced detection
            expr_type_str = self._get_expression_type_enhanced(expr)
            c_expr = self.expr_generator.generate_expression(expr)

            # --- Handle complex types that need their own print function ---
            if expr_type_str.startswith("tix"):
                flush_printf_batch()
                self.main_generator.c_code += f'    prints({c_expr});\n'
                self.main_generator.c_code += "    fflush(stdout);\n"
            elif expr_type_str == "qaamuus":
                flush_printf_batch()
                self.main_generator.used_features.add("dictionary")
                self.main_generator.c_code += f'    tusmo_qaamuus_print({c_expr});\n'
                self.main_generator.c_code += "    fflush(stdout);\n"

            # --- Handle simple types that can be batched into one printf call ---
            elif expr_type_str == "tiro":
                format_parts.append("%d")
                arg_parts.append(c_expr)
            elif expr_type_str == "jajab":
                format_parts.append("%f")
                arg_parts.append(c_expr)
            elif expr_type_str == "eray":
                format_parts.append("%s")
                arg_parts.append(c_expr)
            elif expr_type_str == "xaraf":
                format_parts.append("%c")
                arg_parts.append(c_expr)
            elif expr_type_str == "miyaa":
                format_parts.append("%s")
                arg_parts.append(f'({c_expr} ? "run" : "been")')
            elif expr_type_str == "dynamic_value":
                # This is a TusmoValue from a mixed array - call the special function
                flush_printf_batch()
                self.main_generator.c_code += f'    tusmo_qor_dynamic_value({c_expr});\n'
                self.main_generator.c_code += "    fflush(stdout);\n"
            else:
                # Unknown type - try to call tusmo_qor_dynamic_value as fallback
                flush_printf_batch()
                self.main_generator.c_code += f'    tusmo_qor_dynamic_value({c_expr});\n'
                self.main_generator.c_code += "    fflush(stdout);\n"

        # After processing all expressions, flush any remaining batch
        flush_printf_batch()
        if node.expressions:
            self.main_generator.c_code += '    printf("\\n");\n'
            self.main_generator.c_code += "    fflush(stdout);\n"
