import json
import os

from dotenv import load_dotenv
from groq import Groq

from project_scanner import scan_project
from prompts import SYSTEM_PROMPT, build_user_prompt
from editor import read_file, write_file
from executor import run_tests

load_dotenv()


def get_client():
    """Create the Groq client using the API key from .env."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Check your .env file."
        )

    return Groq(api_key=api_key)


def identify_files(instruction, project_path="sample_project"):
    """Ask the LLM which files need to be changed."""

    project_context = scan_project(project_path)

    prompt = build_user_prompt(
        instruction,
        project_context
    )

    client = get_client()

    response = client.chat.completions.create(
        model=os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        ),
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)

    except json.JSONDecodeError:
        raise RuntimeError(
            f"The LLM did not return valid JSON:\n{content}"
        )


def generate_file_edit(file_path, instruction):
    """Ask the LLM to generate the complete updated file."""

    original_content = read_file(file_path)

    edit_prompt = f'''
You are editing a Python project.

User instruction:
{instruction}

File to edit:
{file_path}

Current file contents:
{original_content}

Return ONLY the complete updated contents of this file.

Do not use Markdown code fences.
Do not explain anything.

Preserve all existing functionality unless the instruction
requires a change.
'''

    client = get_client()

    response = client.chat.completions.create(
        model=os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        ),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful Python software engineer. "
                    "Return only the complete updated file contents."
                ),
            },
            {
                "role": "user",
                "content": edit_prompt,
            },
        ],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```python"):
        content = content[len("```python"):].strip()

    if content.startswith("```"):
        content = content[3:].strip()

    if content.endswith("```"):
        content = content[:-3].strip()

    return content


def edit_project(instruction, project_path="sample_project"):
    """Identify, edit, back up, and update all required files."""

    result = identify_files(
        instruction,
        project_path
    )

    files_to_edit = result.get("files_to_edit", [])

    if not files_to_edit:
        print("\nNo files need to be changed.")
        return []

    print("\nFiles identified for editing:")
    print("=" * 40)

    changed_files = []

    for file_info in files_to_edit:

        file_path = file_info["file"]
        reason = file_info["reason"]

        print(f"\nFile: {file_path}")
        print(f"Reason: {reason}")

        new_content = generate_file_edit(
            file_path,
            instruction
        )

        backup_path = write_file(
            file_path,
            new_content
        )

        changed_files.append(
            {
                "file": file_path,
                "backup": str(backup_path),
            }
        )

        print(f"Backup created: {backup_path}")
        print("File updated successfully.")

    return changed_files


def run_project_tests(project_path="sample_project"):
    """Run the project tests and display the result."""

    print("\nRunning tests...")
    print("=" * 40)

    test_result = run_tests(project_path)

    if test_result["stdout"]:
        print(test_result["stdout"])

    if test_result["stderr"]:
        print(test_result["stderr"])

    if test_result["success"]:
        print("ALL TESTS PASSED")
    else:
        print("TESTS FAILED")

    return test_result


if __name__ == "__main__":

    instruction = (
        "Add input validation to the divide function so it raises "
        "ValueError on division by zero, and update the test file "
        "to test for it."
    )

    print("\nMulti-File Context Agent")
    print("=" * 40)

    print("\nUser instruction:")
    print(instruction)

    changed_files = edit_project(
        instruction,
        "sample_project"
    )

    if changed_files:

        print("\nFiles changed successfully:")
        print("=" * 40)

        for item in changed_files:
            print(f"- {item['file']}")

        print("\nBackups created:")
        print("=" * 40)

        for item in changed_files:
            print(f"- {item['backup']}")

        run_project_tests(
            "sample_project"
        )

        print("\nAgent execution completed.")