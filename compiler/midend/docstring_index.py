from __future__ import annotations

import contextlib
import io
import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import urlparse

from compiler.frontend.lexer.lexer import lexer
from compiler.frontend.parser.ast_nodes import (
    ASTNode,
    ClassNode,
    FunctionNode,
    KeenNode,
    ParameterNode,
)
from compiler.frontend.parser.parser import parser
from compiler.midend.docstring_utils import attach_docstrings, preprocess_docstrings

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocEntry:
    """Represents a single hover/documentation entry."""

    display_name: str
    kind: str
    signature: str | None
    docstring: str


class DocstringIndex:
    """Collects docstring entries for quick lookup."""

    def __init__(self) -> None:
        self._entries: dict[str, list[DocEntry]] = defaultdict(list)

    def add(self, key: str, entry: DocEntry) -> None:
        bucket = self._entries[key]
        if entry not in bucket:
            bucket.append(entry)

    def lookup(self, key: str) -> list[DocEntry]:
        return self._entries.get(key, [])

    def items(self):
        return self._entries.items()

    def merge(self, other: DocstringIndex) -> None:
        for key, entries in other.items():
            for entry in entries:
                self.add(key, entry)


def build_doc_index(source: str, filename: str) -> DocstringIndex:
    """
    Parse `source`, attach docstrings, and build a lookup table suitable for IDE hovers.
    Parsing errors are swallowed so the caller can keep the editor responsive while the
    user is typing an incomplete construct.
    """

    index = DocstringIndex()

    ast_nodes = _safe_parse_ast(source, filename)
    if not ast_nodes:
        return index

    for node in ast_nodes:
        _collect_from_node(node, index)

    return index


def build_doc_index_with_imports(
    source: str, filename: str, *, extra_search_roots: Iterable[str | Path] | None = None
) -> DocstringIndex:
    """
    Build a docstring index for `source` and recursively load entries from files
    referenced via `keen` statements. `filename` should be an absolute path so
    relative imports can be resolved reliably.
    """

    path = _coerce_path(filename)
    visited: set[Path] = set()
    if path:
        visited.add(path.resolve())

    search_roots = _normalize_search_roots(extra_search_roots)
    return _build_index_recursive(source, path, search_roots, visited)


def _log_parse_issue(
    filename: str,
    stdout_buffer: io.StringIO,
    stderr_buffer: io.StringIO,
    exc: BaseException | None = None,
) -> None:
    message_parts = []
    out = stdout_buffer.getvalue().strip()
    err = stderr_buffer.getvalue().strip()
    if out:
        message_parts.append(out)
    if err:
        message_parts.append(err)
    message = " | ".join(message_parts) if message_parts else "parser issue"
    if exc:
        LOGGER.debug(
            "Docstring indexing skipped for %s: %s (%s)", filename, message, exc
        )
    else:
        LOGGER.debug("Docstring indexing failed for %s: %s", filename, message)


def _parse_source(source: str, filename: str) -> list[ASTNode]:
    code = preprocess_docstrings(source)
    lexer.filename = filename
    lexer.lineno = 1
    ast = parser.parse(code, lexer=lexer)
    if not ast:
        return []
    attach_docstrings(ast)
    return ast if isinstance(ast, list) else [ast]


def _safe_parse_ast(source: str, filename: str) -> list[ASTNode]:
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(
            stderr_buffer
        ):
            ast_nodes = _parse_source(source, filename)
    except SystemExit as exc:
        _log_parse_issue(filename, stdout_buffer, stderr_buffer, exc)
        return []
    except Exception:  # pragma: no cover - defensive
        _log_parse_issue(filename, stdout_buffer, stderr_buffer)
        return []

    return ast_nodes


def _collect_from_node(node: ASTNode, index: DocstringIndex, class_name: str | None = None) -> None:
    if isinstance(node, ClassNode):
        _record_class(node, index)
        for method in node.methods or []:
            _collect_from_node(method, index, class_name=node.name)
        return

    if isinstance(node, FunctionNode):
        _record_function(node, index, class_name)
        return


