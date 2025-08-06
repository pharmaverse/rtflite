"""RTF Figure encoding service.

This module provides services for encoding images into RTF format.
"""

from typing import Optional

from ..figure import rtf_read_figure
from ..input import RTFFigure


class RTFFigureService:
    """Service for encoding figures/images in RTF format."""

    @staticmethod
    def encode_figure(rtf_figure: Optional[RTFFigure]) -> str:
        """Encode figure component to RTF.

        Args:
            rtf_figure: RTFFigure object containing image file paths and settings

        Returns:
            RTF string containing encoded figures
        """
        if rtf_figure is None or rtf_figure.figures is None:
            return ""

        # Read figure data and formats from file paths
        figure_data_list, figure_formats = rtf_read_figure(rtf_figure.figures)

        rtf_output = []

        for i, (figure_data, figure_format) in enumerate(
            zip(figure_data_list, figure_formats)
        ):
            # Get dimensions for this figure
            width = RTFFigureService._get_dimension(rtf_figure.fig_width, i)
            height = RTFFigureService._get_dimension(rtf_figure.fig_height, i)

            # Encode single figure
            figure_rtf = RTFFigureService._encode_single_figure(
                figure_data, figure_format, width, height, rtf_figure.fig_align
            )
            rtf_output.append(figure_rtf)

            # Add page break between figures (each figure on separate page)
            if i < len(figure_data_list) - 1:
                rtf_output.append("\\page ")

        # Final paragraph after all figures
        rtf_output.append("\\par ")

        return "".join(rtf_output)

    @staticmethod
    def _get_dimension(dimension: float | list[float], index: int) -> float:
        """Get dimension for specific figure index."""
        if isinstance(dimension, list):
            return dimension[index] if index < len(dimension) else dimension[-1]
        return dimension

    @staticmethod
    def _encode_single_figure(
        figure_data: bytes,
        figure_format: str,
        width: float,
        height: float,
        alignment: str,
    ) -> str:
        """Encode a single figure to RTF format."""
        rtf_parts = []

        # Add alignment
        alignment_map = {"center": "\\qc ", "right": "\\qr ", "left": "\\ql "}
        rtf_parts.append(alignment_map.get(alignment, "\\ql "))

        # Start picture group
        rtf_parts.append("{\\pict")

        # Add format specifier
        format_map = {"png": "\\pngblip", "jpeg": "\\jpegblip", "emf": "\\emfblip"}
        rtf_parts.append(format_map.get(figure_format, "\\pngblip"))

        # Get dimensions
        pic_width, pic_height = RTFFigureService._get_image_dimensions(
            figure_data, figure_format
        )
        if pic_width is None:
            # Fallback: use 96 DPI assumption
            pic_width = int(width * 96)
            pic_height = int(height * 96)

        # Convert display dimensions to twips
        width_twips = int(width * 1440)
        height_twips = int(height * 1440)

        # Add dimensions
        rtf_parts.extend(
            [
                f"\\picw{pic_width}",
                f"\\pich{pic_height}",
                f"\\picwgoal{width_twips}",
                f"\\pichgoal{height_twips}",
            ]
        )

        # Add hex data
        rtf_parts.append(" ")
        rtf_parts.append(RTFFigureService._binary_to_hex(figure_data))
        rtf_parts.append("}")

        return "".join(rtf_parts)

    @staticmethod
    def _binary_to_hex(data: bytes) -> str:
        """Convert binary data to hexadecimal string for RTF.

        Args:
            data: Binary image data

        Returns:
            Hexadecimal string representation
        """
        # Convert each byte to 2-digit hex
        hex_string = data.hex()

        # RTF typically expects line breaks every 80 characters or so
        # This helps with readability but is not strictly required
        line_length = 80
        lines = []
        for i in range(0, len(hex_string), line_length):
            lines.append(hex_string[i : i + line_length])

        return "\n".join(lines)

    @staticmethod
    def _get_image_dimensions(
        data: bytes, format: str
    ) -> tuple[int | None, int | None]:
        """Extract actual pixel dimensions from image data.

        Args:
            data: Image binary data
            format: Image format ('png', 'jpeg', 'emf')

        Returns:
            Tuple of (width, height) in pixels, or (None, None) if unable to extract
        """
        try:
            if format == "png":
                return RTFFigureService._get_png_dimensions(data)
            elif format == "jpeg":
                return RTFFigureService._get_jpeg_dimensions(data)
        except Exception:
            pass

        return None, None

    @staticmethod
    def _get_png_dimensions(data: bytes) -> tuple[int | None, int | None]:
        """Extract dimensions from PNG data."""
        if len(data) > 24 and data[:8] == b"\x89PNG\r\n\x1a\n":
            import struct

            width = struct.unpack(">I", data[16:20])[0]
            height = struct.unpack(">I", data[20:24])[0]
            return width, height
        return None, None

    @staticmethod
    def _get_jpeg_dimensions(data: bytes) -> tuple[int | None, int | None]:
        """Extract dimensions from JPEG data."""
        if len(data) < 10 or data[:2] != b"\xff\xd8":
            return None, None

        import struct

        i = 2
        while i < len(data) - 9:
            if data[i] == 0xFF:
                marker = data[i + 1]
                # SOF markers contain dimension info
                sof_markers = {
                    0xC0,
                    0xC1,
                    0xC2,
                    0xC3,
                    0xC5,
                    0xC6,
                    0xC7,
                    0xC9,
                    0xCA,
                    0xCB,
                    0xCD,
                    0xCE,
                    0xCF,
                }
                if marker in sof_markers:
                    height = struct.unpack(">H", data[i + 5 : i + 7])[0]
                    width = struct.unpack(">H", data[i + 7 : i + 9])[0]
                    return width, height
                # Skip to next marker
                length = struct.unpack(">H", data[i + 2 : i + 4])[0]
                i += 2 + length
            else:
                i += 1
        return None, None
