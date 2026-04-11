# =========================================
# TOOLS MODULE (MCP-READY SAFE VERSION)
# =========================================

import sys
import io
import os
import shutil
import traceback
from ddgs import DDGS
import subprocess

# =========================
# 🔒 SANDBOX CONFIG
# =========================
BASE_DIR = "workspace"

# Ensure workspace exists
os.makedirs(BASE_DIR, exist_ok=True)


def safe_path(path: str) -> str:
    """
    Prevent access outside workspace directory
    """
    full_path = os.path.abspath(os.path.join(BASE_DIR, path))

    if not full_path.startswith(os.path.abspath(BASE_DIR)):
        raise Exception("❌ Access denied خارج workspace")

    return full_path


# =========================
# FILE TOOLS
# =========================
def read_file(filename: str) -> str:
    """Read file content"""
    try:
        filename = safe_path(filename)
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"ERROR: {str(e)}"


def write_file(filename: str, content: str) -> str:
    """Write content to file"""
    try:
        filename = safe_path(filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Saved to {filename}"
    except Exception as e:
        return f"ERROR: {str(e)}"


def delete_file(filename: str) -> str:
    """Delete file"""
    try:
        filename = safe_path(filename)
        os.remove(filename)
        return f"{filename} deleted"
    except Exception as e:
        return f"ERROR: {str(e)}"


def move_file(src: str, dst: str) -> str:
    """Move file"""
    try:
        src = safe_path(src)
        dst = safe_path(dst)

        # Ensure destination folder exists
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        shutil.move(src, dst)
        return f"{src} moved to {dst}"
    except Exception as e:
        return f"ERROR: {str(e)}"


def create_folder(foldername: str) -> str:
    """Create folder"""
    try:
        foldername = safe_path(foldername)
        os.makedirs(foldername, exist_ok=True)
        return f"Folder '{foldername}' created"
    except Exception as e:
        return f"ERROR: {str(e)}"


def list_files(path: str = ".") -> str:
    """List files in directory"""
    try:
        path = safe_path(path)
        files = os.listdir(path)

        if not files:
            return "No files found"

        return "\n".join(files)
    except Exception as e:
        return f"ERROR: {str(e)}"


# =========================
# PYTHON EXECUTION
# =========================
def run_python(code: str) -> str:
    """
    Execute Python code safely and return output or error
    """
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    try:
        exec(code, {})
        return buffer.getvalue() or "No output"

    except Exception:
        return "ERROR:\n" + traceback.format_exc()

    finally:
        sys.stdout = old_stdout


# =========================
# ADVANCED DEBUG TOOL
# =========================
def debug_python(code: str) -> dict:
    """
    Run Python code and return structured debug info
    """
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    try:
        exec(code, {})
        return {
            "status": "success",
            "output": buffer.getvalue() or "No output"
        }

    except Exception as e:
        tb = traceback.format_exc()

        import re
        match = re.search(r'File "<string>", line (\d+)', tb)
        lineno = int(match.group(1)) if match else None

        code_lines = code.split("\n")
        visual = ""

        for i, line in enumerate(code_lines, 1):
            prefix = ">> " if i == lineno else "   "
            visual += f"{prefix}{i:03}: {line}\n"

        return {
            "status": "error",
            "error": str(e),
            "line_number": lineno,
            "highlight": visual,
            "traceback": tb
        }

    finally:
        sys.stdout = old_stdout


# =========================
# SHELL / OS TOOLS ⚠️
# =========================
def run_shell(command: str) -> str:
    """Run shell command (⚠️ use carefully)"""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True
        )

        if result.returncode == 0:
            return result.stdout.strip() or "No output"
        else:
            return f"ERROR: {result.stderr.strip()}"

    except Exception as e:
        return f"ERROR: {str(e)}"


# =========================
# SEARCH TOOL
# =========================
def search_web(query: str) -> str:
    """Search web using DuckDuckGo"""
    try:
        results_text = ""

        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=5)

            for i, r in enumerate(results, 1):
                title = r.get("title", "")
                body = r.get("body", "")
                link = r.get("href", "")

                results_text += (
                    f"{i}. {title}\n{body}\n{link}\n\n"
                )

        return results_text if results_text else "No results found"

    except Exception as e:
        return f"ERROR: {str(e)}"