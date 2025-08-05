import re
import shutil
import subprocess
from pathlib import Path


def extract_r_tests(test_files):
    """Extract R code from Python test comments and generate R script.

    Args:
        test_files: A string or list of strings containing paths to Python test files.
    """
    if isinstance(test_files, str):
        test_files = [test_files]

    # Clean and create output directory
    output_dir = Path("tests/fixtures/r_outputs")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate R script
    r_script = []

    for test_file in test_files:
        with open(test_file, "r") as f:
            content = f.read()

        # Find all R code chunks with labels
        r_chunks = re.findall(
            r"#\s*```\{r,\s*([^}]+)\}(.*?)#\s*```", content, re.DOTALL
        )

        # Get test filename without extension
        test_name = Path(test_file).stem

        for label, code in r_chunks:
            label = label.strip()
            output_file = output_dir / f"{test_name}_{label}.rtf"

            # Clean up the code by properly handling comment markers
            # Lines may be indented and have "# " that needs to be removed
            # After removing "# ", lines starting with "#" are R comments
            # Other lines are R code
            code_lines = []
            for line in code.strip().split("\n"):
                line = line.rstrip()

                # Skip completely empty lines
                if not line.strip():
                    continue

                # Find the "# " pattern (may be after indentation)
                # Look for the pattern of whitespace followed by "# "
                match = re.match(r"^(\s*)# (.*)$", line)
                if match:
                    indent, content = match.groups()
                    # Keep the original indentation, but remove the "# " part
                    cleaned_line = indent + content
                elif re.match(r"^(\s*)#$", line):
                    # Handle lines that are just whitespace + "#" (empty comment lines)
                    continue  # Skip empty comment lines
                else:
                    # This shouldn't happen in well-formed R blocks, but handle it
                    cleaned_line = line

                # Now check if the content (after indentation) starts with "#"
                content_part = cleaned_line.lstrip()
                if content_part.startswith("#"):
                    # This is an R comment - keep as is
                    pass
                elif content_part.strip() == "":
                    # Empty line - skip
                    continue
                else:
                    # This is R code - keep as is
                    pass

                # Add non-empty lines
                if cleaned_line.strip():
                    code_lines.append(cleaned_line)

            clean_code = "\n".join(code_lines)

            r_script.append(f"""
            output_{test_name}_{label} <- capture.output({{
            {clean_code}
            }})
            cat(paste(output_{test_name}_{label}, collapse = "\\n"), file = "{output_file}")
            """)

    # Write R script
    with open("tests/fixtures/r_tests.R", "w") as f:
        f.write("\n".join(r_script))


def execute_r_tests():
    """Execute the generated R script using `Rscript`."""
    # Get the project root directory (one level up from tests/)
    project_root = Path(__name__).parent.parent.parent
    r_script_path = Path("tests/fixtures/r_tests.R")

    # Run Rscript command from project root
    try:
        subprocess.run(["Rscript", str(r_script_path)], check=True, cwd=project_root)
    except subprocess.CalledProcessError as e:
        print(f"Error executing R script: {e}")
        raise
    finally:
        # Remove the R script after execution
        (project_root / r_script_path).unlink()


if __name__ == "__main__":
    extract_r_tests(
        [
            "tests/test_row.py",
            "tests/test_input.py",
            "tests/test_convert.py",
            "tests/test_single_page_rtf.py",
            "tests/test_pagination.py",
        ],
    )
    execute_r_tests()
