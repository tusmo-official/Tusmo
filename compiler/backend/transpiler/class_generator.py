# compiler/backend/transpiler/class_generator.py

from compiler.frontend.parser.ast_nodes import ClassNode

class ClassGenerator:
    """
    Handles the C code generation for Tusmo class definitions.
    """
    def __init__(self, main_generator):
        self.main_generator = main_generator
        # Shortcut to the function generator, which we will use to generate methods
        self.function_generator = main_generator.function_generator

    def generate(self, node: ClassNode):
        """
        Orchestrates the generation of all parts of a class.
        """
        # 1. Generate the C struct definition (e.g., struct Qof { ... };)
        # This code is added to the `class_definitions` buffer.
        self._generate_struct_definition(node)

        # 2. Set the context to the current class. This is crucial for the
        # function generator to know it's generating a method, not a regular function.
        self.main_generator.current_class = node
        for method in node.methods:
            # 3. Generate each method (e.g., Qof_hadal(Qof* kan)).
            # This reuses the existing function generator.
            self.function_generator.generate(method)
        # 4. Unset the context after all methods are generated.
        self.main_generator.current_class = None

        # 5. Generate the hidden creator function (e.g., Qof* _create_Qof(...)).
        # This function is what gets called when you use `cusub`.
        self._generate_class_creator(node)

    def _generate_struct_definition(self, node: ClassNode):
        """Generates the C struct for the class and adds it to the definitions buffer."""
        class_name = node.name
        # Forward declare the struct to allow self-referential pointers if needed later
        struct_def = f"typedef struct {class_name} {class_name};\n"
        struct_def += f"struct {class_name} {{\n"

        if node.parent_name:
            # Inheritance: Embed parent struct as the FIRST member
            # This allows (Child*) -> (Parent*) casting safely in C.
            # We name the field 'parent' for explicit access, though implicit casting works via pointer.
            struct_def += f"    {node.parent_name} parent;\n"

        for member in node.members:
            # Get the corresponding C type for the member variable
            member_c_type = self.main_generator.get_c_type(member.var_type)
            struct_def += f"    {member_c_type} {member.var_name};\n"

        struct_def += f"}};\n\n"

        # Add the complete struct definition to the dedicated buffer in the main generator
        self.main_generator.class_definitions += struct_def

    def _generate_class_creator(self, node: ClassNode):
        """
        Generates the C function that allocates and initializes a new class instance.
        Example: Qof* _create_Qof(char* m, int d) { ... }
        """
        class_name = node.name
        creator_func_name = f"_create_{class_name}"

        # Find the constructor ('dhis') method, if it exists
        constructor = next((m for m in node.methods if m.name == 'dhis'), None)

        # Build the parameter list for the creator function from the constructor's parameters
        params_list = []
        if constructor:
            for param in constructor.params:
                c_param_type = self.main_generator.get_c_type(param.param_type)
                params_list.append(f"{c_param_type} {param.name}")
        c_params = ", ".join(params_list)

        # --- Generate the body of the creator function ---
        creator_body = ""
        # 1. Allocate memory for the object using the garbage collector
        creator_body += f"    {class_name}* kan = GC_MALLOC(sizeof({class_name}));\n"

        # 2. If a constructor exists, call it
        if constructor:
            # The mangled name for the method is ClassName_MethodName
            constructor_c_name = f"{class_name}_{constructor.name}"
            # The first argument to the method is always 'kan' (this), followed by others
            args_list = ["kan"] + [param.name for param in constructor.params]
            c_args = ", ".join(args_list)
            creator_body += f"    {constructor_c_name}({c_args});\n"

        # 3. Return the newly created object pointer
        creator_body += "    return kan;\n"

        # Assemble the full creator function
        creator_function = (
            f"{class_name}* {creator_func_name}({c_params}) {{\n"
            f"{creator_body}"
            f"}}\n\n"
        )

        # Add the creator function to the global function definitions buffer
        self.main_generator.function_definitions += creator_function