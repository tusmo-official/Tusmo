
class ConditionGenerator:
    def __init__(self, main_generator, expr_generator):
        self.main_generator = main_generator
        self.expr_generator = expr_generator
        self.symbol_table = main_generator.symbol_table

    def generate(self, node):
        is_first_case = True
        for condition, body in node.cases:
            keyword = "if" if is_first_case else "else if"
            condition_c = self.expr_generator.generate_expression(condition)
            self.main_generator.c_code += f"    {keyword} ({condition_c}) {{\n"
            self.symbol_table.push_scope()
            self.main_generator._generate_node(body)
            self.symbol_table.pop_scope()
            self.main_generator.c_code += f"    }}\n"
            is_first_case = False

        if node.else_case:
            self.main_generator.c_code += f"    else {{\n"
            self.symbol_table.push_scope()
            self.main_generator._generate_node(node.else_case)
            self.symbol_table.pop_scope()
            self.main_generator.c_code += f"    }}\n"