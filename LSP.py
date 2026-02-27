from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from lsprotocol.types import (
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    Hover,
    HoverParams,
    MarkupContent,
    MarkupKind,
)
from pygls.lsp.server import LanguageServer

from compiler.midend.docstring_index import (
    DocEntry,
    DocstringIndex,
    build_doc_index,
    build_doc_index_with_imports,
)

LOGGER = logging.getLogger("tusmo.hover")

TEXT_DOCUMENT_DID_OPEN = "textDocument/didOpen"
TEXT_DOCUMENT_DID_CHANGE = "textDocument/didChange"
TEXT_DOCUMENT_DID_CLOSE = "textDocument/didClose"
HOVER = "textDocument/hover"


class TusmoLanguageServer(LanguageServer):
    """A minimal hover-focused language server for Tusmo sources."""

    def __init__(self) -> None:
        super().__init__("tusmo-hover-server", "0.1.0")
        self.doc_indices: dict[str, DocstringIndex] = {}


server = TusmoLanguageServer()


@server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: TusmoLanguageServer, params: DidOpenTextDocumentParams) -> None:
    _refresh_index(ls, params.text_document.uri)


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: TusmoLanguageServer, params: DidChangeTextDocumentParams) -> None:
    _refresh_index(ls, params.text_document.uri)


@server.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(ls: TusmoLanguageServer, params: DidCloseTextDocumentParams) -> None:
    ls.doc_indices.pop(params.text_document.uri, None)


@server.feature(HOVER)
def hover(ls: TusmoLanguageServer, params: HoverParams) -> Optional[Hover]:
    document = ls.workspace.get_text_document(params.text_document.uri)
    if not document:
        return None

    line = _get_line(document.source, params.position.line)
    if line is None:
        return None

    symbol, qualified_symbol = _extract_symbol(line, params.position.character)
    if not symbol:
        return None

    doc_index = ls.doc_indices.get(params.text_document.uri)
    if not doc_index:
        return None

    entries: list[DocEntry] = []
    if qualified_symbol:
        entries = doc_index.lookup(qualified_symbol)
    if not entries:
        entries = doc_index.lookup(symbol)
    if not entries:
        return None

    markdown = _format_entries(entries)
    return Hover(contents=MarkupContent(kind=MarkupKind.Markdown, value=markdown))


def _refresh_index(ls: TusmoLanguageServer, uri: str) -> None:
    document = ls.workspace.get_text_document(uri)
    if not document:
        return

    filename = document.path or uri
    file_path = _to_path(filename)
    search_roots = _determine_search_roots(ls, file_path)
    try:
        if file_path:
            index = build_doc_index_with_imports(
                document.source,
                str(file_path),
                extra_search_roots=search_roots,
            )
        else:
            index = build_doc_index(document.source, filename)
    except Exception:  # pragma: no cover - defensive
        LOGGER.exception("Failed to build docstring index for %s", filename)
        return

    ls.doc_indices[uri] = index


def _get_line(source: str, line_number: int) -> Optional[str]:
    lines = source.splitlines()
    if line_number < 0 or line_number >= len(lines):
        return None
    return lines[line_number]


def _is_identifier_char(ch: str) -> bool:
    return ch == "_" or ch.isalnum()


def _extract_symbol(line: str, character: int) -> tuple[Optional[str], Optional[str]]:
    if not line:
        return None, None

    if character >= len(line):
        character = len(line) - 1
    if character < 0:
        return None, None

    if not _is_identifier_char(line[character]) and character > 0 and _is_identifier_char(line[character - 1]):
        character -= 1

    start = character
    while start > 0 and _is_identifier_char(line[start - 1]):
        start -= 1

    end = character
    while end < len(line) and _is_identifier_char(line[end]):
        end += 1

    symbol = line[start:end]
    if not symbol:
        return None, None

    qualifier = None
    dot_index = start - 1
    if dot_index >= 0 and line[dot_index] == ".":
        q_end = dot_index
        q_start = q_end - 1
        while q_start >= 0 and _is_identifier_char(line[q_start]):
            q_start -= 1
        qualifier = line[q_start + 1 : q_end] if q_start < q_end - 1 else None

    if qualifier:
        return symbol, f"{qualifier}.{symbol}"
    return symbol, None


def _format_entries(entries: list[DocEntry]) -> str:
    chunks = []
    for entry in entries:
        header = f"**{entry.display_name}** ({entry.kind})"
        signature_block = (
            f"```tusmo\n{entry.signature}\n```" if entry.signature else ""
        )
        doc_text = _render_docstring(entry.docstring)
        chunk_parts = [header]
        if signature_block:
            chunk_parts.append(signature_block)
        chunk_parts.append(doc_text)
        chunks.append("\n\n".join(chunk_parts))
    return "\n\n---\n\n".join(chunks)


def _render_docstring(docstring: str | None) -> str:
    if not docstring:
        return "_Docstring not provided._"

    text = docstring.strip()
    if not text:
        return "_Docstring not provided._"

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace(r"\\n", "\n")
    text = text.replace(r"\n", "\n")
    text = re.sub(r"#([^#\n]+)#", lambda m: f"**{m.group(1).strip()}**", text)
    text = text.replace("\n", "  \n")
    return text


def _to_path(filename: str | None) -> Optional[Path]:
    if not filename:
        return None
    path_str = filename
    if filename.startswith("file://"):
        path_str = urlparse(filename).path
    try:
        path = Path(path_str)
    except (OSError, ValueError):
        return None
    if not path.is_absolute():
        try:
            path = path.resolve()
        except OSError:
            return None
    return path


def _determine_search_roots(
    ls: TusmoLanguageServer, file_path: Optional[Path]
) -> list[Path]:
    candidates: list[Path] = []

    workspace_root = getattr(ls.workspace, "root_path", None)
    if workspace_root:
        root_path = Path(workspace_root)
        for name in ("lib", "stdlib"):
            candidates.append(root_path / name)

    for name in ("lib", "stdlib"):
        candidates.append(Path.cwd() / name)

    if file_path:
        repo_root = file_path.parent
        for name in ("lib", "stdlib"):
            candidates.append(repo_root / name)

    uniq: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = str(candidate.resolve())
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        path_obj = Path(resolved)
        if path_obj.exists():
            uniq.append(path_obj)

    return uniq


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tusmo hover server (docstrings on hover).",
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run in stdio mode (this is the default if --tcp is not provided).",
    )
    parser.add_argument(
        "--tcp",
        action="store_true",
        help="Run the server over TCP instead of stdio.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind when using --tcp (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=2087,
        help="Port to bind when using --tcp (default: 2087).",
    )
    parser.add_argument(
        "--log-file",
        help="Optional path to write debug logs for the language server.",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging verbosity (default: WARNING).",
    )
    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log_file,
        level=getattr(logging, args.log_level.upper(), logging.WARNING),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.tcp:
        LOGGER.info("Starting Tusmo hover server on tcp://%s:%s", args.host, args.port)
        server.start_tcp(args.host, args.port)
    else:
        LOGGER.info("Starting Tusmo hover server (stdio mode)")
        server.start_io()


if __name__ == "__main__":
    main()
