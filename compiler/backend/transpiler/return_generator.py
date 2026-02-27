
class ReturnGenerator:
    def __init__(self, main_generator, expr_generator):
        self.main_generator = main_generator
        self.expr_generator = expr_generator

    def generate(self, node):
        expression_node = node.expression
        if expression_node:
            expr_c_code = self.expr_generator.generate_expression(expression_node)
            self.main_generator.c_code += f"    return {expr_c_code};\n"
        else:
            self.main_generator.c_code += "    return;\n"