"Encoding strategies for different types of RTF documents."

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ..services.grouping_service import grouping_service
from ..type_guards import (
    is_flat_header_list,
    is_nested_header_list,
    is_single_body,
    is_single_header,
)

if TYPE_CHECKING:
    from ..encode import RTFDocument
    from ..attributes import RTFBody, RTFColumnHeader


class EncodingStrategy(ABC):
    """Abstract base class for RTF encoding strategies."""

    def __init__(self):
        from ..services import RTFEncodingService
        from ..services.document_service import RTFDocumentService
        from ..services.figure_service import RTFFigureService

        self.encoding_service = RTFEncodingService()
        self.document_service = RTFDocumentService()
        self.figure_service = RTFFigureService()

    @abstractmethod
    def encode(self, document: "RTFDocument") -> str:
        """Encode the document using this strategy.

        Args:
            document: The RTF document to encode

        Returns:
            Complete RTF string
        """
        pass

    def _render_page_content(
        self,
        document: "RTFDocument",
        page_df: Any,
        page_body_attrs: "RTFBody | list[RTFBody]",
        page_column_header: Any,
        page_title: Any,
        page_subline: Any,
        page_footnote: Any,
        page_source: Any,
        page_figure: Any,
        extra_top_elements: list[str] | None = None,
        extra_mid_elements: list[str] | None = None,
        page_number: int = 1,
        is_first_page: bool = True,
        is_last_page: bool = True,
    ) -> list[str]:
        """Render the content of a single page.

        Args:
            document: The RTF document (context)
            page_df: DataFrame or list of DataFrames for this page
            page_body_attrs: RTFBody attributes (with page-specific borders)
            page_column_header: Column headers for this page
            page_title: Title object (or None if suppressed)
            page_subline: Subline object (or None if suppressed)
            page_footnote: Footnote object (or None if suppressed)
            page_source: Source object (or None if suppressed)
            page_figure: Figure object (or None if suppressed)
            extra_top_elements: Pre-rendered elements to add before figure/headers
            extra_mid_elements: Pre-rendered elements to add between headers and body
            page_number: Current page number
            is_first_page: Whether this is the first page
            is_last_page: Whether this is the last page

        Returns:
            List of RTF strings
        """
        elements = []

        # 1. Title
        if page_title and page_title.text:
            elements.append(
                self.encoding_service.encode_title(page_title, method="line")
            )
            elements.append("\n")

        # 2. Subline
        if page_subline and page_subline.text:
            elements.append(
                self.encoding_service.encode_subline(page_subline, method="line")
            )

        # 3. Extra Top Elements (e.g. subline_header)
        if extra_top_elements:
            elements.extend(extra_top_elements)

        # 4. Figure (Before)
        if (
            page_figure
            and page_figure.figures
            and page_figure.fig_pos == "before"
            and is_first_page
        ):
            elements.append(self.encoding_service.figure_service.encode_figure(page_figure))
            elements.append("\n")

        # 5. Column Headers
        # Auto-generate header text if missing
        current_body = (
            page_body_attrs[0]
            if isinstance(page_body_attrs, list) and page_body_attrs
            else page_body_attrs
        )
        
        headers_to_process = []
        if page_column_header:
            if is_nested_header_list(page_column_header):
                for section_headers in page_column_header:
                    if section_headers:
                        headers_to_process.extend(section_headers)
            elif is_flat_header_list(page_column_header):
                headers_to_process = page_column_header
            elif is_single_header(page_column_header):
                headers_to_process = [page_column_header]

            first_header = headers_to_process[0] if headers_to_process else None
            if (
                first_header
                and first_header.text is None
                and is_single_body(current_body)
                and current_body.as_colheader
                and page_df is not None
                and not isinstance(page_df, list)
            ):
                import polars as pl
                
                excluded_columns = list(current_body.page_by or []) + list(
                    current_body.subline_by or []
                )
                
                columns = [
                    col for col in page_df.columns if col not in excluded_columns
                ]
                header_df = pl.DataFrame(
                    [columns],
                    schema=[f"col_{i}" for i in range(len(columns))],
                    orient="row",
                )
                first_header.text = header_df

                if excluded_columns and current_body.col_rel_width:
                     if len(current_body.col_rel_width) != len(columns):
                         first_header.col_rel_width = [1] * len(columns)
                elif first_header.col_rel_width is None:
                     first_header.col_rel_width = [1] * len(columns)

        if headers_to_process:
            for header in headers_to_process:
                if header:
                    elements.extend(
                        self.encoding_service.encode_column_header(
                            header.text, header, document.rtf_page.col_width
                        )
                    )

        # 6. Extra Mid Elements (e.g. pageby spanning row)
        if extra_mid_elements:
            elements.extend(extra_mid_elements)

        # 7. Body
        if page_df is not None:
            df_list = page_df if isinstance(page_df, list) else [page_df]
            body_list = (
                page_body_attrs
                if isinstance(page_body_attrs, list)
                else [page_body_attrs]
            )
            
            if len(body_list) < len(df_list):
                body_list = body_list * (len(df_list) // len(body_list) + 1)
            body_list = body_list[:len(df_list)]

            for df, body in zip(df_list, body_list, strict=False):
                body_content = self.encoding_service.encode_body(
                    document, df, body, force_single_page=True
                )
                if body_content:
                    elements.extend(body_content)

        # 8. Footnote
        if page_footnote and page_footnote.text:
            elements.extend(
                self.encoding_service.encode_footnote(
                    page_footnote,
                    page_number=page_number,
                    page_col_width=document.rtf_page.col_width,
                )
            )

        # 9. Source
        if page_source and page_source.text:
            elements.extend(
                self.encoding_service.encode_source(
                    page_source,
                    page_number=page_number,
                    page_col_width=document.rtf_page.col_width,
                )
            )

        # 10. Figure (After)
        if (
            page_figure
            and page_figure.figures
            and page_figure.fig_pos == "after"
            and is_last_page
        ):
            elements.append(self.encoding_service.figure_service.encode_figure(page_figure))

        return elements

    def _wrap_document(self, document: "RTFDocument", content_parts: list[str]) -> str:
        """Wrap content parts in RTF document structure."""
        return "\n".join(
            [
                item
                for item in [
                    self.encoding_service.encode_document_start(),
                    self.encoding_service.encode_font_table(),
                    self.encoding_service.encode_color_table(document),
                    "\n",
                    self.encoding_service.encode_page_header(
                        document.rtf_page_header, method="line"
                    ),
                    self.encoding_service.encode_page_footer(
                        document.rtf_page_footer, method="line"
                    ),
                    self.encoding_service.encode_page_settings(document.rtf_page),
                    *content_parts,
                    "\n\n",
                    "}",
                ]
                if item is not None
            ]
        )


class SinglePageStrategy(EncodingStrategy):
    """Encoding strategy for single-page documents without pagination."""

    def encode(self, document: "RTFDocument") -> str:
        """Encode a single-page document with complete border and layout handling."""
        import polars as pl
        from ..attributes import BroadcastValue
        from copy import deepcopy
        
        if document.df is None:
            return self._encode_figure_only_document_simple(document)

        dim = (0, 0)
        if isinstance(document.df, list) and document.df:
             dim = document.df[0].shape
        elif document.df is not None:
             dim = document.df.shape

        doc_border_top_list = BroadcastValue(
            value=document.rtf_page.border_first, dimension=(1, dim[1])
        ).to_list()
        doc_border_top = doc_border_top_list[0] if doc_border_top_list else None
        doc_border_bottom_list = BroadcastValue(
            value=document.rtf_page.border_last, dimension=(1, dim[1])
        ).to_list()
        doc_border_bottom = (
            doc_border_bottom_list[0] if doc_border_bottom_list else None
        )

        page_df = document.df
        page_body_attrs = deepcopy(document.rtf_body)
        
        if isinstance(page_body_attrs, list):
             if page_body_attrs and doc_border_top:
                  b = page_body_attrs[0]
                  d = page_df[0].shape
                  b.border_top = BroadcastValue(value=b.border_top, dimension=d).update_row(0, doc_border_top)
             
             if document.rtf_footnote is None and page_body_attrs and doc_border_bottom:
                  b = page_body_attrs[-1]
                  d = page_df[-1].shape
                  if d[0] > 0:
                      b.border_bottom = BroadcastValue(value=b.border_bottom, dimension=d).update_row(d[0]-1, doc_border_bottom)
        else:
             if page_body_attrs:
                 d = page_df.shape
                 if doc_border_top:
                     page_body_attrs.border_top = BroadcastValue(value=page_body_attrs.border_top, dimension=d).update_row(0, doc_border_top)
                 
                 if document.rtf_footnote is None and doc_border_bottom and d[0] > 0:
                     page_body_attrs.border_bottom = BroadcastValue(value=page_body_attrs.border_bottom, dimension=d).update_row(d[0]-1, doc_border_bottom)

        page_column_header = deepcopy(document.rtf_column_header)
        if page_column_header and doc_border_top:
            first = None
            if is_nested_header_list(page_column_header) and page_column_header[0]:
                first = page_column_header[0][0]
            elif is_flat_header_list(page_column_header) and page_column_header:
                first = page_column_header[0]
            elif is_single_header(page_column_header):
                first = page_column_header
            
            if first:
                 h_dim = (1, dim[1])
                 if first.text is not None:
                     if isinstance(first.text, pl.DataFrame): h_dim = first.text.shape
                     else: h_dim = (1, len(first.text))
                 
                 first.border_top = BroadcastValue(value=first.border_top, dimension=h_dim).update_row(0, doc_border_top)

        page_footnote = deepcopy(document.rtf_footnote)
        if page_footnote and doc_border_bottom:
             page_footnote.border_bottom = BroadcastValue(value=page_footnote.border_bottom, dimension=(1,1)).update_row(0, [doc_border_bottom[0]])

        from ..services.color_service import color_service
        color_service.set_document_context(document)

        content_parts = self._render_page_content(
            document=document,
            page_df=page_df,
            page_body_attrs=page_body_attrs,
            page_column_header=page_column_header,
            page_title=document.rtf_title,
            page_subline=document.rtf_subline,
            page_footnote=page_footnote,
            page_source=document.rtf_source,
            page_figure=document.rtf_figure,
            page_number=1,
            is_first_page=True,
            is_last_page=True
        )
        
        result = self._wrap_document(document, content_parts)
        color_service.clear_document_context()
        return result

    def _encode_figure_only_document_simple(self, document: "RTFDocument") -> str:
        """Encode a figure-only document with simple page layout."""
        rtf_title = self.encoding_service.encode_title(
            document.rtf_title, method="line"
        )
        
        elements = []
        if rtf_title: elements.extend([rtf_title, "\n"])
        if document.rtf_subline: 
             elements.append(self.encoding_service.encode_subline(document.rtf_subline, method="line"))
        
        if document.rtf_figure:
             elements.append(self.figure_service.encode_figure(document.rtf_figure))
             
        if document.rtf_footnote:
             elements.extend(self.encoding_service.encode_footnote(document.rtf_footnote, page_number=1, page_col_width=document.rtf_page.col_width))
             
        if document.rtf_source:
             elements.extend(self.encoding_service.encode_source(document.rtf_source, page_number=1, page_col_width=document.rtf_page.col_width))
             
        return self._wrap_document(document, elements)


class PaginatedStrategy(EncodingStrategy):
    """Encoding strategy for multi-page documents with pagination."""

    def encode(self, document: "RTFDocument") -> str:
        """Encode a paginated document using the shared render engine."""
        from copy import deepcopy
        import polars as pl
        from ..row import Utils
        from ..attributes import BroadcastValue

        if document.df is None:
            return self._encode_figure_only_document_with_pagination(document)

        from ..services.color_service import color_service
        color_service.set_document_context(document)

        processed_df, original_df = (
            self.encoding_service.prepare_dataframe_for_body_encoding(
                document.df, document.rtf_body
            )
        )
        
        if is_single_body(document.rtf_body) and document.rtf_body.subline_by is not None:
            import warnings
            from typing import cast
            subline_by_list = cast(list[str], document.rtf_body.subline_by)
            formatting_warnings = (
                grouping_service.validate_subline_formatting_consistency(
                    original_df, subline_by_list, document.rtf_body
                )
            )
            for warning_msg in formatting_warnings:
                warnings.warn(f"subline_by formatting: {warning_msg}", UserWarning, stacklevel=3)

        _, distributor = self.document_service.create_pagination_instance(document)
        col_total_width = document.rtf_page.col_width
        
        if isinstance(document.df, list):
            dim = (sum(d.shape[0] for d in document.df), document.df[0].shape[1])
        else:
            dim = document.df.shape

        if is_single_body(document.rtf_body) and document.rtf_body.col_rel_width is not None:
            col_widths = Utils._col_widths(document.rtf_body.col_rel_width, col_total_width if col_total_width else 8.5)
        else:
            col_widths = Utils._col_widths([1] * dim[1], col_total_width if col_total_width else 8.5)

        additional_rows = self.document_service.calculate_additional_rows_per_page(document)
        
        pages = distributor.distribute_content(
            df=original_df,
            col_widths=col_widths,
            page_by=document.rtf_body.page_by if is_single_body(document.rtf_body) else None,
            new_page=document.rtf_body.new_page if is_single_body(document.rtf_body) else None,
            pageby_header=document.rtf_body.pageby_header if is_single_body(document.rtf_body) else None,
            table_attrs=document.rtf_body if is_single_body(document.rtf_body) else None,
            additional_rows_per_page=additional_rows,
            subline_by=document.rtf_body.subline_by if is_single_body(document.rtf_body) else None,
        )

        for page_info in pages:
            start_row = page_info["start_row"]
            end_row = page_info["end_row"]
            page_info["data"] = processed_df.slice(start_row, end_row - start_row + 1)
            
        if is_single_body(document.rtf_body) and document.rtf_body.group_by:
            page_start_indices = []
            cumulative_rows = 0
            for i, page_info in enumerate(pages):
                if i > 0: page_start_indices.append(cumulative_rows)
                cumulative_rows += len(page_info["data"])

            all_page_data = [p["data"] for p in pages]
            full_df = all_page_data[0]
            for page_df in all_page_data[1:]: full_df = full_df.vstack(page_df)

            from typing import cast
            group_by_param = cast(list[str] | None, document.rtf_body.group_by)
            suppressed_df = grouping_service.enhance_group_by(full_df, group_by_param)
            
            restored_df = grouping_service.restore_page_context(
                suppressed_df, full_df, group_by_param, page_start_indices
            )
            
            start_idx = 0
            for page_info in pages:
                page_rows = len(page_info["data"])
                page_info["data"] = restored_df.slice(start_idx, page_rows)
                start_idx += page_rows

        all_content_parts = []
        
        for i, page_info in enumerate(pages):
            is_first = page_info["is_first_page"]
            is_last = page_info["is_last_page"]
            page_num = page_info["page_number"]
            
            if not is_first:
                all_content_parts.append(self.document_service.generate_page_break(document))
                
            show_title = document.rtf_title and self.document_service.should_show_element_on_page(document.rtf_page.page_title, page_info)
            show_subline = document.rtf_subline and self.document_service.should_show_element_on_page(document.rtf_page.page_title, page_info)
            show_footnote = document.rtf_footnote and self.document_service.should_show_element_on_page(document.rtf_page.page_footnote, page_info)
            show_source = document.rtf_source and self.document_service.should_show_element_on_page(document.rtf_page.page_source, page_info)
            
            page_body_attrs = self.document_service.apply_pagination_borders(
                document, document.rtf_body, page_info, len(pages)
            )

            # Clear attributes handled by pagination strategy
            if is_single_body(page_body_attrs):
                if page_body_attrs.new_page and page_body_attrs.page_by:
                    page_body_attrs.page_by = None
                    page_body_attrs.new_page = False
                if page_body_attrs.subline_by:
                    page_body_attrs.subline_by = None
            
            page_column_header = deepcopy(document.rtf_column_header)
            if page_info["needs_header"] and page_column_header:
                 if is_first and document.rtf_page.border_first:
                     first = None
                     if is_nested_header_list(page_column_header) and page_column_header[0]: first = page_column_header[0][0]
                     elif is_flat_header_list(page_column_header) and page_column_header: first = page_column_header[0]
                     elif is_single_header(page_column_header): first = page_column_header
                     
                     if first and first.text is not None:
                          first.border_top = BroadcastValue(value=first.border_top, dimension=(1, dim[1])).update_row(0, [document.rtf_page.border_first]*dim[1])
            elif not page_info["needs_header"]:
                page_column_header = None

            extra_top = []
            if page_info.get("subline_header"):
                 txt = self._generate_subline_header(page_info["subline_header"], document.rtf_body)
                 if txt: extra_top.append(txt)
            
            extra_mid = []
            if page_info.get("pageby_header_info"):
                 header_info = page_info["pageby_header_info"]
                 if "group_values" in header_info:
                      parts = [str(v) for v in header_info["group_values"].values() if v is not None]
                      if parts:
                           row_content = self.encoding_service.encode_spanning_row(
                               ", ".join(parts), 
                               document.rtf_page.col_width if document.rtf_page.col_width else 8.5,
                               document.rtf_body
                           )
                           extra_mid.extend(row_content)

            page_parts = self._render_page_content(
                document=document,
                page_df=page_info["data"],
                page_body_attrs=page_body_attrs,
                page_column_header=page_column_header,
                page_title=document.rtf_title if show_title else None,
                page_subline=document.rtf_subline if show_subline else None,
                page_footnote=document.rtf_footnote if show_footnote else None,
                page_source=document.rtf_source if show_source else None,
                page_figure=document.rtf_figure,
                extra_top_elements=extra_top,
                extra_mid_elements=extra_mid,
                page_number=page_num,
                is_first_page=is_first,
                is_last_page=is_last
            )
            
            all_content_parts.extend(page_parts)
            
        result = self._wrap_document(document, all_content_parts)
        color_service.clear_document_context()
        return result

    def _encode_figure_only_document_with_pagination(self, document: "RTFDocument") -> str:
        from copy import deepcopy
        from ..figure import rtf_read_figure

        if document.rtf_figure is None or document.rtf_figure.figures is None:
            return ""

        figure_data_list, figure_formats = rtf_read_figure(document.rtf_figure.figures)
        num_figures = len(figure_data_list)

        rtf_title = self.encoding_service.encode_title(
            document.rtf_title, method="line"
        )

        footnote_component = document.rtf_footnote
        if footnote_component is not None:
            footnote_component = deepcopy(footnote_component)
            footnote_component.as_table = False

        show_title_on_all = document.rtf_page.page_title == "all"
        show_footnote_on_all = document.rtf_page.page_footnote == "all"
        show_source_on_all = document.rtf_page.page_source == "all"

        inner_elements = []
        
        for i in range(num_figures):
            is_first_page = i == 0
            is_last_page = i == num_figures - 1

            if (
                show_title_on_all
                or (document.rtf_page.page_title == "first" and is_first_page)
                or (document.rtf_page.page_title == "last" and is_last_page)
            ):
                inner_elements.append(rtf_title)
                inner_elements.append("\n")

            if is_first_page:
                inner_elements.append(
                    self.encoding_service.encode_subline(
                        document.rtf_subline, method="line"
                    )
                )

            width = self.figure_service._get_dimension(document.rtf_figure.fig_width, i)
            height = self.figure_service._get_dimension(
                document.rtf_figure.fig_height, i
            )

            figure_rtf = self.figure_service._encode_single_figure(
                figure_data_list[i],
                figure_formats[i],
                width,
                height,
                document.rtf_figure.fig_align,
            )
            inner_elements.append(figure_rtf)
            inner_elements.append("\\par ")

            if footnote_component is not None and (
                show_footnote_on_all
                or (document.rtf_page.page_footnote == "first" and is_first_page)
                or (document.rtf_page.page_footnote == "last" and is_last_page)
            ):
                footnote_content = "\n".join(
                    self.encoding_service.encode_footnote(
                        footnote_component,
                        page_number=i + 1,
                        page_col_width=document.rtf_page.col_width,
                    )
                )
                if footnote_content:
                    inner_elements.append(footnote_content)

            if document.rtf_source is not None and (
                show_source_on_all
                or (document.rtf_page.page_source == "first" and is_first_page)
                or (document.rtf_page.page_source == "last" and is_last_page)
            ):
                source_content = "\n".join(
                    self.encoding_service.encode_source(
                        document.rtf_source,
                        page_number=i + 1,
                        page_col_width=document.rtf_page.col_width,
                    )
                )
                if source_content:
                    inner_elements.append(source_content)

            if not is_last_page:
                inner_elements.append("\\page ")

        return self._wrap_document(document, inner_elements)

    def _generate_subline_header(self, subline_header_info: dict, rtf_body) -> str:
        """Generate RTF paragraph for subline_by header."""
        if not subline_header_info:
            return ""

        if "group_values" in subline_header_info:
            header_parts = []
            for _col, value in subline_header_info["group_values"].items():
                if value is not None:
                    header_parts.append(str(value))
            if not header_parts:
                return ""
            header_text = ", ".join(header_parts)
        else:
            header_parts = []
            for col, value in subline_header_info.items():
                if value is not None and col not in ["group_by_columns", "header_text"]:
                    header_parts.append(str(value))
            if not header_parts:
                return ""
            header_text = ", ".join(header_parts)

        return (
            f"{{\\pard\\hyphpar\\fi0\\li0\\ri0\\ql\\fs18{{\\f0 {header_text}}}\\par}}"
        )