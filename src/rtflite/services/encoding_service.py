"""RTF encoding service that handles document component encoding."""

from collections.abc import Sequence


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
        col_idx: int = 0,
    ) -> Sequence[str]:
        """Generate a spanning table row (single cell spanning full width).

        This is used for page_by group headers that span across all columns.
        Works for both single-page and paginated documents.

        Args:
            text: Text to display in the spanning row
            page_width: Total page width in inches
            rtf_body_attrs: RTFBody attributes for styling (optional)
            col_idx: Column index to inherit attributes from (default: 0)

        Returns:
            List of RTF strings for the spanning row
        """
        from ..attributes import BroadcastValue
        from ..row import Border, Cell, Row, TextContent

        def get_attr(attr_name, default_val):
            if rtf_body_attrs is None:
                return default_val
            val = getattr(rtf_body_attrs, attr_name, None)
            if val is None:
                return default_val
            # Use BroadcastValue to resolve the attribute for the specific column
            # We use row 0 as the reference for column-based attributes
            return BroadcastValue(value=val, dimension=None).iloc(0, col_idx)

        # Extract attributes using the helper
        font = get_attr("text_font", 0)
        size = get_attr("text_font_size", 18)
        text_format = get_attr("text_format", "")
        color = get_attr("text_color", "")
        bg_color = get_attr("text_background_color", "")
        justification = get_attr("text_justification", "c")

        indent_first = get_attr("text_indent_first", 0)
        indent_left = get_attr("text_indent_left", 0)
        indent_right = get_attr("text_indent_right", 0)
        space = get_attr("text_space", 1)
        space_before = get_attr("text_space_before", 15)
        space_after = get_attr("text_space_after", 15)
        convert = get_attr("text_convert", False)
        hyphenation = get_attr("text_hyphenation", True)

        border_left = get_attr("border_left", "single")
        border_right = get_attr("border_right", "single")
        border_top = get_attr("border_top", "single")
        border_bottom = get_attr("border_bottom", "single")

        v_just = get_attr("cell_vertical_justification", "bottom")
        cell_just = get_attr("cell_justification", "c")
        cell_height = get_attr("cell_height", 0.15)

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
                indent_first=indent_first,
                indent_left=indent_left,
                indent_right=indent_right,
                space=space,
                space_before=space_before,
                space_after=space_after,
                convert=convert,
                hyphenation=hyphenation,
            ),
            width=page_width,
            border_left=Border(style=border_left),
            border_right=Border(style=border_right),
            border_top=Border(style=border_top),
            border_bottom=Border(style=border_bottom),
            vertical_justification=v_just,
        )

        # Create row with single spanning cell
        row = Row(row_cells=[cell], justification=cell_just, height=cell_height)

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
        border_style: str | None = None,
    ) -> Sequence[str]:
        """Encode footnote component with advanced formatting.

        Args:
            footnote_config: RTFFootnote configuration
            page_number: Page number for footnote
            page_col_width: Page column width for calculations
            border_style: Optional border style to override defaults

        Returns:
            List of RTF footnote strings
        """
        if footnote_config is None:
            return []

        rtf_attrs = footnote_config

        # Apply explicitly passed border style
        if border_style:
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
        border_style: str | None = None,
    ) -> Sequence[str]:
        """Encode source component with advanced formatting.

        Args:
            source_config: RTFSource configuration
            page_number: Page number for source
            page_col_width: Page column width for calculations
            border_style: Optional border style to override defaults

        Returns:
            List of RTF source strings
        """
        if source_config is None:
            return []

        rtf_attrs = source_config

        # Apply explicitly passed border style
        if border_style:
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
        # The new_page flag only controls whether to force page breaks
        # at group boundaries
        if rtf_attrs.page_by is not None:
            # Restore previous behavior:
            # - If new_page=True: Respect pageby_row (default 'column' -> keep column)
            # - If new_page=False: Always remove columns (legacy behavior
            #   implies spanning rows)
            if rtf_attrs.new_page:
                pageby_row = getattr(rtf_attrs, "pageby_row", "column")
                if pageby_row != "column":
                    columns_to_remove.update(rtf_attrs.page_by)
            else:
                columns_to_remove.update(rtf_attrs.page_by)

        # Apply column removal if any columns need to be removed
        if columns_to_remove:
            remaining_columns = [
                col for col in processed_df.columns if col not in columns_to_remove
            ]
            processed_df = processed_df.select(remaining_columns)

            # Create a copy of attributes to modify
            processed_attrs = rtf_attrs.model_copy(deep=True)

            # Handle attribute slicing for removed columns
            # We need to slice list-based attributes to match the new column structure
            from ..attributes import BroadcastValue

            # Add footer content
            # For now, we assume standard document footers are handled outside.
            # But typically footers are page footers handled by RTFPageFooter.
            # Get indices of removed columns in the original dataframe
            removed_indices = [
                original_df.columns.index(col) for col in columns_to_remove
            ]
            removed_indices.sort(reverse=True)  # Sort reverse to remove safely

            rows, cols = original_df.shape

            # attributes to slice
            # We iterate over all fields that could be list-based
            for attr_name in type(processed_attrs).model_fields:
                if attr_name == "col_rel_width":
                    continue  # Handled separately below

                val = getattr(processed_attrs, attr_name)
                if val is None:
                    continue

                # Check if it's a list/sequence that needs slicing
                # We use BroadcastValue to expand it to full grid, then slice
                if isinstance(val, (list, tuple)):
                    # Expand to full grid
                    expanded = BroadcastValue(
                        value=val, dimension=(rows, cols)
                    ).to_list()

                    # Slice each row
                    sliced_expanded = []
                    if expanded:
                        for row_data in expanded:
                            # Remove items at specified indices
                            new_row = [
                                item
                                for i, item in enumerate(row_data)
                                if i not in removed_indices
                            ]
                            sliced_expanded.append(new_row)

                    # Update attribute
                    setattr(processed_attrs, attr_name, sliced_expanded)

            # Update col_rel_width separately (it's 1D usually)
            if processed_attrs.col_rel_width is not None:
                # Expand if needed (though usually 1D)
                current_widths = processed_attrs.col_rel_width
                # If it matches original columns, slice it
                if len(current_widths) == cols:
                    new_widths = [
                        w
                        for i, w in enumerate(current_widths)
                        if i not in removed_indices
                    ]
                    processed_attrs.col_rel_width = new_widths
        else:
            processed_attrs = rtf_attrs

        # Note: group_by suppression is handled in the pagination strategy
        # for documents that need pagination. For non-paginated documents,
        # group_by is handled separately in encode_body method.

        return processed_df, original_df, processed_attrs

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

        # Convert text list to DataFrame for encoding if needed
        import polars as pl

        df_to_encode = df
        if isinstance(df, (list, tuple)):
            # Create DataFrame from list
            schema = [f"col_{i + 1}" for i in range(len(df))]
            df_to_encode = pl.DataFrame([df], schema=schema, orient="row")
        elif df is None and rtf_attrs.text:
            # Fallback to rtf_attrs.text if df is None
            text = rtf_attrs.text
            if isinstance(text, (list, tuple)):
                schema = [f"col_{i + 1}" for i in range(len(text))]
                df_to_encode = pl.DataFrame([text], schema=schema, orient="row")

        if df_to_encode is None:
            return None

        dim = df_to_encode.shape

        rtf_attrs.col_rel_width = rtf_attrs.col_rel_width or [1] * dim[1]
        rtf_attrs = rtf_attrs._set_default()

        from ..row import Utils

        col_widths = Utils._col_widths(rtf_attrs.col_rel_width, page_col_width)

        return rtf_attrs._encode(df_to_encode, col_widths)

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
