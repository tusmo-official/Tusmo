from compiler.built_in import BUILT_IN_FUNCTIONS

def check_built_in_function_call(checker, node):
    fn_name = node.name
    if fn_name not in BUILT_IN_FUNCTIONS:
        return None
    rules = BUILT_IN_FUNCTIONS[fn_name]
    
    if len(node.params) != rules["arg_count"]:
        raise SyntaxError(f"Khalad Tirada: Hawsha '{fn_name}' waxay u baahan tahay {rules['arg_count']} qaybood, laakiin la siiyay {len(node.params)}.\n\t\tSadarka: {node.line}")
    
    for i, arg_node in enumerate(node.params):
        expected_type = rules["arg_types"][i]
        actual_type = checker.get_expression_type(arg_node)
        if str(actual_type) != expected_type:
            raise SyntaxError(f"Khalad Nooca Xogta: Qaybta {i+1} ee hawsha '{fn_name}' waa inay noqotaa '{expected_type}', laakiin la siiyay '{actual_type}'.\n\t\tSadarka: {node.line}")
            
    return rules["return_type"]
    return rules["return_type"]