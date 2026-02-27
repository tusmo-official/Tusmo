from compiler.frontend.parser.ast_nodes import ArrayTypeNode, ArrayAccessNode


class Keyd_Assignment_Generator:
    def __init__(self, main_generator, expr_generator):
        self.main_generator = main_generator
        self.expr_generator = expr_generator

    def generate(self, node):
        left_expr_node = node.identifier
        op = node.op
        right_expr_node = node.expression

        # Special handling for dictionary assignment (dict["key"] = val)
        if isinstance(left_expr_node, ArrayAccessNode):
             base_type = self.main_generator.semantic_checker.get_expression_type(left_expr_node.array_name_node, skip_context_check=True)
             if str(base_type) == 'qaamuus':
                 dict_c = self.expr_generator.generate_expression(left_expr_node.array_name_node)
                 key_c = self.expr_generator.generate_expression(left_expr_node.index_expression)
                 
                 # Use dictionary generator helper to wrap value in TusmoValue
                 value_c, _ = self.main_generator.dictionary_generator._generate_tusmo_value(right_expr_node)
                 
                 self.main_generator.c_code += f"    tusmo_qaamuus_set({dict_c}, {key_c}, {value_c});\n"
                 return

        left_c_code = self.expr_generator.generate_expression(left_expr_node)

        if (op == "=" and hasattr(right_expr_node, '__class__') and right_expr_node.__class__.__name__ == 'FunctionCallNode' 
            and right_expr_node.name == 'tix_cayiman'):
            
            left_side_type = self.main_generator.semantic_checker.get_expression_type(left_expr_node, skip_context_check=True)
            
            if not isinstance(left_side_type, ArrayTypeNode):
                raise Exception("tix_cayiman can only be assigned to array types")

            if not hasattr(right_expr_node, 'params') or not right_expr_node.params or len(right_expr_node.params) < 1:
                raise ValueError(f"tix_cayiman requires at least one parameter (size)")

            size_expr = self.expr_generator.generate_expression(right_expr_node.params[0])
            element_type = left_side_type.element_type
            
            if element_type is None:
                init_c = f"tusmo_tix_mixed_create({size_expr})"
            elif isinstance(element_type, ArrayTypeNode):
                init_c = f"tusmo_tix_generic_create({size_expr})"
            else:
                element_type_str = str(element_type)
                init_c = f"tusmo_hp_tix_{element_type_str}_create({size_expr})"
            
            self.main_generator.c_code += f"    {left_c_code} = {init_c};\n"

        else:
            right_c_code = self.expr_generator.generate_expression(right_expr_node)
            left_side_type = self.main_generator.semantic_checker.get_expression_type(left_expr_node, skip_context_check=True)
            right_side_type = self.main_generator.semantic_checker.get_expression_type(right_expr_node, skip_context_check=True)

            # If assigning from dynamic_value, unwrap to the target primitive where possible
            if str(right_side_type) == "dynamic_value":
                unwrap_map = {
                    "tiro": "as_tiro",
                    "jajab": "as_jajab",
                    "eray": "as_eray",
                    "miyaa": "as_miyaa",
                    "xaraf": "as_xaraf",
                    "qaamuus": "as_qaamuus",
                    "tix": "as_tix",
                }
                member = unwrap_map.get(str(left_side_type))
                if member:
                    right_c_code = f"({right_c_code}).value.{member}"

            if str(left_side_type) == "eray" and op == "+=":
                right_c_converted = self.expr_generator._ensure_string_operand(right_c_code, right_side_type)
                self.main_generator.c_code += f"    {left_c_code} = tusmo_concat_cstr({left_c_code}, {right_c_converted});\n"
            else:
                self.main_generator.c_code += f"    {left_c_code} {op} {right_c_code};\n"
