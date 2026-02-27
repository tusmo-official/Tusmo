# ast_nodes.py (La cusboonaysiiyay)

class ASTNode:
    """
    Fasalka aasaasiga ah ee dhammaan qodobbada AST.
    Wuxuu si toos ah u kaydiyaa lambarka safka iyo magaca faylka.
    """
    def __init__(self, line=None, filename=None):
        self.line = line
        self.filename = filename

class ExpressionNode(ASTNode):
    """Fasalka aasaasiga ah ee dhammaan 'expressions'."""
    pass

class NumberNode(ExpressionNode):
    def __init__(self, value, line=None, filename=None):
        super().__init__(line, filename)
        self.value = value

class FloatNode(ExpressionNode):
    def __init__(self, value, line=None, filename=None):
        super().__init__(line, filename)
        self.value = value

class StringNode(ExpressionNode):
    def __init__(self, value, line=None, filename=None):
        super().__init__(line, filename)
        self.value = value

class CharNode(ExpressionNode):
    def __init__(self, value, line=None, filename=None):
        super().__init__(line, filename)
        self.value = value

class IdentifierNode(ExpressionNode):
    def __init__(self, name, line=None, filename=None):
        super().__init__(line, filename)
        self.name = name

class TernaryOpNode(ExpressionNode):
    def __init__(self, condition, if_true, if_false, line=None, filename=None):
        super().__init__(line, filename)
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false

class BooleanNode(ExpressionNode):
    def __init__(self, value, line=None, filename=None):
        super().__init__(line, filename)
        self.value = value

class BinaryOpNode(ExpressionNode):
    def __init__(self, left, op, right, line=None, filename=None):
        super().__init__(line, filename)
        self.left = left
        self.op = op
        self.right = right
        self.type = "binary_op"

class FStringNode(ExpressionNode):
    def __init__(self, parts, line=None, filename=None):
        super().__init__(line, filename)
        self.parts = parts
        self.type = "fstring"

class TypeLiteralNode(ExpressionNode):
    """Represents a type used as a literal, e.g., tiro, eray, or a class name."""
    def __init__(self, type_name, line=None, filename=None):
        super().__init__(line, filename)
        self.type_name = type_name

#|-----------------------------------------------------------------|
#|                       Keyd                                      |
#|-----------------------------------------------------------------|

class KeydNode(ASTNode):
    def __init__(self, var_name, var_type, value, line, filename):
        super().__init__(line, filename)
        self.var_name = var_name
        self.var_type = var_type
        self.value = value

class AssignmentNode(ASTNode):
    def __init__(self, identifier, op, expression, line, filename):
        super().__init__(line, filename)
        self.identifier = identifier
        self.op = op
        self.expression = expression

#|-----------------------------------------------------------------|
#|                       Qor, Soo Celi, Hel                        |
#|-----------------------------------------------------------------|

class ReturnStatementNode(ASTNode):
    def __init__(self, expression, line=None, filename=None):
        super().__init__(line, filename)
        self.expression = expression

class BreakNode(ASTNode):
    """Represents the 'joog' statement (break)."""
    def __init__(self, line=None, filename=None):
        super().__init__(line, filename)

class ContinueNode(ASTNode):
    """Represents the 'kasoco' statement (continue)."""
    def __init__(self, line=None, filename=None):
        super().__init__(line, filename)

class EmbeddedCNode(ASTNode):
    """Represents an embedded C code block injected via ___c__code_()."""
    def __init__(self, code, line=None, filename=None):
        super().__init__(line, filename)
        self.code = code

class QorNode(ASTNode):
    def __init__(self, line, expressions, filename):
        super().__init__(line, filename)
        self.expressions = expressions

class HelNode(ASTNode):
    def __init__(self, line, identifier, filename):
        super().__init__(line, filename)
        self.identifier = identifier

#|-----------------------------------------------------------------|
#|                       HADDII (IF Statements)                    |
#|-----------------------------------------------------------------|
class IfNode(ASTNode):
    def __init__(self, cases, else_case=None, line=None, filename=None):
        super().__init__(line, filename)
        self.cases = cases
        self.else_case = else_case

#|-----------------------------------------------------------------|
#|                       TIX (Arrays/Lists)                        |
#|-----------------------------------------------------------------|

class ArrayTypeNode(ASTNode):
    def __init__(self, line, element_type=None, filename=None):
        super().__init__(line, filename)
        self.element_type = element_type # This can now be a string OR another ArrayTypeNode

    def __eq__(self, other):
        # This should handle recursion correctly
        return (isinstance(other, ArrayTypeNode) and
                self.element_type == other.element_type)

    def __str__(self):
        # --- MAKE THIS RECURSIVE ---
        if self.element_type:
            # Recursively call str() on the element_type
            return f"tix:{self.element_type}"
        else:
            return "tix"

class FunctionTypeNode(ASTNode):
    def __init__(self, line, param_types, return_type, filename=None):
        super().__init__(line, filename)
        self.param_types = param_types
        self.return_type = return_type

    def __eq__(self, other):
        return (isinstance(other, FunctionTypeNode) and
                self.param_types == other.param_types and
                self.return_type == other.return_type)

    def __str__(self):
        param_str = ', '.join(map(str, self.param_types))
        return f"hawl({param_str}):{self.return_type}"

class ArrayInitializationNode(ExpressionNode):
    def __init__(self, line, elements, filename):
        super().__init__(line, filename)
        self.elements = elements

class ArrayAccessNode(ExpressionNode):
    def __init__(self, line, array_name_node, index_expression, filename):
        super().__init__(line, filename)
        self.array_name_node = array_name_node
        self.index_expression = index_expression

