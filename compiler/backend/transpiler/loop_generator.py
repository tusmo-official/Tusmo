from compiler.frontend.parser.ast_nodes import (
    WhileNode, DoWhileNode, ForRangeNode, ForEachNode, ArrayTypeNode
)

class LoopGenerator:
    def __init__(self, main_generator, expr_generator):
        self.main_generator = main_generator
        self.expr_generator = expr_generator
        self.symbol_table = main_generator.symbol_table

    def generate_while(self, node: WhileNode):
        condition_c = self.expr_generator.generate_expression(node.condition)
        self.main_generator.c_code += f"    while ({condition_c}) {{\n"
        self.symbol_table.push_scope()
        self.main_generator._generate_node(node.body)
        self.symbol_table.pop_scope()
        self.main_generator.c_code += f"    }}\n"

    def generate_do_while(self, node: DoWhileNode):
        self.main_generator.c_code += f"    do {{\n"
        self.symbol_table.push_scope()
        self.main_generator._generate_node(node.body)
        self.symbol_table.pop_scope()
        condition_c = self.expr_generator.generate_expression(node.condition)
        self.main_generator.c_code += f"    }} while ({condition_c});\n"

    def generate_for_range(self, node: ForRangeNode):
        iterator = node.iterator_var_name
        start_c = self.expr_generator.generate_expression(node.start_expr)
        end_c = self.expr_generator.generate_expression(node.end_expr)
        
        self.symbol_table.push_scope()
        self.symbol_table.set(iterator, 'tiro')

        self.main_generator.c_code += f"    for (int {iterator} = {start_c}; {iterator} < {end_c}; ++{iterator}) {{\n"
        self.main_generator._generate_node(node.body)
        self.main_generator.c_code += f"    }}\n"

        self.symbol_table.pop_scope()

    def generate_for_each(self, node: ForEachNode):
        item_var = node.iterator_var_name
        array_c = self.expr_generator.generate_expression(node.array_expr)
        array_type = self.expr_generator.get_expression_type(node.array_expr)

        self.symbol_table.push_scope()

        if str(array_type) == 'eray':
            length_var = self.main_generator.get_temp_var()
            self.main_generator.c_code += f"    int {length_var} = strlen({array_c});\n"
            index_var = self.main_generator.get_temp_var()
            self.main_generator.c_code += f"    for (int {index_var} = 0; {index_var} < {length_var}; ++{index_var}) {{\n"
            self.symbol_table.set(item_var, 'xaraf')
            self.main_generator.c_code += f"        char {item_var} = {array_c}[{index_var}];\n"
            self.main_generator._generate_node(node.body)
            self.main_generator.c_code += "    }\n"

        else: # It's a Tusmo array type
            index_var = self.main_generator.get_temp_var() + "_i"
            self.main_generator.c_code += f"    for (size_t {index_var} = 0; {index_var} < {array_c}->size; ++{index_var}) {{\n"
            
            element_tusmo_type = array_type.element_type
            
            if element_tusmo_type is None:
                iterator_c_type = "TusmoValue"
                self.symbol_table.set(item_var, 'dynamic_value')
                self.main_generator.c_code += f"        {iterator_c_type} {item_var} = {array_c}->data[{index_var}];\n"
            
            elif isinstance(element_tusmo_type, ArrayTypeNode):
                iterator_c_type = self.main_generator.array_generator.get_c_type_from_tusmo_type(element_tusmo_type)
                self.symbol_table.set(item_var, element_tusmo_type)
                self.main_generator.c_code += f"        {iterator_c_type} {item_var} = ({iterator_c_type})({array_c}->data[{index_var}]);\n"

            else:
                iterator_c_type = self.main_generator.array_generator.get_c_type_map().get(str(element_tusmo_type))
                self.symbol_table.set(item_var, str(element_tusmo_type))
                self.main_generator.c_code += f"        {iterator_c_type} {item_var} = {array_c}->data[{index_var}];\n"

            self.main_generator._generate_node(node.body)
            self.main_generator.c_code += f"    }}\n"

        self.symbol_table.pop_scope()