"""RTF encoding engine for orchestrating document generation."""

from typing import TYPE_CHECKING

from .unified_encoder import UnifiedRTFEncoder

if TYPE_CHECKING:
    from ..encode import RTFDocument


class RTFEncodingEngine:
    """Main engine for RTF document encoding.

    This class orchestrates the encoding process using the UnifiedRTFEncoder
    which implements the strategy pattern for pagination and rendering.
    """

    def __init__(self):
        self._encoder = UnifiedRTFEncoder()

    def encode_document(self, document: "RTFDocument") -> str:
        """Encode an RTF document using the unified encoder.

        Args:
            document: The RTF document to encode

        Returns:
            Complete RTF string
        """
        return self._encoder.encode(document)