class ArrayTypeQueryNode(ExpressionNode):
    """Represents the special nooc(arr[]) syntax to ask for an array's element type."""
    def __init__(self, line, identifier, filename):
        super().__init__(line, filename)
        self.identifier = identifier

class ArrayAssignmentNode(ASTNode):
    def __init__(self, line, array_access_node, value_expression, filename):
        super().__init__(line, filename)
        self.array_access_node = array_access_node
        self.value_expression = value_expression

#|-----------------------------------------------------------------|
#|                       HAWL/SHAQO (Function Declarations)        |
#|-----------------------------------------------------------------|
class FunctionNode(ASTNode):
    def __init__(self, return_type, name, params, body, line, filename):
        super().__init__(line, filename)
        self.return_type = return_type
        self.name = name
        self.params = params
        self.body = body
        self.docstring = None

class ParameterNode(ASTNode):
    def __init__(self, name, param_type, default_value=None, line=None, filename=None):
        super().__init__(line, filename)
        self.name = name
        self.param_type = param_type
        self.default_value = default_value

# Represents a named argument in a call, e.g., fn(x=1)
class NamedArgument(ASTNode):
    def __init__(self, name, value, line=None, filename=None):
        super().__init__(line, filename)
        self.name = name
        self.value = value

#|-----------------------------------------------------------------|
#|                       Function Call                             |
#|-----------------------------------------------------------------|
class FunctionCallNode(ExpressionNode):
    def __init__(self, name, params, line, filename):
        super().__init__(line, filename)
        self.name = name
        self.params = params
        # Will be set by the semantic checker when keyword args are resolved.
        self.ordered_args = None

#|-----------------------------------------------------------------|
#|                       LOOPS                                     |
#|-----------------------------------------------------------------|

class WhileNode(ASTNode):
    def __init__(self, line, condition, body, filename):
        super().__init__(line, filename)
        self.condition = condition
        self.body = body

class DoWhileNode(ASTNode):
    def __init__(self, line, body, condition, filename):
        super().__init__(line, filename)
        self.body = body
        self.condition = condition

class ForRangeNode(ASTNode):
    def __init__(self, line, iterator_var_name, start_expr, end_expr, body, filename):
        super().__init__(line, filename)
        self.iterator_var_name = iterator_var_name
        self.start_expr = start_expr
        self.end_expr = end_expr
        self.body = body

class ForEachNode(ASTNode):
    def __init__(self, line, iterator_var_name, array_expr, body, filename):
        super().__init__(line, filename)
        self.iterator_var_name = iterator_var_name
        self.array_expr = array_expr
        self.body = body

class MethodCallNode(ExpressionNode):
    def __init__(self, line, object_node, method_name, args_list, filename):
        super().__init__(line, filename)
        self.object_node = object_node
        self.method_name = method_name
        self.args_list = args_list
        self.ordered_args = None

class KeenNode(ASTNode):
    def __init__(self, line, filename_to_import, source_filename):
        # Kaydi meesha 'keen' lagu qoray
        super().__init__(line, source_filename)
        # Kaydi faylka la soo dejinayo
        self.filename = filename_to_import

    def __str__(self):
        return f"keen: {self.filename}"

#|-----------------------------------------------------------------|
#|                 KOOX (Class related nodes)                      |
#|-----------------------------------------------------------------|

class ClassNode(ASTNode):
    """Represents a class definition with its members and methods."""
    def __init__(self, name, members, methods, line, filename, parent_name=None):
        super().__init__(line, filename)
        self.name = name
        self.members = members
        self.methods = methods
        self.docstring = None
        self.parent_name = parent_name # The name of the parent class, if any

class ClassInstantiationNode(ExpressionNode):
    """Represents creating a new instance of a class, e.g., Qof(...) cusub."""
    def __init__(self, class_name, constructor_args, line, filename):
        super().__init__(line, filename)
        self.class_name = class_name
        self.constructor_args = constructor_args
        self.ordered_args = None

class MemberAccessNode(ExpressionNode):
    """Represents accessing a member of an object, e.g., qof1.magac."""
    def __init__(self, object_node, member_name, line, filename):
        super().__init__(line, filename)
        self.object_node = object_node
        self.member_name = member_name

class ThisNode(ExpressionNode):
    """Represents the 'kan' keyword inside a method."""
    def __init__(self, line, filename):
        super().__init__(line, filename)

class WaalidNode(ExpressionNode):
    """Represents the 'waalid' keyword for parent access."""
    def __init__(self, line, filename):
        super().__init__(line, filename)


class CCallNode(ExpressionNode):
    def __init__(self, c_function_name, args, line, filename):
        super().__init__(line, filename)
        self.c_function_name = c_function_name
        self.args = args

    def __repr__(self):
        return f"CCallNode({self.c_function_name}, {self.args})"


#|-----------------------------------------------------------------|
#|                 QAAMUUS (Dictionary related nodes)              |
#|-----------------------------------------------------------------|

class DictionaryInitializationNode(ExpressionNode):
    """Represents a dictionary literal, e.g., {"magac": "Ali", "da": 25}."""
    def __init__(self, line, pairs, filename):
        super().__init__(line, filename)
        self.pairs = pairs

class DictionaryAccessNode(ExpressionNode):
    """Represents accessing a dictionary's value, e.g., my_dict["key"]."""
    def __init__(self, line, dictionary_node, key_node, filename):
        super().__init__(line, filename)
        self.dictionary_node = dictionary_node
        self.key_node = key_node

class DictionaryAssignmentNode(ASTNode):
    """Represents assigning a value to a dictionary key, e.g., my_dict["key"] = value."""
    def __init__(self, line, dictionary_access_node, value_node, filename):
        super().__init__(line, filename)
        self.dictionary_access_node = dictionary_access_node
        self.value_node = value_node
