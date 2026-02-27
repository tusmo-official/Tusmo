# function_generator.py (Modified)

from compiler.frontend.parser.ast_nodes import *

class FunctionGenerator:
    """
    Handles the C code generation for both standalone functions and class methods.
    """
    def __init__(self, main_generator, expr_generator):
        self.main_generator = main_generator
        self.expr_generator = expr_generator
        self.symbol_table = main_generator.symbol_table

    def generate(self, node: FunctionNode):
        """Generates a C function definition for a FunctionNode."""
        # --- NEW: Check if we are generating a method within a class context ---
        is_method = self.main_generator.current_class is not None

        # Determine the C return type. Use the main generator's mapping.
        c_return_type = self.main_generator.get_c_type(node.return_type)

        # --- NEW: Name Mangling for Methods ---
        if is_method:
            class_name = self.main_generator.current_class.name
            c_func_name = f"{class_name}_{node.name}"  # e.g., Qof_hadal
        else:
            c_func_name = node.name  # Regular function name

        # --- Build the C parameter list ---
        params_list = []
        # --- NEW: Add the implicit 'this' ('kan') parameter for methods ---
        if is_method:
            class_name = self.main_generator.current_class.name
            # The first parameter is always a pointer to the object's struct
            params_list.append(f"{class_name}* kan")

        # Add the explicit parameters from the Tusmo function definition
        for param in node.params:
            ptype = param.param_type
            pname = param.name
            if isinstance(ptype, FunctionTypeNode):
                c_param_type_str = self.main_generator.get_c_type(ptype.return_type)
                param_types = [self.main_generator.get_c_type(p) for p in ptype.param_types]
                if not param_types:
                    param_types.append("void")
                params_list.append(f"{c_param_type_str} (*{pname})({', '.join(param_types)})")
            else:
                c_param_type = self.main_generator.get_c_type(ptype)
                params_list.append(f"{c_param_type} {pname}")

        c_params = ", ".join(params_list)
        function_signature = f"{c_return_type} {c_func_name}({c_params})"

        # --- Generate the function body ---
        # We temporarily hijack the main generator's C code buffer to generate
        # the body for this function, then restore it.
        self.symbol_table.push_scope()

        # Add parameters to the symbol table for the scope of this function's body
        if is_method:
            self.symbol_table.set("kan", self.main_generator.current_class.name)
        for param in node.params:
            self.symbol_table.set(param.name, param.param_type)

        original_c_code_buffer = self.main_generator.c_code
        self.main_generator.c_code = ""  # Clear buffer for this function's body
        self.main_generator._generate_node(node.body)
        function_body_code = self.main_generator.c_code
        self.main_generator.c_code = original_c_code_buffer # Restore original buffer

        self.symbol_table.pop_scope()

        # --- Assemble and store the final function code ---
        full_function_code = f"{function_signature} {{\n{function_body_code}}}\n\n"

        # Add the complete C function to the dedicated `function_definitions` buffer
        self.main_generator.function_definitions += full_function_code