# midend/symbol_table.py

from typing import Any, Optional, Tuple

class SymbolTable:
    """
    SymbolTable for Tusmo language.

    - Supports multiple scopes (global + local)
    - Variables stored as tuple: (value, type, return_type)
    - Functions can have return_type
    """

    def __init__(self) -> None:
        # Stack of scopes, first is global
        self.scopes: list[dict[str, Tuple[Any, str, Optional[str]]]] = [{}]

    # ---------------- Scope Management ----------------
    def push_scope(self) -> None:
        """Enter a new scope (e.g., function, block)."""
        self.scopes.append({})

    def pop_scope(self) -> None:
        """Exit current scope."""
        if len(self.scopes) > 1:  # Keep global scope
            self.scopes.pop()
        else:
            raise Exception("Cannot pop global scope")

    # ---------------- Variable Management ----------------
    def set(self, name: str, var_type: str, value: Any = None, return_type: Optional[str] = None) -> None:
        """
        Set variable in current scope.
        """
        self.scopes[-1][name] = (value, var_type, return_type)

    def set_global(self, name: str, var_type: str, value: Any = None, return_type: Optional[str] = None) -> None:
        """
        Set variable in global scope.
        """
        if self.exists_in_global_scope(name):
            raise Exception(f"Khalad: '{name}' hore ayaa loo qeexay global scope.")
        self.scopes[0][name] = (value, var_type, return_type)

    def get(self, name: str) -> Optional[Tuple[Any, str, Optional[str]]]:
        """
        Lookup variable from current scope up to global.
        Returns (value, type, return_type) or None.
        """
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    # ---------------- Existence Checks ----------------
    def exists_in_current_scope(self, name: str) -> bool:
        return name in self.scopes[-1]

    def exists_in_global_scope(self, name: str) -> bool:
        return name in self.scopes[0]

    def exists(self, name: str) -> bool:
        return self.get(name) is not None

    # ---------------- Debug ----------------
    def dump_current_scope(self) -> None:
        """Print current scope for debugging."""
        current_scope_level = len(self.scopes) - 1
        current_scope = self.scopes[-1]
        print(f"===== Current Scope (Level {current_scope_level}) =====")
        if not current_scope:
            print("  (Empty)")
        else:
            for name, (value, var_type, ret_type) in current_scope.items():
                print(f"  {name} ({var_type}) = {value}, return_type={ret_type}")
        print("========================================")

    def dump_all(self) -> None:
        """Print all scopes for debugging."""
        print("===== Symbol Table =====")
        for i, scope in enumerate(self.scopes):
            print(f"Scope {i}:")
            if not scope:
                print("  (Empty)")
            else:
                for name, (value, var_type, ret_type) in scope.items():
                    print(f"  {name} ({var_type}) = {value}, return_type={ret_type}")
        print("========================================")
