from compiler.frontend.parser.ast_nodes import ArrayTypeNode

class KeydGenerator:
    def __init__(self, main_generator, expr_generator):
        self.main_generator = main_generator
        self.symbol_table = main_generator.symbol_table
        self.expr_generator = expr_generator

    def generate(self, node):
        """Main method to generate C code for variable declarations."""
        var_name = node.var_name
        var_type = node.var_type
        value = node.value

        # Add the variable to the symbol table for the current scope
        self.symbol_table.set(var_name, var_type)

        # Handle qaamuus type
        if str(var_type) == "qaamuus":
            self.main_generator.used_features.add("dictionary")
            c_type = "TusmoQaamuus*"
            if value:
                init_c = self.expr_generator.generate_expression(value)
                self.main_generator.c_code += f"    {c_type} {var_name} = {init_c};\n"
            else:
                self.main_generator.c_code += f"    {c_type} {var_name} = tusmo_qaamuus_create();\n"
            return
        # Handle array types
        if isinstance(var_type, ArrayTypeNode):
            c_type = self.main_generator.array_generator.get_c_type_from_tusmo_type(var_type)
            if value:
                # Check if it's a tix_cayiman function call
                if (hasattr(value, '__class__') and value.__class__.__name__ == 'FunctionCallNode' 
                    and value.name == 'tix_cayiman'):
                    # Validate that the function has at least one parameter
                    if not hasattr(value, 'params') or not value.params or len(value.params) < 1:
                        raise ValueError(f"tix_cayiman requires at least one parameter (size) for variable {var_name}")
                    # Generate the appropriate create function based on the declared type
                    size_expr = self.expr_generator.generate_expression(value.params[0])
                    element_type = var_type.element_type
                    
                    if element_type is None:
                        # Mixed/heterogeneous array
                        init_c = f"tusmo_tix_mixed_create({size_expr})"
                    elif isinstance(element_type, ArrayTypeNode):
                        # Multi-dimensional array
                        init_c = f"tusmo_tix_generic_create({size_expr})"
                    else:
                        # Homogeneous array
                        element_type_str = str(element_type)
                        init_c = f"tusmo_hp_tix_{element_type_str}_create({size_expr})"
                    
                    self.main_generator.c_code += f"    {c_type} {var_name} = {init_c};\n"
                # Check if it's an array initialization
                elif hasattr(value, '__class__') and value.__class__.__name__ == 'ArrayInitializationNode':
                    # Use the declared type instead of inferred type for empty arrays
                    init_c = self.main_generator.array_generator._generate_recursive_initializer(var_type, value.elements)
                    self.main_generator.c_code += f"    {c_type} {var_name} = {init_c};\n"
                else:
                    # Other initializations
                    init_c = self.expr_generator.generate_expression(value)
                    self.main_generator.c_code += f"    {c_type} {var_name} = {init_c};\n"
            else:
                # Array without initialization - set to NULL
                self.main_generator.c_code += f"    {c_type} {var_name} = NULL;\n"
        # Handle class types
        elif isinstance(var_type, str):
            type_info = self.symbol_table.get(var_type)
            is_class = type_info and type_info[1] == 'class_definition'
            
            if is_class:
                # Class type declaration
                c_type = f"{var_type}*"
                if value:
                    init_c = self.expr_generator.generate_expression(value)
                    self.main_generator.c_code += f"    {c_type} {var_name} = {init_c};\n"
                else:
                    self.main_generator.c_code += f"    {c_type} {var_name} = NULL;\n"
            else:
                # Primitive type
                if value:
                    # Declaration with initialization
                    self.generate_declaration_only(var_name, var_type)
                    init_c = self.expr_generator.generate_expression(value)
                    # Unwrap dynamic_value if assigning from dictionaries/mixed arrays
                    right_type = self.main_generator.semantic_checker.get_expression_type(value, skip_context_check=True)
                    if str(right_type) == "dynamic_value":
                        unwrap_map = {
                            "tiro": "as_tiro",
                            "jajab": "as_jajab",
                            "eray": "as_eray",
                            "miyaa": "as_miyaa",
                            "xaraf": "as_xaraf",
                            "qaamuus": "as_qaamuus",
                            "tix": "as_tix",
                        }
                        member = unwrap_map.get(str(var_type))
                        if member:
                            init_c = f"({init_c}).value.{member}"
                    self.main_generator.c_code += f"    {var_name} = {init_c};\n"
                else:
                    # Declaration without initialization - use defaults
                    self.generate_declaration_only(var_name, var_type)
                    self.generate_default_init(var_name, var_type)

    def generate_declaration_only(self, var_name, var_type):
        """Generates only the C declaration line for a primitive variable."""
        if var_type == "tiro":
            self.main_generator.c_code += f"    int {var_name};\n"
        elif var_type == "jajab":
            self.main_generator.c_code += f"    double {var_name};\n"
        elif var_type == "xaraf":
            self.main_generator.c_code += f"    char {var_name};\n"
        elif var_type == "miyaa":
            self.main_generator.c_code += f"    bool {var_name};\n"
        elif var_type == "eray":
            self.main_generator.c_code += f"    char* {var_name};\n"
        elif var_type == "waxbo":
            self.main_generator.c_code += f"    void* {var_name};\n"

    def generate_default_init(self, var_name, var_type):
        """Generates an assignment to a default value if no initializer was provided."""
        if var_type == "tiro":
            self.main_generator.c_code += f"    {var_name} = 0;\n"
        elif var_type == "jajab":
            self.main_generator.c_code += f"    {var_name} = 0.0;\n"
        elif var_type == "xaraf":
            self.main_generator.c_code += f"    {var_name} = '\\0';\n"
        elif var_type == "miyaa":
            self.main_generator.c_code += f"    {var_name} = false;\n"
        elif var_type == "eray":
            self.main_generator.c_code += f"    {var_name} = NULL;\n"
        elif var_type == "waxbo":
            self.main_generator.c_code += f"    {var_name} = NULL;\n"
