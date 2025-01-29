import os
import platform
import re
import subprocess
from collections.abc import Sequence
from pathlib import Path

from packaging import version

from .dictionary.libreoffice import DEFAULT_PATHS, MIN_VERSION


class LibreOfficeConverter:
    """LibreOffice-based document converter."""

    def __init__(self, executable_path: str | None = None):
        """Initialize converter with optional executable path."""
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
        """
        Convert RTF file(s) to specified format using LibreOffice.

        Args:
            input_files: Path to input RTF file or list of paths.
            output_dir: Directory for output files.
            format: Output format (`'pdf'`, `'docx'`, or `'html'`).
            overwrite: Whether to overwrite existing output files.

        Returns:
            Path to converted file, or list of paths for multiple files.
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