def _record_class(node: ClassNode, index: DocstringIndex) -> None:
    if not node.docstring:
        return

    entry = DocEntry(
        display_name=node.name,
        kind="class",
        signature=f"koox {node.name}",
        docstring=node.docstring.strip(),
    )
    index.add(node.name, entry)


def _record_function(node: FunctionNode, index: DocstringIndex, class_name: str | None) -> None:
    if not node.docstring:
        return

    signature = _format_function_signature(node, class_name)
    kind = "method" if class_name else "function"
    display_name = f"{class_name}.{node.name}" if class_name else node.name
    entry = DocEntry(
        display_name=display_name,
        kind=kind,
        signature=signature,
        docstring=node.docstring.strip(),
    )

    index.add(node.name, entry)
    if class_name:
        index.add(f"{class_name}.{node.name}", entry)


def _format_function_signature(node: FunctionNode, class_name: str | None) -> str:
    params = ", ".join(_format_param(p) for p in node.params or [])
    qualifier = f"{class_name}." if class_name else ""
    return_type = _type_to_string(node.return_type)
    return f"{qualifier}{node.name}({params}) : {return_type}"


def _format_param(param: ParameterNode) -> str:
    type_repr = _type_to_string(param.param_type)
    return f"{param.name}: {type_repr}"


def _type_to_string(type_node) -> str:
    if isinstance(type_node, ASTNode):
        return str(type_node)
    return str(type_node or "waxbo")


def _build_index_recursive(
    source: str,
    file_path: Path | None,
    search_roots: list[Path],
    visited: set[Path],
) -> DocstringIndex:

    filename = str(file_path) if file_path else "<memory>"
    index = DocstringIndex()
    ast_nodes = _safe_parse_ast(source, filename)
    if not ast_nodes:
        return index

    for node in ast_nodes:
        _collect_from_node(node, index)

    if not file_path:
        return index

    current_dir = file_path.parent
    for module_name in _iter_keen_targets(ast_nodes):
        module_path = _resolve_module_path(module_name, current_dir, search_roots)
        if not module_path:
            continue
        try:
            resolved = module_path.resolve()
        except OSError:  # pragma: no cover - filesystem edge
            continue
        if resolved in visited:
            continue
        visited.add(resolved)
        try:
            child_source = module_path.read_text(encoding="utf-8")
        except OSError:
            LOGGER.debug("Docstring import skipped (unreadable): %s", module_path)
            continue
        child_index = _build_index_recursive(
            child_source, module_path, search_roots, visited
        )
        index.merge(child_index)

    return index


def _iter_keen_targets(ast_nodes: list[ASTNode]) -> Iterator[str]:
    for node in ast_nodes:
        if isinstance(node, KeenNode):
            yield node.filename


def _resolve_module_path(
    module_name: str, current_dir: Path, search_roots: list[Path]
) -> Path | None:
    if not module_name:
        return None

    target = module_name if module_name.endswith(".tus") else f"{module_name}.tus"
    target_path = Path(target)

    candidates: list[Path] = []
    if target_path.is_absolute():
        candidates.append(target_path)
    else:
        candidates.append(current_dir / target_path)
        for root in search_roots:
            candidates.append(root / target_path)
        candidates.append(Path.cwd() / target_path)

    seen: set[str] = set()
    for candidate in candidates:
        try:
            normalized = str(candidate.resolve())
        except OSError:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        if candidate.is_file():
            return candidate

    return None


def _normalize_search_roots(
    roots: Iterable[str | Path] | None,
) -> list[Path]:
    result: list[Path] = []
    if not roots:
        return result
    for root in roots:
        try:
            path = Path(root).resolve()
        except OSError:
            continue
        if path.exists() and path not in result:
            result.append(path)
    return result


def _coerce_path(filename: str | Path | None) -> Path | None:
    if not filename:
        return None
    if isinstance(filename, str) and filename.startswith("file://"):
        filename = urlparse(filename).path
    try:
        path = Path(filename)
    except TypeError:
        return None
    return path if path.is_absolute() else path.resolve()
