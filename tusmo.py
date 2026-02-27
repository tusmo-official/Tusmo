# tusmo.py (Correctly Updated)

import sys
import os
import traceback
import subprocess

sys.path.append(os.path.dirname(__file__))


from compiler.frontend.lexer.lexer import lexer
from compiler.frontend.parser.parser import parser
from compiler.backend.transpiler import Transpiler
from compiler.midend.symbol_table import SymbolTable
from compiler.midend.semanticanalyzer import SemanticChecker, SemanticError
from compiler.processer import process_imports
from compiler.midend.fstring_resolver import resolve_fstrings
from compiler.midend.docstring_utils import (
    preprocess_docstrings,
    attach_docstrings,
)


def main():
    remove_c_code = True
    if len(sys.argv) not in [2, 3]:
        print("Isticmaalka: python tusmo.py <magaca_faylka.tus> [--c]")
        sys.exit(1)

    if len(sys.argv) == 3 and sys.argv[2] == "--c":
        remove_c_code = False

    filename = sys.argv[1]
    if not os.path.exists(filename):
        print(f"Cilad: Faylka '{filename}' ma jiro.")
        sys.exit(1)

    script_directory = os.path.dirname(os.path.abspath(__file__))
    project_root = script_directory
    runtime_dir = os.path.join(project_root, "runtime")
    stdlib_dir = os.path.join(project_root, "stdlib")

    # Map features to their source files
    feature_to_source_map = {
        "string": os.path.join(runtime_dir, "string.c"),
        "nasiib": os.path.join(runtime_dir, "random.c"),
        "io": os.path.join(runtime_dir, "io.c"),
        "wakhti": os.path.join(runtime_dir, "time.c"),
        "os": os.path.join(runtime_dir, "os.c"),
        "dictionary": os.path.join(runtime_dir, "dictionary.c"),
        "conversion": os.path.join(runtime_dir, "type_conversion.c"),
        "http": os.path.join(runtime_dir, "http.c"),
        "socket": os.path.join(runtime_dir, "socket.c"),
        "websocket": os.path.join(runtime_dir, "websocket.c"),
        "array": [
            os.path.join(runtime_dir, "array.c"),
            os.path.join(runtime_dir, "array_generic.c"),
        ],
    }

    with open(filename, "r") as f:
        main_code = f.read()

    shared_symbol_table = SymbolTable()

    try:
        initial_ast = parse_code_to_ast(main_code, filename)

        if not initial_ast:
            sys.exit(0)

        main_file_directory = os.path.dirname(os.path.abspath(filename))
        final_ast = process_imports(initial_ast, base_directory=main_file_directory, stdlib_path=stdlib_dir)

        if not final_ast:
            sys.exit(0)

        resolve_fstrings(final_ast)
        attach_docstrings(final_ast)

        checker = SemanticChecker(shared_symbol_table)
        checker.check(final_ast)

    
        # Pass the 'checker' instance to the Transpiler
        transpiler = Transpiler(shared_symbol_table, checker)
        c_code, used_features = transpiler.transpile(final_ast)                
        out_file = filename.replace(".tus", ".c")
        with open(out_file, "w") as f:
            f.write(c_code)

        binary = out_file.replace(".c", "")

        # Dynamically build the list of source files to compile
        source_files_to_compile = [out_file]
        
        


        for feature in used_features:
            if feature in feature_to_source_map:
                source_path = feature_to_source_map[feature]
                # Check if the path is a list (like for 'array') or a single string
                if isinstance(source_path, list):
                    for path in source_path:
                        if os.path.exists(path):
                            source_files_to_compile.append(path)
                else:  # It's a single string
                    if os.path.exists(source_path):
                        source_files_to_compile.append(source_path)

        # Implicit dependency: Array (mixed) might use Dictionary printing
        if "array" in used_features and "dictionary" not in used_features:
            dict_path = feature_to_source_map["dictionary"]
            if os.path.exists(dict_path):
                source_files_to_compile.append(dict_path)

        all_sources_str = " ".join([f'"{path}"' for path in source_files_to_compile])

        # Allow overriding compiler/lib/include via env vars (for bundled installs)
        cc = os.environ.get("TUSMO_CC", "gcc")
        lib_dir_override = os.environ.get("TUSMO_LIB_DIR")
        include_override = os.environ.get("TUSMO_INCLUDE_DIR")

        include_flag = f'-I"{include_override}"' if include_override else f'-I"{runtime_dir}"'
        lib_flag = f' -L"{lib_dir_override}"' if lib_dir_override else ""

        # The final, dynamic compile command
        compile_command = (
            f'"{cc}" -O3 -march=native -flto -o "{binary}" '
            f'{all_sources_str} {include_flag}{lib_flag} -lgc'
        )

        compile_result = os.system(compile_command)

        if compile_result == 1:
            print(
                f"\nCilad ayaa ka dhacday isku-darka C code-ka. Faylka C wuxuu ku yaal: {out_file}"
            )
           

        if remove_c_code:
            if os.path.exists(out_file):
                os.remove(out_file)
            

    except SemanticError as e:
        print(f"\n{e}")
        sys.exit(1)
    except Exception:
        print("\nCilad Lama Filaan Ah Ayaa Dhacday:")
        traceback.print_exc()
        sys.exit(1)


def parse_code_to_ast(code, filename):
    code = preprocess_docstrings(code)
    lexer.filename = filename
    lexer.lineno = 1
    ast = parser.parse(code, lexer=lexer)
    return ast if ast is not None else []


if __name__ == "__main__":
    main()
