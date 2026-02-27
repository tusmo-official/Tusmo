import sys
import os
from compiler.frontend.parser.ast_nodes import KeenNode
from compiler.frontend.lexer.lexer import lexer
from compiler.frontend.parser.parser import parser
from compiler.midend.docstring_utils import preprocess_docstrings

def find_and_read_file(file_path):
    """Wuxuu si badbaado leh u furaa oo u akhriyaa fayl."""
    with open(file_path, "r") as f:
        return f.read()

def parse_code_to_ast(code, filename):
    """
    Wuxuu u beddelaa koodka qoran AST.
    Wuxuu u sheegayaa lexer-ka magaca faylka si ay u saxmaan fariimaha cilladaha.
    """
    code = preprocess_docstrings(code)
    lexer.filename = filename
    lexer.lineno = 1
    
    ast = parser.parse(code, lexer=lexer)
    if ast is None:
        return []
    return ast

def process_imports(initial_ast_nodes, base_directory, stdlib_path="stdlib", processed_files=None):
    """
    Wuxuu si is-daba-joog ah u raadiyaa dhammaan qodobbada 'keen', wuxuuna soo celiyaa
    hal AST oo la isku daray.
    """
    if processed_files is None:
        processed_files = set()

    final_ast = []

    for node in initial_ast_nodes:
        if isinstance(node, KeenNode):
            module_name = node.filename.strip('"\'')
            if module_name.endswith(".tus"):
                file_to_import = module_name
            else:
                file_to_import = module_name + ".tus"
            found_path = None

            # --- Istaraatiijiyadda Raadinta Faylka ---
            # 1. Marka hore, ka hubi galka uu ku jiro faylka hadda la shaqeynayo.
            potential_local_path = os.path.abspath(os.path.join(base_directory, file_to_import))
            
            if os.path.exists(potential_local_path):
                found_path = potential_local_path
            else:
                # 2. Haddii aan laga helin deegaanka, ka hubi maktabadda `library`.
                potential_library_path = os.path.abspath(os.path.join("lib", file_to_import))
                if os.path.exists(potential_library_path):
                    found_path = potential_library_path
                else:
                    # 3. Haddii aan laga helin maktabadda, ka hubi maktabadda asaasiga ah (stdlib).
                    potential_stdlib_path = os.path.abspath(os.path.join(stdlib_path, file_to_import))
                    if os.path.exists(potential_stdlib_path):
                        found_path = potential_stdlib_path

            # --- Cilad haddii faylka la waayo ---
            if not found_path:
                error_filename = getattr(lexer, 'filename', '<faylka isha>')
                print(f"Cilad ayaa ku jirta '{error_filename}' safka {node.line}:")
                print(f"Lama helin (module) '{module_name}'. Faylka lagama helin galka deegaanka, maktabadda 'lib', ama maktabadda asaasiga ah (stdlib).")
                sys.exit(1)

            # --- Ka hortagga soo dejinta isku-wareegta (Circular Imports) ---
            if found_path in processed_files:
                continue
            
            processed_files.add(found_path)

            try:
                imported_code = find_and_read_file(found_path)
                imported_ast = parse_code_to_ast(imported_code, found_path)
                
                new_base_dir = os.path.dirname(found_path)
                resolved_imported_ast = process_imports(imported_ast, new_base_dir, stdlib_path, processed_files)
                
                final_ast.extend(resolved_imported_ast)

            except FileNotFoundError:
                print(f"Cilad Isku-dubaraha: Faylka '{found_path}' wuu lumay intii lagu kuda jiray.")
                sys.exit(1)
            except Exception as e:
                # Tani waxay qabanaysaa ciladaha naxwaha ee parser-ka.
                print(f"Way fashilantay in la soo shaqeysiiyo '{found_path}':\n{e}")
                sys.exit(1)
        else:
            final_ast.append(node)
            
    return final_ast
