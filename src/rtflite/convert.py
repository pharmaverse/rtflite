import os
import platform
import re
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from math import isfinite
from pathlib import Path

from .dictionary.libreoffice import DEFAULT_PATHS, MIN_VERSION


class LibreOfficeConverter:
    """Convert RTF documents to other formats using LibreOffice.

    Convert RTF files to various formats including PDF, DOCX, HTML, and others
    using LibreOffice in headless mode.

    Requirements:
        - LibreOffice 7.1 or later must be installed.
        - Automatically finds LibreOffice in standard installation paths.
        - For custom installations, provide `executable_path` parameter.

    Note:
        The converter runs LibreOffice in headless mode, so no GUI is required.
        This makes it suitable for server environments and automated workflows.
    """

    def __init__(
        self,
        executable_path: str | Path | None = None,
        *,
        timeout: float | None = 120,
    ) -> None:
        """Initialize converter with optional executable path.

        Args:
            executable_path: Path (or executable name) to LibreOffice. If None,
                searches standard installation locations for each platform.
            timeout: Maximum seconds for each LibreOffice process, including
                the version check. Defaults to 120. Use None to disable.

        Raises:
            FileNotFoundError: If LibreOffice executable cannot be found.
            ValueError: If timeout is invalid or the version cannot be parsed.
            RuntimeError: If LibreOffice is too old, fails to start, or times out.
        """
        if timeout is not None and (not isfinite(timeout) or timeout <= 0):
            raise ValueError("timeout must be a positive finite number or None.")
        self.timeout = timeout
        self.executable_path = self._resolve_executable_path(executable_path)

        self._verify_version()

    def _resolve_executable_path(self, executable_path: str | Path | None) -> Path:
        """Resolve the LibreOffice executable path."""
        if executable_path is None:
            found_executable = self._find_executable()
            if found_executable is None:
                raise FileNotFoundError("Can't find LibreOffice executable.")
            return found_executable

        executable = os.fspath(executable_path)
        expanded = os.path.expanduser(executable)
        candidate = Path(expanded)
        looks_like_path = (
            isinstance(executable_path, Path)
            or candidate.is_absolute()
            or os.sep in expanded
            or (os.altsep is not None and os.altsep in expanded)
        )
        if looks_like_path:
            if candidate.is_file():
                return candidate.absolute()
            raise FileNotFoundError(
                f"LibreOffice executable not found at: {candidate}."
            )

        resolved_executable = shutil.which(executable)
        if resolved_executable is None:
            raise FileNotFoundError(f"Can't find LibreOffice executable: {executable}.")
        return Path(resolved_executable).absolute()

    def _find_executable(self) -> Path | None:
        """Find LibreOffice executable in default locations."""
        system = platform.system()
        # Windows needs the console launcher to capture output and wait for exit.
        names: tuple[str, ...] = ("soffice", "libreoffice")
        if system == "Windows":
            names = ("soffice.com", *names)
        for name in names:
            resolved = shutil.which(name)
            if resolved is not None:
                return Path(resolved).absolute()

        if system not in DEFAULT_PATHS:
            raise RuntimeError(f"Unsupported operating system: {system}.")

        for path in DEFAULT_PATHS[system]:
            candidate = Path(path)
            if candidate.is_file():
                return candidate
        return None

    def _run_command(
        self, cmd: list[str], action: str
    ) -> subprocess.CompletedProcess[str]:
        """Run LibreOffice with bounded execution and useful diagnostics."""
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                errors="replace",
                check=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(
                f"LibreOffice {action} timed out after {self.timeout} seconds."
            ) from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"LibreOffice {action} failed (exit code {e.returncode}):\n"
                f"Command output: {e.stdout}\n"
                f"Error output: {e.stderr}"
            ) from e
        except OSError as e:
            raise RuntimeError(
                f"Failed to run LibreOffice at {self.executable_path}: {e}"
            ) from e

    def _verify_version(self) -> None:
        """Verify LibreOffice version meets minimum requirement."""
        result = self._run_command(
            [str(self.executable_path), "--version"], "version check"
        )
        version_str = result.stdout.strip()
        match = re.search(r"LibreOffice\s+(\d+\.\d+(?:\.\d+)*)", version_str)
        if not match:
            raise ValueError(f"Can't parse LibreOffice version from: {version_str}.")

        # LibreOffice uses numeric versions, including calendar versions (24+).
        # Compare numerically without requiring the optional packaging library.
        current_version = tuple(int(part) for part in match.group(1).split("."))
        min_version = tuple(int(part) for part in MIN_VERSION.split("."))
        if current_version < min_version:
            raise RuntimeError(
                f"LibreOffice version {match.group(1)} is below minimum required "
                f"version {MIN_VERSION}."
            )

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

                - `'pdf'`: Portable Document Format (default)
                - `'docx'`: Microsoft Word (Office Open XML)
                - `'doc'`: Microsoft Word 97-2003
                - `'html'`: HTML Document
                - `'odt'`: OpenDocument Text
                - `'txt'`: Plain Text

                Also accepts LibreOffice's `extension:filter[:options]` syntax,
                for example `'pdf:writer_pdf_Export'` or
                `'txt:Text (encoded):UTF8'`. Filter names and options are passed
                through unchanged; the extension determines the output filename.
            overwrite: If `True`, overwrites existing files in output directory.
                If `False`, raises error if output file already exists. Existing
                output is preserved if LibreOffice fails to convert the input.

        Returns:
            Path | Sequence[Path]: For single file input, returns Path to the
                converted file. For multiple files, returns list of Paths.

        Raises:
            FileNotFoundError: If an input file is missing or is not a file.
            FileExistsError: If output file exists and overwrite=False.
            ValueError: If format does not start with a valid file extension.
            RuntimeError: If LibreOffice conversion fails or times out.

        Note:
            Each file is converted with a temporary, isolated LibreOffice user
            profile, independent of an open desktop session or other conversions.
            Personal LibreOffice settings and extensions are not used. Batch
            inputs are processed sequentially, with a new process for each file.

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
        extension = format.split(":", 1)[0]
        if not re.fullmatch(r"[A-Za-z0-9]+", extension):
            raise ValueError(
                "format must be an extension or extension:filter[:options], "
                f"got {format!r}."
            )
        output_dir = Path(output_dir).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Handle single input file
        if isinstance(input_files, (str, Path)):
            input_path = Path(input_files).expanduser()
            if not input_path.is_file():
                raise FileNotFoundError(f"Input file not found: {input_path}.")
            return self._convert_single_file(input_path, output_dir, format, overwrite)

        # Handle multiple input files
        input_paths = [Path(f).expanduser() for f in input_files]
        for path in input_paths:
            if not path.is_file():
                raise FileNotFoundError(f"Input file not found: {path}.")

        return [
            self._convert_single_file(input_path, output_dir, format, overwrite)
            for input_path in input_paths
        ]

    def _convert_single_file(
        self, input_file: Path, output_dir: Path, format: str, overwrite: bool
    ) -> Path:
        """Convert a single file using LibreOffice."""
        extension = format.split(":", 1)[0]
        output_file = output_dir / f"{input_file.stem}.{extension}"

        if output_file.exists() and not overwrite:
            raise FileExistsError(
                f"Output file already exists: {output_file}. "
                "Use overwrite=True to force."
            )

        # Stage output so an old file cannot be mistaken for a successful export.
        # Keep it on the destination filesystem for the final file replacement.
        with tempfile.TemporaryDirectory(prefix=".rtflite-", dir=output_dir) as tmpdir:
            work_dir = Path(tmpdir).resolve()
            converted_dir = work_dir / "output"
            converted_dir.mkdir()
            cmd = [
                str(self.executable_path),
                f"-env:UserInstallation={(work_dir / 'profile').as_uri()}",
                "--headless",
                "--nologo",
                "--norestore",
                "--convert-to",
                format,
                "--outdir",
                str(converted_dir),
                str(input_file.absolute()),
            ]
            result = self._run_command(cmd, "conversion")
            converted_file = converted_dir / output_file.name
            if not converted_file.is_file():
                raise RuntimeError(
                    f"Conversion failed: Output file not created.\n"
                    f"Command output: {result.stdout}\n"
                    f"Error output: {result.stderr}"
                )

            # Include companion files/directories created by formats such as HTML.
            generated_paths = list(converted_dir.iterdir())
            if not overwrite:
                for path in generated_paths:
                    destination = output_dir / path.name
                    if destination.exists():
                        raise FileExistsError(
                            f"Output file already exists: {destination}. "
                            "Use overwrite=True to force."
                        )
            for path in generated_paths:
                if path == converted_file:
                    continue
                destination = output_dir / path.name
                if path.is_dir():
                    shutil.copytree(path, destination, dirs_exist_ok=overwrite)
                else:
                    path.replace(destination)
            converted_file.replace(output_file)

        return output_file
