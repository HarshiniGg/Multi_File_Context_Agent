import ast
from pathlib import Path


def summarize_file(file_path):
    """Create a simple summary of a Python file."""
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    functions = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)

    return {
        "file": str(file_path),
        "functions": functions,
    }


def scan_project(project_path):
    """Scan all Python files in the project and summarize them."""
    project_path = Path(project_path)

    summaries = []

    for file_path in sorted(project_path.glob("*.py")):
        summaries.append(summarize_file(file_path))

    return summaries


if __name__ == "__main__":
    summaries = scan_project("sample_project")

    for summary in summaries:
        print(f"\nFile: {summary['file']}")
        print(f"Functions: {', '.join(summary['functions'])}")