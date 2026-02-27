# compiler/backend/transpiler/c_call_generator.py

from compiler.frontend.parser.ast_nodes import FunctionCallNode

class CCallGenerator:
    """
    Handles ___C__CALL_ calls in Tusmo.
    Maintains a registry of available C functions and their required number of arguments.
    """

    def __init__(self, code_generator):
        self.cg = code_generator  # your CCodeGenerator instance
        self.used_features = code_generator.used_features

        # Registry of available C functions
        # key = C function name as string (or identifier), value = number of parameters
        self.c_function_registry = {
            "tusmo_init_random": 0,
            "tusmo_random_int": 2,
            "tusmo_random_double": 2,
        }

    def generate_call(self, node: FunctionCallNode):
        """
        Generate C code for ___C__CALL_.
        First argument = function name
        Remaining arguments = function parameters
        """
        if node.function_name != "___C__CALL_":
            raise ValueError(f"CCallGenerator only handles ___C__CALL_, got {node.function_name}")

        if not node.arguments:
            raise ValueError("___C__CALL_ requires at least one argument: the function to call")

        # First argument: function identifier or name
        # First argument: function identifier or name
        func_node = node.arguments[0]
        if hasattr(func_node, 'value') and isinstance(func_node.value, str):
            func_name_str = func_node.value
        else:
            # Fallback: generate expression and strip quotes more carefully
            func_name = self.cg.generate_expression(func_node)
            func_name_str = func_name.strip('\'"')

        # Lookup registry
        if func_name_str not in self.c_function_registry:
            raise ValueError(f"C function '{func_name_str}' is not registered in ___C__CALL_")

        expected_args = self.c_function_registry[func_name_str]
        provided_args = node.arguments[1:]
        if len(provided_args) != expected_args:
            raise ValueError(
                f"C function '{func_name_str}' expects {expected_args} arguments, "
                f"got {len(provided_args)}"
            )

        # Generate C expressions for arguments
        args_c = [self.cg.generate_expression(arg) for arg in provided_args]
        args_str = ", ".join(args_c)

        # Track feature if it comes from runtime (arrays, random, etc.)
        if func_name_str.startswith("tusmo_hp_tix") or func_name_str.startswith("tusmo_tix_"):
            self.used_features.add("array")
        elif func_name_str.startswith("tusmo_random") or func_name_str == "tusmo_init_random":
            self.used_features.add("random")

        # Emit the call
        return f"{func_name_str}({args_str})"
