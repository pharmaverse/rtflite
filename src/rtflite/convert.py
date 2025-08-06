import os
import platform
import re
import subprocess
from collections.abc import Sequence
from pathlib import Path

from packaging import version

from .dictionary.libreoffice import DEFAULT_PATHS, MIN_VERSION


class LibreOfficeConverter:
    """Convert RTF documents to other formats using LibreOffice.

    The LibreOfficeConverter enables conversion of RTF files to various formats
    including PDF, DOCX, HTML, and others using LibreOffice in headless mode.
    It automatically detects LibreOffice installation on Windows, macOS, and Linux.

    Examples:
        Basic PDF conversion:
        ```python
        from rtflite import LibreOfficeConverter

        converter = LibreOfficeConverter()
        converter.convert("report.rtf", format="pdf")
        # Creates report.pdf in the same directory
        ```

        Convert multiple files to specific directory:
        ```python
        converter = LibreOfficeConverter()
        converter.convert(
            input_files=["report1.rtf", "report2.rtf"],
            output_dir="pdf_output/",
            format="pdf",
            overwrite=True
        )
        ```

        Convert to Word format:
        ```python
        converter.convert("report.rtf", format="docx")
        # Creates report.docx
        ```

    Supported Formats:
        - pdf: Portable Document Format
        - docx: Microsoft Word (Office Open XML)
        - doc: Microsoft Word 97-2003
        - html: HTML Document
        - odt: OpenDocument Text
        - txt: Plain Text

    Requirements:
        - LibreOffice 7.3 or later must be installed
        - Automatically finds LibreOffice in standard installation paths
        - For custom installations, provide executable_path parameter

    Note:
        The converter runs LibreOffice in headless mode, so no GUI is required.
        This makes it suitable for server environments and automated workflows.
    """

    def __init__(self, executable_path: str | None = None):
        """Initialize converter with optional executable path.

        Args:
            executable_path: Path to LibreOffice executable. If None, searches
                standard installation locations for each platform.

        Raises:
            FileNotFoundError: If LibreOffice executable cannot be found.
            ValueError: If LibreOffice version is below minimum requirement.
        """
        self.executable_path = executable_path or self._find_executable()
        if not self.executable_path:
            raise FileNotFoundError("Can't find LibreOffice executable.")

        self._verify_version()

    def _find_executable(self) -> str | None:
        """Find LibreOffice executable in default locations."""
        system = platform.system()
        if system not in DEFAULT_PATHS:
            raise RuntimeError(f"Unsupported operating system: {system}.")

        for path in DEFAULT_PATHS[system]:
            if os.path.isfile(path):
                return path
        return None

    def _verify_version(self):
        """Verify LibreOffice version meets minimum requirement."""
        try:
            result = subprocess.run(
                [self.executable_path, "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            version_str = result.stdout.strip()
            # Extract version number (for example, "24.8.3.2" from the output)
            match = re.search(r"LibreOffice (\d+\.\d+)", version_str)
            if not match:
                raise ValueError(
                    f"Can't parse LibreOffice version from: {version_str}."
                )

            current_version = version.parse(match.group(1))
            min_version = version.parse(MIN_VERSION)

            if current_version < min_version:
                raise RuntimeError(
                    f"LibreOffice version {current_version} is below minimum required version {min_version}."
                )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get LibreOffice version: {e}.")

    def convert(
        self,
        input_files: str | Path | Sequence[str | Path],
        output_dir: str | Path,
        format: str = "pdf",
        overwrite: bool = False,
    ) -> Path | Sequence[Path]:
        """Convert RTF file(s) to specified format using LibreOffice.

        Performs the actual conversion of RTF files to the target format using
        LibreOffice in headless mode. Supports single file or batch conversion.

        Args:
            input_files: Path to input RTF file or list of paths. Can be string
                or Path object. For batch conversion, provide a list/tuple.
            output_dir: Directory where converted files will be saved. Created
                if it doesn't exist. Can be string or Path object.
            format: Target format for conversion. Supported formats:
                - 'pdf': Portable Document Format (default)
                - 'docx': Microsoft Word (Office Open XML)
                - 'doc': Microsoft Word 97-2003
                - 'html': HTML Document
                - 'odt': OpenDocument Text
                - 'txt': Plain Text
            overwrite: If True, overwrites existing files in output directory.
                If False, raises error if output file already exists.

        Returns:
            Path | Sequence[Path]: For single file input, returns Path to the
                converted file. For multiple files, returns list of Paths.

        Raises:
            FileExistsError: If output file exists and overwrite=False.
            RuntimeError: If LibreOffice conversion fails.

        Examples:
            Single file conversion:
            ```python
            converter = LibreOfficeConverter()
            pdf_path = converter.convert(
                "report.rtf",
                output_dir="pdfs/",
                format="pdf"
            )
            print(f"Created: {pdf_path}")
            ```

            Batch conversion with overwrite:
            ```python
            rtf_files = ["report1.rtf", "report2.rtf", "report3.rtf"]
            pdf_paths = converter.convert(
                input_files=rtf_files,
                output_dir="output/pdfs/",
                format="pdf",
                overwrite=True
            )
            for path in pdf_paths:
                print(f"Converted: {path}")
            ```
        """
        output_dir = Path(os.path.expanduser(str(output_dir)))
        if not output_dir.exists():
            output_dir.mkdir(parents=True)

        # Handle single input file
        if isinstance(input_files, (str, Path)):
            input_path = Path(os.path.expanduser(str(input_files)))
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_path}.")
            return self._convert_single_file(input_path, output_dir, format, overwrite)

        # Handle multiple input files
        input_paths = [Path(os.path.expanduser(str(f))) for f in input_files]
        for path in input_paths:
            if not path.exists():
                raise FileNotFoundError(f"Input file not found: {path}.")

        return [
            self._convert_single_file(input_path, output_dir, format, overwrite)
            for input_path in input_paths
        ]

    def _convert_single_file(
        self, input_file: Path, output_dir: Path, format: str, overwrite: bool
    ) -> Path:
        """Convert a single file using LibreOffice."""
        output_file = output_dir / f"{input_file.stem}.{format}"

        if output_file.exists() and not overwrite:
            raise FileExistsError(
                f"Output file already exists: {output_file}. Use overwrite=True to force."
            )

        cmd = [
            self.executable_path,
            "--invisible",
            "--headless",
            "--nologo",
            "--convert-to",
            format,
            "--outdir",
            str(output_dir),
            str(input_file),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if not output_file.exists():
                raise RuntimeError(
                    f"Conversion failed: Output file not created.\n"
                    f"Command output: {result.stdout}\n"
                    f"Error output: {result.stderr}"
                )

            return output_file

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"LibreOffice conversion failed:\n"
                f"Command output: {e.stdout}\n"
                f"Error output: {e.stderr}"
            )
