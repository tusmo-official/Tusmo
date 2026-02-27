import sys

class HelGenerator:
    def __init__(self, main_generator):
        self.main_generator = main_generator
        self.symbol_table = main_generator.symbol_table

    def generate(self, node):
        var_name = node.identifier
        varInfo = self.symbol_table.get(var_name)
        
        if not varInfo:
            return

        
        if varInfo[1] == "eray": 
            self.main_generator.c_code += f'    {var_name} = hel_str();\n'

        
        if varInfo[1] == "tiro": 
            self.main_generator.c_code += f'    scanf("%d", &{var_name});\n'
            self.main_generator.c_code += f'    {{ int c; while((c = getchar()) != \'\\n\' && c != EOF); }}\n'

        
        if varInfo[1] == "jajab": 
            self.main_generator.c_code += f'    scanf("%lf", &{var_name});\n'
            self.main_generator.c_code += f'    {{ int c; while((c = getchar()) != \'\\n\' && c != EOF); }}\n'