from __future__ import annotations

from typing import List

from compiler.frontend.parser.ast_nodes import ASTNode, FStringNode
from compiler.processer import parse_code_to_ast
from compiler.frontend.parser.ast_nodes import StringNode, BinaryOpNode


def resolve_fstrings(ast):
    """
    Walk the AST and convert FStringNode parts from raw source strings into
    real expression subtrees so downstream passes (semantic analysis,
    codegen) can treat them like regular expressions.
    """
    if isinstance(ast, list):
        for node in ast:
            _resolve_node(node)
    elif isinstance(ast, ASTNode):
        _resolve_node(ast)
    return ast


def _resolve_node(node: ASTNode | None):
    if node is None:
        return

    if isinstance(node, FStringNode):
        _resolve_fstring_parts(node)

    for attr_name in dir(node):
        if attr_name.startswith("__"):
            continue
        value = getattr(node, attr_name)
        if isinstance(value, list):
            for child in list(value):
                if isinstance(child, ASTNode):
                    _resolve_node(child)
        elif isinstance(value, ASTNode):
            _resolve_node(value)


def _resolve_fstring_parts(node: FStringNode) -> None:
    concatenated: List[ASTNode] = []
    text_buffer = ""

    def flush_text():
        nonlocal text_buffer
        if text_buffer:
            concatenated.append(StringNode(text_buffer, line=node.line, filename=node.filename))
            text_buffer = ""

    for part_type, part_value in node.parts:
        if part_type == "text":
            text_buffer += part_value
        elif part_type == "expr":
            flush_text()
            if isinstance(part_value, ASTNode):
                concatenated.append(part_value)
            else:
                expr_text = part_value.strip()
                if expr_text:
                    expr_ast = _parse_expression(expr_text, node.filename, node.line)
                    concatenated.append(expr_ast)
    flush_text()

    if not concatenated:
        node.parts = [("expr", StringNode("", line=node.line, filename=node.filename))]
        return

    combined = concatenated[0]
    for expr in concatenated[1:]:
        combined = BinaryOpNode(combined, '+', expr, line=node.line, filename=node.filename)
    node.parts = [("expr", combined)]


def _parse_expression(expr_src: str, filename: str | None, line: int | None):
    """
    Parse a single expression snippet using the regular compiler parser by
    wrapping it in a minimal statement.
    """
    code = f"{expr_src};"
    parsed = parse_code_to_ast(code, filename or "<fstring>")
    if not parsed:
        raise SyntaxError(
            f"F-string: Failed to parse expression '{expr_src}'"
            f"{' at line ' + str(line) if line else ''}"
        )
    return parsed[0]
