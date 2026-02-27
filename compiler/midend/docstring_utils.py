import codecs
import re
from compiler.frontend.parser.ast_nodes import (
    ASTNode,
    ClassNode,
    FunctionNode,
    StringNode,
)

_DOCSTRING_PATTERN = re.compile(
    r'(^[ \t]*)(?<!\$)"""(.*?)(?<!\$)"""[ \t]*(?:\r?\n|$)',
    re.DOTALL | re.MULTILINE,
)


def preprocess_docstrings(source: str) -> str:
    """
    Replace lines of the form `    :text goes here:` with
    string-literal statements so the parser treats them like
    Python-style docstrings.
    """

    def _escape(text: str) -> str:
        return (
            text.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
        )

    def repl(match: re.Match) -> str:
        indent = match.group(1)
        text = match.group(2)
        escaped = _escape(text)
        return f'{indent}"{escaped}";\n'

    return _DOCSTRING_PATTERN.sub(repl, source)


def attach_docstrings(ast):
    """
    Traverse the AST and attach docstring metadata to FunctionNode/ClassNode
    instances. Removes the synthetic StringNode from the body/members so it
    does not generate code.
    """
    if isinstance(ast, list):
        for node in ast:
            _attach_docstrings(node)
    elif isinstance(ast, ASTNode):
        _attach_docstrings(ast)
    return ast


def _attach_docstrings(node: ASTNode | None):
    if node is None:
        return

    if isinstance(node, FunctionNode):
        if isinstance(node.body, list) and node.body and isinstance(node.body[0], StringNode):
            node.docstring = _unescape_docstring(node.body[0].value)
            node.body = node.body[1:]

    if isinstance(node, ClassNode):
        if getattr(node, "docstring", None) is None:
            members = getattr(node, "members", None)
            if isinstance(members, list) and members and isinstance(members[0], StringNode):
                node.docstring = _unescape_docstring(members[0].value)
                node.members = members[1:]

    for attr_name in dir(node):
        if attr_name.startswith("__"):
            continue
        value = getattr(node, attr_name)
        if isinstance(value, list):
            for child in value:
                if isinstance(child, ASTNode):
                    _attach_docstrings(child)
        elif isinstance(value, ASTNode):
            _attach_docstrings(value)


def _unescape_docstring(text: str) -> str:
    try:
        return codecs.decode(text, "unicode_escape")
    except Exception:
        return text
