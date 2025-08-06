"""RTF Figure handling utilities.

This module provides functions for reading and processing images
for embedding in RTF documents.
"""

import mimetypes
from pathlib import Path
from typing import Union


def rtf_read_figure(
    file_paths: Union[str, Path, list[Union[str, Path]]],
) -> tuple[list[bytes], list[str]]:
    """Read image files and return their binary data with format information.

    This function reads image files from disk and prepares them for embedding
    in RTF documents. It supports PNG, JPEG, and EMF formats.

    Args:
        file_paths: Single file path or list of file paths to image files

    Returns:
        Tuple of (figure_data, figure_formats) where:
            - figure_data: List of image binary data as bytes
            - figure_formats: List of format strings ('png', 'jpeg', 'emf')

    Raises:
        FileNotFoundError: If any image file cannot be found
        ValueError: If image format is not supported
    """
    # Ensure file_paths is a list
    if isinstance(file_paths, (str, Path)):
        file_paths = [file_paths]

    figure_data = []
    figure_formats = []

    for file_path in file_paths:
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")

        # Determine format and read data
        img_format = _determine_image_format(path)
        data = _read_image_data(path)

        figure_data.append(data)
        figure_formats.append(img_format)

    return figure_data, figure_formats


def _determine_image_format(path: Path) -> str:
    """Determine image format from file extension or MIME type."""
    extension = path.suffix.lower()
    format_map = {".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg", ".emf": "emf"}

    if extension in format_map:
        return format_map[extension]

    # Fallback to MIME type detection
    mime_type, _ = mimetypes.guess_type(str(path))
    mime_to_format = {"image/png": "png", "image/jpeg": "jpeg", "image/jpg": "jpeg"}

    if mime_type in mime_to_format:
        return mime_to_format[mime_type]

    raise ValueError(
        f"Unsupported image format: {extension}. Supported formats: PNG, JPEG, EMF"
    )


def _read_image_data(path: Path) -> bytes:
    """Read binary data from image file."""
    with open(path, "rb") as f:
        return f.read()
