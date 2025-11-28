"""RTF encoding service that handles document component encoding."""

from collections.abc import Sequence

from .grouping_service import grouping_service


class RTFEncodingService:
    """Service class that handles RTF component encoding operations.

    This class extracts encoding logic from RTFDocument to improve separation
    of concerns and enable better testing and maintainability.
    """

    def __init__(self):
        from ..rtf import RTFSyntaxGenerator

        self.syntax = RTFSyntaxGenerator()

    def encode_spanning_row(
        self,
        text: str,
        page_width: float,
        rtf_body_attrs=None,
    ) -> Sequence[str]:
        """Generate a spanning table row (single cell spanning full width).

        This is used for page_by group headers that span across all columns.
        Works for both single-page and paginated documents.

        Args:
            text: Text to display in the spanning row
            page_width: Total page width in inches
            rtf_body_attrs: RTFBody attributes for styling (optional)

        Returns:
            List of RTF strings for the spanning row
        """
        from ..row import Border, Cell, Row, TextContent

        # Use body attributes if provided, otherwise use defaults
        if rtf_body_attrs:
            font = rtf_body_attrs.text_font[0][0] if rtf_body_attrs.text_font else 0
            size = (
                rtf_body_attrs.text_font_size[0][0]
                if rtf_body_attrs.text_font_size
                else 18
            )
            text_format = (
                rtf_body_attrs.text_format[0][0] if rtf_body_attrs.text_format else ""
            )
            color = rtf_body_attrs.text_color[0][0] if rtf_body_attrs.text_color else ""
            bg_color = (
                rtf_body_attrs.text_background_color[0][0]
                if rtf_body_attrs.text_background_color
                else ""
            )
            justification = (
                rtf_body_attrs.text_justification[0][0]
                if rtf_body_attrs.text_justification
                else "c"
            )
            border_left = (
                rtf_body_attrs.border_left[0][0]
                if rtf_body_attrs.border_left
                else "single"
            )
            border_right = (
                rtf_body_attrs.border_right[0][0]
                if rtf_body_attrs.border_right
                else "single"
            )
            border_top = (
                rtf_body_attrs.border_top[0][0]
                if rtf_body_attrs.border_top
                else "single"
            )
            border_bottom = (
                rtf_body_attrs.border_bottom[0][0]
                if rtf_body_attrs.border_bottom
                else "single"
            )
            v_just = (
                rtf_body_attrs.cell_vertical_justification[0][0]
                if rtf_body_attrs.cell_vertical_justification
                else "b"
            )
            cell_just = (
                rtf_body_attrs.cell_justification[0][0]
                if rtf_body_attrs.cell_justification
                else "c"
            )
        else:
            font = 0
            size = 18
            text_format = ""
            color = ""
            bg_color = ""
            justification = "c"
            border_left = "single"
            border_right = "single"
            border_top = "single"
            border_bottom = "single"
            v_just = "b"
            cell_just = "c"

        # Create spanning cell
        cell = Cell(
            text=TextContent(
                text=text,
                font=font,
                size=size,
                format=text_format,
                color=color,
                background_color=bg_color,
                justification=justification,
                indent_first=0,
                indent_left=0,
                indent_right=0,
                space=0,  # No line spacing
                space_before=15,
                space_after=15,
                convert=False,
                hyphenation=True,
            ),
            width=page_width,
            border_left=Border(style=border_left),
            border_right=Border(style=border_right),
            border_top=Border(style=border_top),
            border_bottom=Border(style=border_bottom),
            vertical_justification=v_just,
        )

        # Create row with single spanning cell
        row = Row(row_cells=[cell], justification=cell_just, height=0)

        return row._as_rtf()

    def encode_document_start(self) -> str:
        """Encode RTF document start."""
        return "{\\rtf1\\ansi\n\\deff0\\deflang1033"

    def encode_font_table(self) -> str:
        """Encode RTF font table."""
        return self.syntax.generate_font_table()

    def encode_color_table(
        self, document=None, used_colors: Sequence[str] | None = None
    ) -> str:
        """Encode RTF color table with comprehensive 657-color support.

        Args:
            document: RTF document to analyze for color usage (preferred)
            used_colors: Color names used in the document. If None and a
                document is provided, colors are auto-detected.

        Returns:
            RTF color table string (empty if no colors beyond black/"" are used)
        """
        if document is not None and used_colors is None:
            # Auto-detect colors from document
            from ..services.color_service import color_service

            used_colors = color_service.collect_document_colors(document)

        return self.syntax.generate_color_table(used_colors)

    def encode_page_settings(self, page_config) -> str:
        """Encode RTF page settings.

        Args:
            page_config: RTFPage configuration object

        Returns:
            RTF page settings string
        """
        return self.syntax.generate_page_settings(
            page_config.width,
            page_config.height,
            page_config.margin,
            page_config.orientation,
        )

    def encode_page_header(self, header_config, method: str = "line") -> str:
        """Encode page header component.

        Args:
            header_config: RTFPageHeader configuration
            method: Encoding method

        Returns:
            RTF header string
        """
        if header_config is None or not header_config.text:
            return ""

        # Use the existing text encoding method
        result = header_config._encode_text(text=header_config.text, method=method)

        return f"{{\\header{result}}}"

    def encode_page_footer(self, footer_config, method: str = "line") -> str:
        """Encode page footer component.

        Args:
            footer_config: RTFPageFooter configuration
            method: Encoding method

        Returns:
            RTF footer string
        """
        if footer_config is None or not footer_config.text:
            return ""

        # Use the existing text encoding method
        result = footer_config._encode_text(text=footer_config.text, method=method)
        return f"{{\\footer{result}}}"

    def encode_title(self, title_config, method: str = "line") -> str:
        """Encode title component.

        Args:
            title_config: RTFTitle configuration
            method: Encoding method

        Returns:
            RTF title string
        """
        if not title_config or not title_config.text:
            return ""

        # Use the existing text encoding method
        return title_config._encode_text(text=title_config.text, method=method)

    def encode_subline(self, subline_config, method: str = "line") -> str:
        """Encode subline component.

        Args:
            subline_config: RTFSubline configuration
            method: Encoding method

        Returns:
            RTF subline string
        """
        if subline_config is None or not subline_config.text:
            return ""

        # Use the existing text encoding method
        return subline_config._encode_text(text=subline_config.text, method=method)

    def encode_footnote(
        self,
        footnote_config,
        page_number: int | None = None,
        page_col_width: float | None = None,
    ) -> Sequence[str]:
        """Encode footnote component with advanced formatting.

        Args:
            footnote_config: RTFFootnote configuration
            page_number: Page number for footnote
            page_col_width: Page column width for calculations

        Returns:
            List of RTF footnote strings
        """
        if footnote_config is None:
            return []

        rtf_attrs = footnote_config

        # Apply page-specific border if set
        if (
            hasattr(rtf_attrs, "_page_border_style")
            and page_number is not None
            and page_number in rtf_attrs._page_border_style
        ):
            border_style = rtf_attrs._page_border_style[page_number]
            # Create a copy with modified border
            rtf_attrs = rtf_attrs.model_copy()
            rtf_attrs.border_bottom = [[border_style]]

        # Check if footnote should be rendered as table or paragraph
        if hasattr(rtf_attrs, "as_table") and not rtf_attrs.as_table:
            # Render as paragraph (plain text)
            if isinstance(rtf_attrs.text, list):
                text_list = rtf_attrs.text
            else:
                text_list = [rtf_attrs.text] if rtf_attrs.text else []

            # Use TextAttributes._encode_text method directly for paragraph rendering
            return rtf_attrs._encode_text(text_list, method="paragraph")
        else:
            # Render as table (default behavior)
            if page_col_width is not None:
                from ..row import Utils

                col_total_width = page_col_width
                col_widths = Utils._col_widths(rtf_attrs.col_rel_width, col_total_width)

                # Create DataFrame from text string
                import polars as pl

                df = pl.DataFrame([[rtf_attrs.text]])
                return rtf_attrs._encode(df, col_widths)
            else:
                # Fallback without column width calculations
                import polars as pl

                df = pl.DataFrame([[rtf_attrs.text]])
                return rtf_attrs._encode(df)

    def encode_source(
        self,
        source_config,
        page_number: int | None = None,
        page_col_width: float | None = None,
    ) -> Sequence[str]:
        """Encode source component with advanced formatting.

        Args:
            source_config: RTFSource configuration
            page_number: Page number for source
            page_col_width: Page column width for calculations

        Returns:
            List of RTF source strings
        """
        if source_config is None:
            return []

        rtf_attrs = source_config

        # Apply page-specific border if set
        if (
            hasattr(rtf_attrs, "_page_border_style")
            and page_number is not None
            and page_number in rtf_attrs._page_border_style
        ):
            border_style = rtf_attrs._page_border_style[page_number]
            # Create a copy with modified border
            rtf_attrs = rtf_attrs.model_copy()
            rtf_attrs.border_bottom = [[border_style]]

        # Check if source should be rendered as table or paragraph
        if hasattr(rtf_attrs, "as_table") and not rtf_attrs.as_table:
            # Render as paragraph (plain text)
            if isinstance(rtf_attrs.text, list):
                text_list = rtf_attrs.text
            else:
                text_list = [rtf_attrs.text] if rtf_attrs.text else []

            # Use TextAttributes._encode_text method directly for paragraph rendering
            return rtf_attrs._encode_text(text_list, method="paragraph")
        else:
            # Render as table (default behavior)
            if page_col_width is not None:
                from ..row import Utils

                col_total_width = page_col_width
                col_widths = Utils._col_widths(rtf_attrs.col_rel_width, col_total_width)

                # Create DataFrame from text string
                import polars as pl

                df = pl.DataFrame([[rtf_attrs.text]])
                return rtf_attrs._encode(df, col_widths)
            else:
                # Fallback without column width calculations
                import polars as pl

                df = pl.DataFrame([[rtf_attrs.text]])
                return rtf_attrs._encode(df)

    def prepare_dataframe_for_body_encoding(self, df, rtf_attrs):
        """Prepare DataFrame for body encoding with group_by and column removal.

        Args:
            df: Input DataFrame
            rtf_attrs: RTFBody attributes

        Returns:
            Tuple of (processed_df, original_df) where processed_df has
            transformations applied
        """
        original_df = df.clone()
        processed_df = df.clone()

        # Collect columns to remove
        columns_to_remove = set()

        # Remove subline_by columns from the processed DataFrame
        if rtf_attrs.subline_by is not None:
            columns_to_remove.update(rtf_attrs.subline_by)

        # Remove page_by columns from table display
        # page_by columns are shown as spanning rows, not as table columns
        # The new_page flag only controls whether to force page breaks at group
        # boundaries
        if rtf_attrs.page_by is not None:
            columns_to_remove.update(rtf_attrs.page_by)

        # Apply column removal if any columns need to be removed
        if columns_to_remove:
            remaining_columns = [
                col for col in processed_df.columns if col not in columns_to_remove
            ]
            processed_df = processed_df.select(remaining_columns)

            # Update col_rel_width to match the new column count
            # Find indices of removed columns to remove corresponding width entries
            if rtf_attrs.col_rel_width is not None and len(
                rtf_attrs.col_rel_width
            ) == len(original_df.columns):
                removed_indices = [
                    i
                    for i, col in enumerate(original_df.columns)
                    if col in columns_to_remove
                ]
                # Create new col_rel_width with removed column widths excluded
                new_col_rel_width = [
                    width
                    for i, width in enumerate(rtf_attrs.col_rel_width)
                    if i not in removed_indices
                ]
                # Update rtf_attrs with new col_rel_width
                rtf_attrs.col_rel_width = new_col_rel_width

        # Note: group_by suppression is handled in the pagination strategy
        # for documents that need pagination. For non-paginated documents,
        # group_by is handled separately in encode_body method.

        return processed_df, original_df

    def encode_body(
        self, document, df, rtf_attrs, force_single_page=False
    ) -> Sequence[str] | None:
        """Encode table body component with full pagination support.

        Args:
            document: RTFDocument instance for accessing pagination logic
            df: DataFrame containing table data
            rtf_attrs: RTFBody attributes

        Returns:
            List of RTF body strings
        """
        if rtf_attrs is None:
            return None

        # Initialize dimensions and widths
        from ..row import Utils
        from .document_service import RTFDocumentService

        document_service = RTFDocumentService()
        col_total_width = document.rtf_page.col_width

        # Validate data sorting for all grouping parameters
        if any([rtf_attrs.group_by, rtf_attrs.page_by, rtf_attrs.subline_by]):
            grouping_service.validate_data_sorting(
                df,
                group_by=rtf_attrs.group_by,
                page_by=rtf_attrs.page_by,
                subline_by=rtf_attrs.subline_by,
            )

        # Validate subline_by formatting consistency and issue warnings
        if rtf_attrs.subline_by is not None:
            import warnings

            formatting_warnings = (
                grouping_service.validate_subline_formatting_consistency(
                    df, rtf_attrs.subline_by, rtf_attrs
                )
            )
            for warning_msg in formatting_warnings:
                warnings.warn(
                    f"subline_by formatting: {warning_msg}", UserWarning, stacklevel=2
                )

        # Apply group_by and subline_by processing if specified
        processed_df, original_df = self.prepare_dataframe_for_body_encoding(
            df, rtf_attrs
        )

        # Calculate col_widths AFTER prepare_dataframe_for_body_encoding()
        # because that method may modify col_rel_width when removing columns
        # (page_by, subline_by)
        col_widths = Utils._col_widths(rtf_attrs.col_rel_width, col_total_width)

        # Check if pagination is needed (unless forced to single page)
        if not force_single_page and document_service.needs_pagination(document):
            return self._encode_body_paginated(
                document, processed_df, rtf_attrs, col_widths
            )

        # Handle existing page_by grouping (non-paginated)
        page_by = document_service.process_page_by(document)
        if page_by is None:
            # Note: subline_by documents should use pagination, so this path
            # should not be reached for them
            # Apply group_by processing for non-paginated documents
            if rtf_attrs.group_by is not None:
                processed_df = grouping_service.enhance_group_by(
                    processed_df, rtf_attrs.group_by
                )
            return rtf_attrs._encode(processed_df, col_widths)

        rows: list[str] = []
        for section in page_by:
            # Skip empty sections
            indices = [(row, col) for row, col, level in section]
            if not indices:
                continue

            # Create DataFrame for current section
            import polars as pl

            from ..attributes import BroadcastValue

            section_df = pl.DataFrame(
                {
                    str(i): [
                        BroadcastValue(value=processed_df, dimension=None).iloc(
                            row, col
                        )
                    ]
                    for i, (row, col) in enumerate(indices)
                }
            )

            # Collect all text and table attributes
            from ..input import TableAttributes

            section_attrs_dict = rtf_attrs._get_section_attributes(indices)
            section_attrs = TableAttributes(**section_attrs_dict)

            # Calculate column widths and encode section
            if section_attrs.col_rel_width is None:
                # Default to equal widths if not specified
                section_attrs.col_rel_width = [1.0] * len(indices)
            section_col_widths = Utils._col_widths(
                section_attrs.col_rel_width, col_total_width
            )
            rows.extend(section_attrs._encode(section_df, section_col_widths))

        return rows

    def _encode_body_paginated(
        self, document, df, rtf_attrs, col_widths
    ) -> Sequence[str]:
        """Encode body content with pagination support."""
        from .document_service import RTFDocumentService

        document_service = RTFDocumentService()
        _, distributor = document_service.create_pagination_instance(document)

        # Distribute content across pages (r2rtf compatible)
        additional_rows = document_service.calculate_additional_rows_per_page(document)
        pages = distributor.distribute_content(
            df=df,
            col_widths=col_widths,
            table_attrs=rtf_attrs,
            additional_rows_per_page=additional_rows,
        )

        # Generate RTF for each page
        all_rows = []
        for page_num, page_content in enumerate(pages, 1):
            page_rows = []

            # Add page header content
            if page_content.get("headers"):
                for header_content in page_content["headers"]:
                    header_text = header_content.get("text", "")
                    if header_text:
                        page_rows.append(header_text)

            # Add table data
            page_data = page_content.get("data")
            if page_data is not None:
                # Check if it's a DataFrame or a list
                if hasattr(page_data, "is_empty"):
                    # It's a DataFrame
                    if not page_data.is_empty():
                        page_rows.extend(page_data)
                else:
                    # It's a list or other iterable
                    if page_data:
                        page_rows.extend(page_data)

            # Add footer content
            if page_content.get("footers"):
                for footer_content in page_content["footers"]:
                    footer_text = footer_content.get("text", "")
                    if footer_text:
                        page_rows.append(footer_text)

            # Add page break between pages (except last page)
            if page_num < len(pages):
                page_rows.append(document_service.generate_page_break(document))

            all_rows.extend(page_rows)

        return all_rows

    def encode_column_header(
        self, df, rtf_attrs, page_col_width: float
    ) -> Sequence[str] | None:
        """Encode column header component with column width support.

        Args:
            df: DataFrame containing header data
            rtf_attrs: RTFColumnHeader attributes
            page_col_width: Page column width for calculations

        Returns:
            List of RTF header strings
        """
        if rtf_attrs is None:
            return None

        dim = df.shape

        rtf_attrs.col_rel_width = rtf_attrs.col_rel_width or [1] * dim[1]
        rtf_attrs = rtf_attrs._set_default()

        from ..row import Utils

        col_widths = Utils._col_widths(rtf_attrs.col_rel_width, page_col_width)

        return rtf_attrs._encode(df, col_widths)

    def encode_page_break(self, page_config, page_margin_encode_func) -> str:
        """Generate proper RTF page break sequence matching r2rtf format.

        Args:
            page_config: RTFPage configuration
            page_margin_encode_func: Function to encode page margins

        Returns:
            RTF page break string
        """
        from ..core import RTFConstants

        page_setup = (
            f"\\paperw{int(page_config.width * RTFConstants.TWIPS_PER_INCH)}"
            f"\\paperh{int(page_config.height * RTFConstants.TWIPS_PER_INCH)}\n\n"
            f"{page_margin_encode_func()}\n"
        )

        return f"{{\\pard\\fs2\\par}}\\page{{\\pard\\fs2\\par}}\n{page_setup}"

    def encode_page_margin(self, page_config) -> str:
        """Define RTF margin settings.

        Args:
            page_config: RTFPage configuration with margin settings

        Returns:
            RTF margin settings string
        """
        from ..row import Utils

        margin_codes = [
            "\\margl",
            "\\margr",
            "\\margt",
            "\\margb",
            "\\headery",
            "\\footery",
        ]
        margins = [Utils._inch_to_twip(m) for m in page_config.margin]
        margin = "".join(
            f"{code}{margin}"
            for code, margin in zip(margin_codes, margins, strict=True)
        )
        return margin + "\n"
