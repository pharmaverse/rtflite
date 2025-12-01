from abc import ABC, abstractmethod
from typing import Any

import polars as pl
from pydantic import BaseModel, ConfigDict, Field

from ...attributes import TableAttributes
from ...input import RTFBody, RTFPage


class PageContext(BaseModel):
    """Holds all data and metadata required to render a single page."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Core Data
    page_number: int
    total_pages: int
    data: pl.DataFrame

    # Page State
    is_first_page: bool
    is_last_page: bool

    # Layout
    col_widths: list[float]

    # Content Flags
    needs_header: bool = True

    # Base attributes for the table body (sliced/processed)
    table_attrs: TableAttributes | None = None

    # Feature-specific Metadata (populated by strategies or processors)
    subline_header: dict[str, Any] | None = None
    pageby_header_info: dict[str, Any] | None = None
    group_boundaries: list[dict[str, Any]] | None = None

    # Finalized Attributes (populated by PageProcessor)
    # These override the document-level attributes for this specific page
    final_body_attrs: TableAttributes | None = None
    component_borders: dict[str, Any] = Field(default_factory=dict)


class PaginationContext(BaseModel):
    """Context passed to the strategy to perform pagination."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    df: pl.DataFrame
    rtf_body: RTFBody
    rtf_page: RTFPage
    col_widths: list[float]
    table_attrs: TableAttributes | None
    additional_rows_per_page: int = 0
    row_metadata: pl.DataFrame | None = None
    removed_column_indices: list[int] | None = None


class PaginationStrategy(ABC):
    """Abstract base class for pagination strategies."""

    @abstractmethod
    def paginate(self, context: PaginationContext) -> list[PageContext]:
        """Split the document into pages based on the strategy."""
        pass
