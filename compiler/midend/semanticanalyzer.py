# semanticanalyzer.py (Final Clean Version)

from compiler.frontend.parser.ast_nodes import (

    KeydNode, AssignmentNode, IdentifierNode, FunctionNode, FunctionCallNode,

    IfNode, QorNode, HelNode, ReturnStatementNode, BinaryOpNode, NumberNode,

    StringNode, FloatNode, CharNode, BooleanNode, FStringNode, TernaryOpNode, ASTNode,

    ArrayTypeNode, ArrayInitializationNode, ArrayAccessNode, ArrayAssignmentNode, ArrayTypeQueryNode,

    WhileNode, DoWhileNode, ForRangeNode, ForEachNode, MethodCallNode,

    ClassNode, ClassInstantiationNode, MemberAccessNode, ThisNode, CCallNode, WaalidNode,

    DictionaryInitializationNode, DictionaryAccessNode, DictionaryAssignmentNode,

    FunctionTypeNode, ParameterNode, BreakNode, ContinueNode, NamedArgument, TypeLiteralNode
)

from compiler.midend.symbol_table import SymbolTable

from compiler.midend.built_in_fn import functions_



class SemanticError(Exception):

    pass



class SemanticChecker:

    def __init__(self, symbol_table: SymbolTable):

        self.symbol_table = symbol_table

        self.current_function = None

        self.current_class = None

        self.loop_depth = 0



    def _are_types_compatible(self, declared_type, value_type):
        if declared_type is None: return True

        if isinstance(declared_type, ASTNode) and not isinstance(declared_type, FunctionTypeNode):
            declared_type = str(declared_type)

        if isinstance(value_type, ASTNode) and not isinstance(value_type, FunctionTypeNode):
            value_type = str(value_type)

        if declared_type == value_type:
            return True

        if isinstance(declared_type, str) and isinstance(value_type, str):
            if declared_type == 'dynamic_value' or value_type == 'dynamic_value':
                return True
            
            if declared_type == 'None': # Mixed array
                return True

            if declared_type.startswith("tix:") and value_type == 'tix':
                return True

            if declared_type == 'tix' and value_type.startswith("tix:"):
                return True

            if declared_type == 'qaamuus' and value_type == 'qaamuus':
                return True
            if declared_type == 'hawl' and value_type == 'hawl':
                return True

        if isinstance(declared_type, FunctionTypeNode) and isinstance(value_type, FunctionTypeNode):
            if len(declared_type.param_types) != len(value_type.param_types):
                return False
            return all(self._are_types_compatible(dt, vt) for dt, vt in zip(declared_type.param_types, value_type.param_types)) and self._are_types_compatible(declared_type.return_type, value_type.return_type)
        if isinstance(declared_type, FunctionTypeNode) and value_type == 'hawl': return True
        if declared_type == 'hawl' and isinstance(value_type, FunctionTypeNode): return True


        return False

    def _resolve_call_arguments(self, args, params, call_node, context="call"):
        """
        Reorder positional/keyword args to match parameter order and fill defaults.
        Returns ordered list and sets call_node.ordered_args.
        """
        param_index = {p.name: idx for idx, p in enumerate(params)}
        ordered = [None] * len(params)
        provided = [False] * len(params)
        next_pos = 0
        seen_named = False

        for arg in args:
            if isinstance(arg, NamedArgument):
                seen_named = True
                if arg.name not in param_index:
                    raise SemanticError(f"Cilad Macne: Magac halbeeg aan la aqoon '{arg.name}' loogu isticmaalay {context}.\n\t\tFaylka: '{arg.filename}', Sadarka: {arg.line}")
                idx = param_index[arg.name]
                if provided[idx]:
                    raise SemanticError(f"Cilad Macne: Halbeeg '{arg.name}' waxaa la siiyay laba jeer {context}.\n\t\tFaylka: '{arg.filename}', Sadarka: {arg.line}")
                ordered[idx] = arg.value
                provided[idx] = True
            else:
                if seen_named:
                    raise SemanticError(f"Cilad Macne: Halbeegyada meeleysan lama dhigi karo kadib kuwa magac leh {context}.\n\t\tFaylka: '{getattr(arg, 'filename', call_node.filename)}', Sadarka: {getattr(arg, 'line', call_node.line)}")
                if next_pos >= len(params):
                    raise SemanticError(f"Cilad Tirada: {context} wuxuu helay halbeegyo ka badan intii la rabay.\n\t\tFaylka: '{call_node.filename}', Sadarka: {call_node.line}")
                ordered[next_pos] = arg
                provided[next_pos] = True
                next_pos += 1

        for i, p in enumerate(params):
            if not provided[i]:
                if p.default_value is not None:
                    ordered[i] = p.default_value
                else:
                    raise SemanticError(f"Cilad Tirada: Halbeeg '{p.name}' ayaa ka maqan {context} ee '{getattr(call_node, 'name', getattr(call_node, 'method_name', ''))}'.\n\t\tFaylka: '{call_node.filename}', Sadarka: {call_node.line}")

        call_node.ordered_args = ordered
        return ordered



    def check(self, node):

        if node is None: return

        if isinstance(node, list):

            for item in node: self.check(item)

            return

        method_name = f"check_{type(node).__name__}"

        method = getattr(self, method_name, self.generic_check)

        return method(node)



    def generic_check(self, node):

        for attr_name in dir(node):

            if not attr_name.startswith("__"):

                value = getattr(node, attr_name)

                if isinstance(value, list):

                    for item in value:

                        if isinstance(item, ASTNode): self.check(item)

                elif isinstance(value, ASTNode): self.check(value)



    def get_expression_type(self, node: ASTNode, skip_context_check=False):

        """

        Get the type of an expression node.

        

        Args:

            node: The AST node to get the type of

            skip_context_check: If True, skip validation checks (used during code generation)

        """

        if not isinstance(node, ASTNode):

             raise SemanticError(f"Cilad Gudaha ah: get_expression_type waxaa la siiyay wax aan ASTNode ahayn: {type(node).__name__}")

        if isinstance(node, NumberNode): return "tiro"

        if isinstance(node, FloatNode): return "jajab"

        if isinstance(node, StringNode): return "eray"

        if isinstance(node, CharNode): return "xaraf"

        if isinstance(node, BooleanNode): return "miyaa"
        if isinstance(node, NamedArgument): return self.get_expression_type(node.value, skip_context_check)

        if isinstance(node, FStringNode):
            return "eray"

        if isinstance(node, TypeLiteralNode):
            return f"nooc:{node.type_name}"

        if isinstance(node, DictionaryInitializationNode): return "qaamuus"
        
        if isinstance(node, WaalidNode):
            if self.current_class and self.current_class.parent_name:
                return self.current_class.parent_name
            return None

        if isinstance(node, ThisNode):
            if not skip_context_check and not self.current_class:
                raise SemanticError(f"Cilad Macne: 'kan' waxaa la isticmaali karaa oo kaliya marka lagu jiro hawl kooxeed (method).\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
            # During code generation, try to look up 'kan' in the symbol table
            if skip_context_check:
                kan_info = self.symbol_table.get('kan')

                if kan_info:

                    return kan_info[1]  # Return the type of 'kan'

            return self.current_class.name if self.current_class else None

        if isinstance(node, IdentifierNode):

            var_info = self.symbol_table.get(node.name)

            if not skip_context_check and not var_info:

                raise SemanticError(f"Cilad Macne: Doorsoomaha '{node.name}' lama helin.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

            return var_info[1] if var_info else None

        if isinstance(node, ArrayTypeQueryNode):
            var_info = self.symbol_table.get(node.identifier)
            if not skip_context_check and (not var_info or not isinstance(var_info[1], ArrayTypeNode)):
                raise SemanticError(f"Cilad Nooca Xogta: '{node.identifier}' maaha tix sidaa darteed looma isticmaali karo 'nooc(arr[])'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
            return var_info[1] if var_info else None

        if isinstance(node, ClassInstantiationNode):

            class_info = self.symbol_table.get(node.class_name)

            if not skip_context_check and (not class_info or class_info[1] != 'class_definition'):

                raise SemanticError(f"Cilad Macne: Kooxda (class) '{node.class_name}' lama yaqaan.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

            return node.class_name

        if isinstance(node, MemberAccessNode):

            object_type_name = str(self.get_expression_type(node.object_node, skip_context_check))

            # If we couldn't determine the object type during code generation,

            # it might be 'kan' (ThisNode) - try to infer from the identifier lookup

            if not object_type_name or object_type_name == 'None':

                # Check if the object_node is an IdentifierNode and look it up

                if isinstance(node.object_node, IdentifierNode):

                    var_info = self.symbol_table.get(node.object_node.name)

                    if var_info:

                        object_type_name = str(var_info[1])

            

            if not object_type_name or object_type_name == 'None':

                return None

                

            class_info = self.symbol_table.get(object_type_name)

            if not skip_context_check and (not class_info or not isinstance(class_info[0], ClassNode)):

                raise SemanticError(f"Cilad Nooca Xogta: Isku day inaad gasho xubin ka mid ah '{object_type_name}' oo aan ahayn koox (class).\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

            if not class_info:

                return None

            class_node = class_info[0]
            current_class = class_node
            
            while current_class:
                member = next((m for m in current_class.members if m.var_name == node.member_name), None)
                if member:
                    return member.var_type
                
                if getattr(current_class, 'parent_class', None):
                    current_class = current_class.parent_class
                else:
                    break

            if not skip_context_check:
                raise SemanticError(f"Cilad Macne: Kooxda '{object_type_name}' malaha xubin la yiraahdo '{node.member_name}'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

            return None


        if isinstance(node, MethodCallNode):
            object_type = self.get_expression_type(node.object_node, skip_context_check)
            
            if isinstance(object_type, ArrayTypeNode):
                if node.method_name == 'gali':
                    if len(node.args_list) == 1:
                        # Append: gali(value)
                        arg_type = self.get_expression_type(node.args_list[0])
                        if not self._are_types_compatible(object_type.element_type, arg_type):
                             raise SemanticError(f"Cilad Nooca Xogta: Hawsha 'gali' waxay rabtaa '{object_type.element_type}', laakiin waxaa la siiyay '{arg_type}'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
                    elif len(node.args_list) == 2:
                        # Insert: gali(boos=i, value)
                        # Check first arg is named 'boos'
                        first_arg = node.args_list[0]
                        if not isinstance(first_arg, NamedArgument) or first_arg.name != 'boos':
                             raise SemanticError(f"Cilad Syntax: Halbeega koowaad ee 'gali' marka la isticmaalayo laba halbeeg waa inuu ahaadaa 'boos'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
                        
                        index_type = self.get_expression_type(first_arg.value)
                        if str(index_type) != 'tiro':
                             raise SemanticError(f"Cilad Nooca Xogta: 'boos' waa inuu ahaadaa 'tiro'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
                        
                        val_type = self.get_expression_type(node.args_list[1])
                        if not self._are_types_compatible(object_type.element_type, val_type):
                             raise SemanticError(f"Cilad Nooca Xogta: Qiimaha la gelinayo waa inuu ahaadaa '{object_type.element_type}', laakiin waa '{val_type}'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
                    else:
                        raise SemanticError(f"Cilad Tirada: Hawsha 'gali' waxay rabtaa 1 ama 2 halbeeg.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
                    return 'waxbo'

                elif node.method_name == 'kasaar':
                    if len(node.args_list) != 1:
                        raise SemanticError(f"Cilad Tirada: Hawsha 'kasaar' waxay rabtaa 1 halbeeg.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
                    
                    arg = node.args_list[0]
                    if isinstance(arg, NamedArgument) and arg.name == 'boos':
                        # Remove by index: kasaar(boos=i)
                        index_type = self.get_expression_type(arg.value)
                        if str(index_type) != 'tiro':
                             raise SemanticError(f"Cilad Nooca Xogta: 'boos' waa inuu ahaadaa 'tiro'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
                        return object_type.element_type
                    else:
                        # Remove by value: kasaar(value)
                        val_type = self.get_expression_type(arg)
                        if not self._are_types_compatible(object_type.element_type, val_type):
                             raise SemanticError(f"Cilad Nooca Xogta: Qiimaha la saarayo waa inuu ahaadaa '{object_type.element_type}', laakiin waa '{val_type}'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
                        return 'miyaa'

                elif not skip_context_check:
                    raise SemanticError(f"Cilad: Ma jiro hawl la yiraahdo '{node.method_name}' oo saaran tix.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

            if str(object_type) == 'qaamuus':
                if node.method_name == 'kasaar': return 'waxbo'
                if node.method_name == 'majiraa': return 'miyaa'
                return None

            class_info = self.symbol_table.get(str(object_type))
            if not class_info: return None
            
            class_node = class_info[0]
            for method in class_node.methods:
                if method.name == node.method_name:
                    return method.return_type
            return None
        if isinstance(node, ArrayAccessNode):

            base_type = self.get_expression_type(node.array_name_node, skip_context_check)

            if not skip_context_check and not isinstance(base_type, ArrayTypeNode) and str(base_type) != 'eray' and str(base_type) != 'qaamuus':

                raise SemanticError(f"Cilad Nooca Xogta: Isku day inaad u isticmaasho wax sidii tix, laakiin maaha.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

            if isinstance(base_type, ArrayTypeNode):

                # If the array holds dictionaries or is mixed, access returns a dynamic value

                if base_type.element_type is None or str(base_type.element_type) == 'qaamuus':

                    return "dynamic_value"

                return base_type.element_type

            if str(base_type) == 'eray':

                return 'xaraf'

            if str(base_type) == 'qaamuus':
                return "dynamic_value"

            return None

        if isinstance(node, DictionaryAccessNode):

            base_type = self.get_expression_type(node.dictionary_node, skip_context_check)

            if not skip_context_check and str(base_type) != 'qaamuus':

                raise SemanticError(f"Cilad Nooca Xogta: Isku day inaad u isticmaasho wax sidii qaamuus, laakiin maaha.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

            return "dynamic_value" # Dictionaries hold dynamic values

        if isinstance(node, ArrayInitializationNode):

            if not node.elements:

                return ArrayTypeNode(line=node.line, element_type=None, filename=node.filename)

            

            # Check if all elements have the same type

            first_element_type = self.get_expression_type(node.elements[0], skip_context_check)

            is_homogeneous = True

            

            for elem in node.elements[1:]:

                elem_type = self.get_expression_type(elem, skip_context_check)

                if str(elem_type) != str(first_element_type):

                    is_homogeneous = False

                    break

            

            if is_homogeneous:

                # All elements have the same type - homogeneous array

                return ArrayTypeNode(line=node.line, element_type=first_element_type, filename=node.filename)

            else:

                # Elements have different types - heterogeneous/mixed array

                return ArrayTypeNode(line=node.line, element_type=None, filename=node.filename)

        if isinstance(node, BinaryOpNode):

            op = node.op
            left_type = self.get_expression_type(node.left, skip_context_check)
            right_type = self.get_expression_type(node.right, skip_context_check)

            if op in ('>', '<', '>=', '<=', '==', '!=', 'iyo', 'ama', '&&', '||'):
                # Allow type comparison for == and !=
                if op in ('==', '!=') and (str(left_type).startswith("nooc:") or str(right_type).startswith("nooc:")):
                    return "miyaa"
                return "miyaa"

            if op == '+' and ('eray' in (str(left_type), str(right_type))): return 'eray'

            return left_type

        if isinstance(node, FunctionCallNode):

            if node.name == 'tix_cayiman':

                return ArrayTypeNode(line=node.line, element_type=None, filename=node.filename)



            func_info = self.symbol_table.get(node.name)

        

            # Check if it's a built-in function

            is_builtin = node.name in functions_

        

            if not skip_context_check and (not func_info or (func_info[1] != 'hawl' and not isinstance(func_info[1], FunctionTypeNode))) and not is_builtin:

                raise SemanticError(

                    f"Cilad Macne: Hawsha '{node.name}' lama helin ama maaha hawl.\n"

                    f"\t\tFaylka: '{node.filename}', Sadarka: {node.line}"

                )

        

            # Return type from symbol table for user-defined functions

            if func_info:
                if isinstance(func_info[1], FunctionTypeNode):
                    return func_info[1].return_type
                else: # 'hawl'
                    return func_info[2]

        

            # Return type from built-in functions registry

            if is_builtin:

                return_type = functions_[node.name].get('return_type')

                if return_type:

                    return return_type



            return None

        if isinstance(node, TernaryOpNode):

            return self.get_expression_type(node.if_true, skip_context_check)

        if isinstance(node, CCallNode):
            # No hardcoded mappings - all types defined in stdlib wrappers!
            if node.c_function_name == "tusmo_qaamuus_has_key":
                return "miyaa"
            if self.current_function:
                return self.current_function.return_type
            return "dynamic_value"

        if not skip_context_check:

            raise SemanticError(f"Lama garanayo nooca expression-ka: {type(node).__name__} faylka {getattr(node, 'filename', 'unknown')} sadarka {getattr(node, 'line', 'unknown')}")

        return None



    def check_ClassNode(self, node: ClassNode):

        if self.symbol_table.exists_in_current_scope(node.name):
            raise SemanticError(f"Cilad Macne: Kooxda '{node.name}' hore ayaa loo qeexay.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        self.symbol_table.set(node.name, 'class_definition', value=node)
        
        # Inheritance Logic
        if node.parent_name:
            parent_info = self.symbol_table.get(node.parent_name)
            if not parent_info or parent_info[1] != 'class_definition':
                 raise SemanticError(f"Cilad Macne: Kooxda '{node.name}' waxay dhaxlaysaa '{node.parent_name}' oo aan la aqoon ama aan ahayn koox.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
            
            parent_node = parent_info[0]
            node.parent_class = parent_node # Link to AST
            
            # 1. Cycle Detection
            current = parent_node
            while getattr(current, 'parent_name', None):
                if current.parent_name == node.name:
                    raise SemanticError(f"Cilad Macne: Wareeg dhaxalka ah (Inheritance Cycle) ayaa laga helay '{node.name}' iyo '{parent_node.name}'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
                
                 # Look up grand-parent
                grand_parent_info = self.symbol_table.get(current.parent_name)
                if grand_parent_info and grand_parent_info[1] == 'class_definition':
                    current = grand_parent_info[0]
                else:
                    break
        else:
             node.parent_class = None



        previous_class = self.current_class

        self.current_class = node

        self.symbol_table.push_scope()



        for member in node.members:

            self.check(member)

        for method in node.methods:

            self.check(method)



        self.symbol_table.pop_scope()

        self.current_class = previous_class



    def check_ClassInstantiationNode(self, node: ClassInstantiationNode):

        class_info = self.symbol_table.get(node.class_name)

        if not class_info or class_info[1] != 'class_definition':

            raise SemanticError(f"Cilad Macne: Isku day inaad abuurto shay ka yimid '{node.class_name}' oo aan ahayn koox.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        class_node = class_info[0]

        constructor = next((m for m in class_node.methods if m.name == 'dhis'), None)

        if not constructor and node.constructor_args:
            raise SemanticError(f"Cilad Tirada: Kooxda '{node.class_name}' ma laha dhise laakiin waxaa la siiyay {len(node.constructor_args)} halbeeg.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        if constructor:

            node.constructor_args = self._resolve_call_arguments(node.constructor_args, constructor.params, node, context="constructor")

            for i, arg_node in enumerate(node.constructor_args):

                arg_type = self.get_expression_type(arg_node)

                param_def = constructor.params[i]
                if isinstance(param_def, ParameterNode):
                    param_type = param_def.param_type
                else:
                    param_type = param_def[1]

                if not self._are_types_compatible(param_type, arg_type):

                    raise SemanticError(f"Cilad Nooca Xogta: Qaybta {i+1} ee dhisaha '{node.class_name}' waa inay noqotaa '{param_type}', laakiin la siiyay '{arg_type}'.\n\t\tFaylka: '{arg_node.filename}', Sadarka: {node.line}")

        self.check(node.constructor_args)



    def check_KeydNode(self, node: KeydNode):

        if self.symbol_table.exists_in_current_scope(node.var_name):

            raise SemanticError(f"Cilad Macne: Doorsoomaha '{node.var_name}' hore ayaa loogu qeexay.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        if isinstance(node.var_type, str):

            type_info = self.symbol_table.get(node.var_type)

            is_primitive = node.var_type in ['tiro', 'eray', 'jajab', 'miyaa', 'xaraf', 'waxbo', 'qaamuus']

            is_known_class = type_info and type_info[1] == 'class_definition'

            if not is_primitive and not is_known_class:

                 raise SemanticError(f"Cilad Macne: Nooca xogta '{node.var_type}' lama yaqaan.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        if node.value:

            value_type = self.get_expression_type(node.value)

            if not self._are_types_compatible(node.var_type, value_type):

                 raise SemanticError(f"Cilad Nooca Xogta: Lama siin karo doorsoome noociisu yahay '{str(node.var_type)}' qiime noociisu yahay '{str(value_type)}'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        self.symbol_table.set(node.var_name, node.var_type, value=node.value)



    def check_AssignmentNode(self, node: AssignmentNode):

        assign_target_node = node.identifier

        if not isinstance(assign_target_node, (IdentifierNode, MemberAccessNode, ArrayAccessNode)):

            raise SemanticError(f"Cilad Macne: Qiime lama gelin karo dhinaca bidix ee calaamada '='.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        declared_type = self.get_expression_type(assign_target_node)

        value_type = self.get_expression_type(node.expression)

        if not self._are_types_compatible(declared_type, value_type):

            raise SemanticError(f"Cilad Nooca Xogta: Lama siin karo doorsoome/xubin noociisu yahay '{str(declared_type)}' qiime noociisu yahay '{str(value_type)}'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        self.check(assign_target_node)

        self.check(node.expression)



    def check_FunctionNode(self, node: FunctionNode):
        is_method = self.current_class is not None

        if is_method:
            if self.symbol_table.exists_in_current_scope(node.name):
                raise SemanticError(f"Cilad Macne: Hawsha '{node.name}' hore ayaa loogu qeexay kooxdan dhexdeeda.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
            self.symbol_table.set(node.name, "hawl", value=node, return_type=node.return_type)
        else:
            if self.symbol_table.exists_in_global_scope(node.name):
                raise SemanticError(f"Cilad Macne: Hawsha '{node.name}' horey ayaa loo qeexay.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")
            self.symbol_table.set_global(node.name, "hawl", value=node, return_type=node.return_type)

        previous_function = self.current_function
        self.current_function = node
        self.symbol_table.push_scope()

        if is_method:
            self.symbol_table.set("kan", self.current_class.name)

        has_default = False
        for param in node.params:
            if param.default_value:
                has_default = True
                # Check the type of the default value
                default_value_type = self.get_expression_type(param.default_value)
                if not self._are_types_compatible(param.param_type, default_value_type):
                    raise SemanticError(f"Cilad Nooca Xogta: Qiimaha caadiga ah ee '{param.name}' waa inuu noqdaa '{param.param_type}', laakiin waa '{default_value_type}'.\n\t\tFaylka: '{node.filename}', Sadarka: {param.line}")
            elif has_default:
                raise SemanticError(f"Cilad Syntax: Halbeega aan lahayn qiime default ah kama dambayn karo halbeeg leh qiime default ah.\n\t\tFaylka: '{node.filename}', Sadarka: {param.line}")

            self.symbol_table.set(param.name, param.param_type)

        self.check(node.body)

        self.symbol_table.pop_scope()
        self.current_function = previous_function





    def check_MethodCallNode(self, node: MethodCallNode):
        self.check(node.object_node)
        object_type = self.get_expression_type(node.object_node)
        if isinstance(object_type, ArrayTypeNode):
            self.get_expression_type(node)
            return
        class_info = self.symbol_table.get(str(object_type))
        if not class_info or class_info[1] != 'class_definition':
            raise SemanticError(f"Cilad Macne: Hawsha '{node.method_name}' lagama yeeri karo shayga '{object_type}' (ma ahan koox).\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        class_node = class_info[0]
        
        # Look for method in class or parents
        method = None
        current_class = class_node
        method_source_class = None
        while current_class:
            method = next((m for m in current_class.methods if m.name == node.method_name), None)
            if method: 
                method_source_class = current_class
                break
            
            # Use parent_class AST node if linked, else fail
            if getattr(current_class, 'parent_class', None):
                current_class = current_class.parent_class
            else:
                current_class = None

        if not method:
            raise SemanticError(f"Cilad Macne: Kooxda '{object_type}' ma laha hawl la yiraahdo '{node.method_name}'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        node.method_source_class = method_source_class

        # Resolve arguments against method parameters
        node.args_list = self._resolve_call_arguments(node.args_list, method.params, node, context=f"method '{node.method_name}'")

        # Type check arguments
        for i, arg_node in enumerate(node.args_list):
            arg_type = self.get_expression_type(arg_node)
            param_def = method.params[i]
            if isinstance(param_def, ParameterNode):
                 param_type = param_def.param_type
            else:
                 param_type = param_def[1]
                 
            if not self._are_types_compatible(param_type, arg_type):
                raise SemanticError(f"Cilad Nooca Xogta: Halbeega {i+1} ee hawsha '{node.method_name}' waa inuu noqdaa '{param_type}', laakiin waa '{arg_type}'.\n\t\tFaylka: '{arg_node.filename}', Sadarka: {node.line}")
        self.check(node.args_list)



    def check_ReturnStatementNode(self, node: ReturnStatementNode):

        if not self.current_function:

            raise SemanticError(f"Cilad Macne: 'soo_celi' waxaa loo isticmaali karaa oo kaliya hawl gudaheeda.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        if node.expression:

            return_type = self.get_expression_type(node.expression)

            expected_type = self.current_function.return_type

            if not self._are_types_compatible(expected_type, return_type):

                raise SemanticError(f"Cilad Nooca Xogta: Hawsha waa inay soo celisaa '{expected_type}', laakiin waxay soo celinaysaa '{return_type}'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")



    def check_IdentifierNode(self, node: IdentifierNode):

        pass



    def check_MemberAccessNode(self, node: MemberAccessNode):

        self.check(node.object_node)



    def check_ThisNode(self, node: ThisNode):

        pass



    def check_IfNode(self, node: IfNode):

        self.generic_check(node)



    def check_BinaryOpNode(self, node: BinaryOpNode):

        self.generic_check(node)



    def check_TernaryOpNode(self, node: TernaryOpNode):

        self.generic_check(node)



    def check_QorNode(self, node: QorNode):

        for expr in node.expressions:

            self.check(expr)



    def check_HelNode(self, node: HelNode):

        self.generic_check(node)



    def check_FStringNode(self, node: FStringNode):
        for part_type, part_value in node.parts:
            if part_type == "expr" and isinstance(part_value, ASTNode):
                self.check(part_value)



    def check_FunctionCallNode(self, node: FunctionCallNode):
        func_info = self.symbol_table.get(node.name)
        is_builtin = node.name in functions_

        if not func_info and not is_builtin:
            raise SemanticError(f"Cilad Macne: Hawsha '{node.name}' lama helin.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        if is_builtin:
            # Handle built-in functions separately if they have different calling conventions
            # For now, assume they are handled by the transpiler
            for arg in node.params:
                if isinstance(arg, NamedArgument):
                    raise SemanticError(f"Cilad Macne: Hawl dhaxal (built-in) '{node.name}' ma taageerto halbeegyo magac leh.\n\t\tFaylka: '{arg.filename}', Sadarka: {arg.line}")
            self.generic_check(node)
            return
        else:
            func_node = func_info[0]
            func_type = func_info[1]

            if isinstance(func_type, FunctionTypeNode):
                expected_params = func_type.param_types or []
                for arg in node.params:
                    if isinstance(arg, NamedArgument):
                        raise SemanticError(f"Cilad Macne: Wicitaan hawl nooc lagu hayo (function variable) ma taageerto halbeegyo magac leh.\n\t\tFaylka: '{arg.filename}', Sadarka: {arg.line}")
                if len(node.params) != len(expected_params):
                    raise SemanticError(
                        f"Cilad Tirada: Hawsha '{node.name}' waxay rabtaa {len(expected_params)} xabo, "
                        f"laakiin waxaa la siiyay {len(node.params)}.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}"
                    )
                for i, (arg_node, expected_type) in enumerate(zip(node.params, expected_params)):
                    arg_type = self.get_expression_type(arg_node)
                    if not self._are_types_compatible(expected_type, arg_type):
                        raise SemanticError(
                            f"Cilad Nooca Xogta: Qaybta {i+1} ee hawsha '{node.name}' waa inay noqotaa '{expected_type}', "
                            f"laakiin la siiyay '{arg_type}'.\n\t\tFaylka: '{arg_node.filename}', Sadarka: {arg_node.line}"
                        )
                self.generic_check(node)
                return

            # Normal user-defined function
            ordered_args = self._resolve_call_arguments(node.params, func_node.params, node, context=f"hawl '{node.name}'")

            for i, arg_node in enumerate(ordered_args):
                arg_type = self.get_expression_type(arg_node)
                param_type = func_node.params[i].param_type
                if not self._are_types_compatible(param_type, arg_type):
                    raise SemanticError(f"Cilad Nooca Xogta: Qaybta {i+1} ee hawsha '{node.name}' waa inay noqotaa '{param_type}', laakiin la siiyay '{arg_type}'.\n\t\tFaylka: '{getattr(arg_node, 'filename', node.filename)}', Sadarka: {getattr(arg_node, 'line', node.line)}")

        self.generic_check(node)



    def check_ArrayAccessNode(self, node: ArrayAccessNode):

        self.generic_check(node)



    def check_ArrayAssignmentNode(self, node: ArrayAssignmentNode):

        self.generic_check(node)



    def check_DictionaryInitializationNode(self, node: DictionaryInitializationNode):

        for key, value in node.pairs:

            key_type = self.get_expression_type(key)

            if str(key_type) != 'eray':

                raise SemanticError(f"Cilad Nooca Xogta: Furaha qaamuuska waa inuu noqdaa 'eray', laakiin la helay '{key_type}'.\n\t\tFaylka: '{key.filename}', Sadarka: {key.line}")

            self.check(value)



    def check_DictionaryAccessNode(self, node: DictionaryAccessNode):

        self.check(node.dictionary_node)

        dict_type = self.get_expression_type(node.dictionary_node)

        if str(dict_type) != 'qaamuus':

            raise SemanticError(f"Cilad Nooca Xogta: Isku day inaad furaha ka gasho wax aan qaamuus ahayn ('{dict_type}').\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        key_type = self.get_expression_type(node.key_node)

        if str(key_type) != 'eray':

            raise SemanticError(f"Cilad Nooca Xogta: Furaha qaamuuska waa inuu noqdaa 'eray', laakiin la helay '{key_type}'.\n\t\tFaylka: '{node.key_node.filename}', Sadarka: {node.key_node.line}")



    def check_DictionaryAssignmentNode(self, node: DictionaryAssignmentNode):

        self.check(node.dictionary_access_node)

        self.check(node.value_node)



    def check_WhileNode(self, node: WhileNode):
        self.check(node.condition)
        self.loop_depth += 1
        self.check(node.body)
        self.loop_depth -= 1


    def check_DoWhileNode(self, node: DoWhileNode):
        self.loop_depth += 1
        self.check(node.body)
        self.loop_depth -= 1
        self.check(node.condition)



    def check_ForRangeNode(self, node: ForRangeNode):
        self.check(node.start_expr)
        self.check(node.end_expr)
        start_type = self.get_expression_type(node.start_expr)
        end_type = self.get_expression_type(node.end_expr)

        if str(start_type) != 'tiro' or str(end_type) != 'tiro':
            raise SemanticError(f"Cilad Macne: 'soco laga bilaabo' wuxuu u baahan yahay tirooyin (integers), laakiin waxaa la siiyay '{start_type}' iyo '{end_type}'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        self.symbol_table.push_scope()
        self.symbol_table.set(node.iterator_var_name, 'tiro')
        self.loop_depth += 1
        self.check(node.body)
        self.loop_depth -= 1
        self.symbol_table.pop_scope()

    def check_BreakNode(self, node: BreakNode):
        if self.loop_depth == 0:
            raise SemanticError(f"Cilad Macne: 'joog' waxaa la isticmaali karaa oo keliya gudaha wareeg (loop).\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

    def check_ContinueNode(self, node: ContinueNode):
        if self.loop_depth == 0:
            raise SemanticError(f"Cilad Macne: 'kasoco' waxaa la isticmaali karaa oo keliya gudaha wareeg (loop).\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")



    def check_ForEachNode(self, node: ForEachNode):
        self.check(node.array_expr)
        iterable_type = self.get_expression_type(node.array_expr)

        element_type = None
        if isinstance(iterable_type, ArrayTypeNode):
            element_type = iterable_type.element_type or "dynamic_value"
        elif str(iterable_type) == 'eray':
            element_type = 'xaraf'
        else:
            raise SemanticError(f"Cilad Macne: 'soco kasta' wuxuu u baahan yahay tix (array) ama eray (string), laakiin waxaa la siiyay '{iterable_type}'.\n\t\tFaylka: '{node.filename}', Sadarka: {node.line}")

        self.symbol_table.push_scope()
        self.symbol_table.set(node.iterator_var_name, element_type)
        self.loop_depth += 1
        self.check(node.body)
        self.loop_depth -= 1
        self.symbol_table.pop_scope()



    def check_NumberNode(self, node: NumberNode):

        pass



    def check_FloatNode(self, node: FloatNode):

        pass



    def check_StringNode(self, node: StringNode):

        pass



    def check_CharNode(self, node: CharNode):

        pass



    def check_BooleanNode(self, node: BooleanNode):

        pass