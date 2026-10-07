import os
import subprocess
import sys
from pathlib import Path


def run_tests(project_path):
    """Run pytest using the same Python environment as the agent."""

    project_path = Path(project_path).resolve()

    # Keep the Python paths that are already working for this interpreter.
    python_paths = [
        path
        for path in sys.path
        if path
    ]

    # Make sure the sample project itself is available to the tests.
    python_paths.insert(0, str(project_path))

    environment = os.environ.copy()

    # Explicitly provide the paths needed by the child Python process.
    environment["PYTHONPATH"] = os.pathsep.join(python_paths)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ],
        cwd=str(project_path),
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    )

    return {
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.returncode == 0,
    }


if __name__ == "__main__":
    result = run_tests("sample_project")

    if result["stdout"]:
        print(result["stdout"])

    if result["stderr"]:
        print(result["stderr"])

    if result["success"]:
        print("Tests passed.")
    else:
        print("Tests failed.")