# =========================================================
# TOOLS MODULE
# Python does the heavy lifting.
# MCP server calls these functions.
# =========================================================

import ast
import io
import os
import re
import sys
import shutil
import traceback
from contextlib import redirect_stdout
from pathlib import Path

from ddgs import DDGS


# =========================================================
# CONFIG
# =========================================================

BASE_DIR = Path("workspace").resolve()

# Maximum amount of text returned to the LLM.
# This is VERY important for a slow/small local model.
MAX_OUTPUT_CHARS = 5000

# Maximum number of search results.
MAX_SEARCH_RESULTS = 5


BASE_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# OUTPUT CONTROL
# =========================================================

def compact_output(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    """
    Keep tool output small so the LLM does not receive
    unnecessary huge context.
    """

    if not text:
        return "No output"

    text = str(text)

    if len(text) <= limit:
        return text

    return (
        text[:limit]
        + f"\n\n...[output truncated: {len(text) - limit} characters removed]"
    )


# =========================================================
# SAFE PATH
# =========================================================

def safe_path(path: str) -> Path:
    """
    Resolve a path and ensure it stays inside WORKSPACE.

    Unlike the old startswith() check, this correctly handles
    paths such as:

        ../secret.txt
        ../../file.txt
        workspace_evil
    """

    try:
        candidate = (BASE_DIR / path).resolve()

        # Python 3.9+ supports Path.is_relative_to()
        if not candidate.is_relative_to(BASE_DIR):
            raise PermissionError(
                "Access denied: path is outside workspace"
            )

        return candidate

    except Exception as e:
        raise PermissionError(
            f"Invalid workspace path: {path}"
        ) from e


# =========================================================
# FILE TOOLS
# =========================================================

def read_file(filename: str) -> str:
    """
    Read a text file from the workspace.
    """

    try:
        path = safe_path(filename)

        if not path.exists():
            return f"ERROR: File not found: {filename}"

        if not path.is_file():
            return f"ERROR: Not a file: {filename}"

        content = path.read_text(encoding="utf-8")

        return compact_output(content)

    except Exception as e:
        return f"ERROR: {str(e)}"


# =========================================================

def write_file(filename: str, content: str) -> str:
    """
    Create or overwrite a text file inside the workspace.
    """

    try:
        path = safe_path(filename)

        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(
            content,
            encoding="utf-8"
        )

        return f"SUCCESS: Saved {filename}"

    except Exception as e:
        return f"ERROR: {str(e)}"


# =========================================================

def delete_file(filename: str) -> str:
    """
    Delete a file inside the workspace.
    """

    try:
        path = safe_path(filename)

        if not path.exists():
            return f"ERROR: File not found: {filename}"

        if not path.is_file():
            return f"ERROR: Not a file: {filename}"

        path.unlink()

        return f"SUCCESS: Deleted {filename}"

    except Exception as e:
        return f"ERROR: {str(e)}"


# =========================================================

def move_file(src: str, dst: str) -> str:
    """
    Move or rename a file inside the workspace.
    """

    try:
        source = safe_path(src)
        destination = safe_path(dst)

        if not source.exists():
            return f"ERROR: Source not found: {src}"

        if not source.is_file():
            return f"ERROR: Source is not a file: {src}"

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.move(
            str(source),
            str(destination)
        )

        return f"SUCCESS: {src} -> {dst}"

    except Exception as e:
        return f"ERROR: {str(e)}"


# =========================================================

def create_folder(foldername: str) -> str:
    """
    Create a folder inside the workspace.
    """

    try:
        path = safe_path(foldername)

        path.mkdir(
            parents=True,
            exist_ok=True
        )

        return f"SUCCESS: Folder created: {foldername}"

    except Exception as e:
        return f"ERROR: {str(e)}"


# =========================================================

def list_files(path: str = ".") -> str:
    """
    List files and folders inside the workspace.

    Returns a compact result to avoid unnecessary
    LLM context.
    """

    try:
        directory = safe_path(path)

        if not directory.exists():
            return f"ERROR: Directory not found: {path}"

        if not directory.is_dir():
            return f"ERROR: Not a directory: {path}"

        entries = []

        for item in sorted(
            directory.iterdir(),
            key=lambda x: x.name.lower()
        ):
            if item.is_dir():
                entries.append(f"[DIR]  {item.name}")
            else:
                entries.append(f"[FILE] {item.name}")

        if not entries:
            return "No files found"

        return compact_output(
            "\n".join(entries)
        )

    except Exception as e:
        return f"ERROR: {str(e)}"


# =========================================================
# PYTHON EXECUTION
# =========================================================

# Modules that are commonly useful for calculations/data work.
#
# IMPORTANT:
# This is NOT a security sandbox.
# It only reduces accidental dangerous imports.
ALLOWED_IMPORTS = {
    "math",
    "statistics",
    "random",
    "json",
    "csv",
    "re",
    "datetime",
    "collections",
    "itertools",
    "functools",
    "numpy",
    "pandas",
}


def check_python_code(code: str):
    """
    Perform a basic AST inspection before execution.

    This is a safety layer, NOT a real sandbox.
    """

    tree = ast.parse(code)

    for node in ast.walk(tree):

        # -------------------------------------------------
        # Check imports
        # -------------------------------------------------

        if isinstance(node, ast.Import):

            for alias in node.names:

                module = alias.name.split(".")[0]

                if module not in ALLOWED_IMPORTS:
                    raise PermissionError(
                        f"Import not allowed: {module}"
                    )

        elif isinstance(node, ast.ImportFrom):

            module = (node.module or "").split(".")[0]

            if module not in ALLOWED_IMPORTS:
                raise PermissionError(
                    f"Import not allowed: {module}"
                )

        # -------------------------------------------------
        # Block obvious dangerous builtins
        # -------------------------------------------------

        elif isinstance(node, ast.Call):

            if isinstance(node.func, ast.Name):

                dangerous = {
                    "eval",
                    "exec",
                    "compile",
                    "open",
                    "__import__",
                    "input",
                }

                if node.func.id in dangerous:
                    raise PermissionError(
                        f"Function not allowed: {node.func.id}"
                    )


# =========================================================

def run_python(code: str) -> str:
    """
    Execute Python for calculations and data processing.

    Heavy work should happen here instead of inside the LLM.

    IMPORTANT:
    This is restricted execution, NOT a secure sandbox.
    """

    try:

        # -------------------------------------------------
        # Validate code first
        # -------------------------------------------------

        check_python_code(code)

        # -------------------------------------------------
        # Capture stdout
        # -------------------------------------------------

        buffer = io.StringIO()

        with redirect_stdout(buffer):

            exec(
                code,
                {
                    "__builtins__": {
                        "print": print,
                        "len": len,
                        "range": range,
                        "sum": sum,
                        "min": min,
                        "max": max,
                        "abs": abs,
                        "round": round,
                        "sorted": sorted,
                        "enumerate": enumerate,
                        "zip": zip,
                        "map": map,
                        "filter": filter,
                        "list": list,
                        "dict": dict,
                        "set": set,
                        "tuple": tuple,
                        "str": str,
                        "int": int,
                        "float": float,
                        "bool": bool,
                    }
                }
            )

        output = buffer.getvalue()

        return compact_output(output)

    except Exception:
        return compact_output(
            "ERROR:\n" + traceback.format_exc()
        )


# =========================================================
# ADVANCED DEBUG TOOL
# =========================================================

def debug_python(code: str) -> dict:
    """
    Execute Python and return structured debugging information.
    """

    try:

        check_python_code(code)

        buffer = io.StringIO()

        with redirect_stdout(buffer):

            exec(
                code,
                {
                    "__builtins__": {
                        "print": print,
                        "len": len,
                        "range": range,
                        "sum": sum,
                        "min": min,
                        "max": max,
                        "abs": abs,
                        "round": round,
                        "sorted": sorted,
                        "enumerate": enumerate,
                        "zip": zip,
                        "map": map,
                        "filter": filter,
                        "list": list,
                        "dict": dict,
                        "set": set,
                        "tuple": tuple,
                        "str": str,
                        "int": int,
                        "float": float,
                        "bool": bool,
                    }
                }
            )

        return {
            "status": "success",
            "output": compact_output(
                buffer.getvalue()
            )
        }

    except Exception as e:

        tb = traceback.format_exc()

        match = re.search(
            r'File "<string>", line (\d+)',
            tb
        )

        lineno = (
            int(match.group(1))
            if match
            else None
        )

        code_lines = code.splitlines()

        highlighted = []

        for number, line in enumerate(
            code_lines,
            start=1
        ):

            prefix = (
                ">> "
                if number == lineno
                else "   "
            )

            highlighted.append(
                f"{prefix}{number:03}: {line}"
            )

        return {
            "status": "error",
            "error": str(e),
            "line_number": lineno,
            "highlight": "\n".join(highlighted),
            "traceback": compact_output(tb)
        }


# =========================================================
# WEB SEARCH
# =========================================================

def search_web(query: str) -> str:
    """
    Search the web using DuckDuckGo.

    Only a small number of results are returned
    to keep the LLM context small.
    """

    try:

        results = []

        with DDGS() as ddgs:

            search_results = ddgs.text(
                query,
                max_results=MAX_SEARCH_RESULTS
            )

            for index, result in enumerate(
                search_results,
                start=1
            ):

                title = result.get(
                    "title",
                    ""
                )

                body = result.get(
                    "body",
                    ""
                )

                link = result.get(
                    "href",
                    ""
                )

                results.append(
                    f"{index}. {title}\n"
                    f"{body}\n"
                    f"{link}"
                )

        if not results:
            return "No results found"

        return compact_output(
            "\n\n".join(results)
        )

    except Exception as e:
        return f"ERROR: {str(e)}"