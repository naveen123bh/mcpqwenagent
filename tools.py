# =========================================
# TOOLS MODULE (MCP-READY CLEAN VERSION)
# =========================================

import sys
import io
import os
import shutil
import traceback
from ddgs import DDGS
import subprocess

# =========================
# FILE TOOLS
# =========================
def read_file(filename: str) -> str:
    """Read file content"""
    try:
        with open(filename, "r") as f:
            return f.read()
    except Exception as e:
        return f"ERROR: {str(e)}"


def write_file(filename: str, content: str) -> str:
    """Write content to file"""
    try:
        with open(filename, "w") as f:
            f.write(content)
        return f"Saved to {filename}"
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
# ADVANCED DEBUG TOOL (🔥 IMPORTANT)
# =========================
def debug_python(code: str) -> dict:
    """
    Run Python code and return structured debug info
    (line number + highlighted code)
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

        # Extract error line number
        import re
        match = re.search(r'File "<string>", line (\d+)', tb)
        lineno = int(match.group(1)) if match else None

        # Highlight code
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
# SHELL / OS TOOLS
# =========================
def run_shell(command: str) -> str:
    """Run shell command"""
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


def create_folder(foldername: str) -> str:
    """Create folder"""
    try:
        os.makedirs(foldername, exist_ok=True)
        return f"Folder '{foldername}' created"
    except Exception as e:
        return f"ERROR: {str(e)}"


def delete_file(filename: str) -> str:
    """Delete file"""
    try:
        os.remove(filename)
        return f"{filename} deleted"
    except Exception as e:
        return f"ERROR: {str(e)}"


def move_file(src: str, dst: str) -> str:
    """Move file"""
    try:
        shutil.move(src, dst)
        return f"{src} moved to {dst}"
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