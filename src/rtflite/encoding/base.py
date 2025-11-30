from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..encode import RTFDocument


class EncodingStrategy(ABC):
    """Abstract base class for RTF encoding strategies."""

    @abstractmethod
    def encode(self, document: "RTFDocument") -> str:
        """Encode the document using this strategy.

        Args:
            document: The RTF document to encode

        Returns:
            Complete RTF string
        """
        pass
