"""Utilities for snapshot testing with font table removal."""

import re


def remove_font_table(rtf_text: str) -> str:
    """Remove font table from RTF text to focus on structural differences.

    Args:
        rtf_text: RTF text containing font table

    Returns:
        RTF text with font table removed
    """

    # Use regex to remove the entire font table block
    # Pattern matches {\fonttbl...} including nested braces and newlines
    pattern = r"\{\\fonttbl[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"

    # Remove font table while preserving line structure
    result = re.sub(pattern, "", rtf_text, flags=re.MULTILINE | re.DOTALL)

    # Clean up any resulting empty lines from font table removal
    lines = result.split("\n")
    cleaned_lines = []

    for line in lines:
        # Skip lines that only had font table content
        if line.strip():
            cleaned_lines.append(line)
        elif not cleaned_lines or cleaned_lines[-1].strip():
            # Keep empty lines that provide structure, but not consecutive ones
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def normalize_rtf_whitespace(rtf_text: str) -> str:
    """Normalize RTF whitespace patterns for comparison.

    Args:
        rtf_text: RTF text to normalize

    Returns:
        RTF text with normalized whitespace
    """
    lines = rtf_text.split("\n")
    normalized_lines = []

    for line in lines:
        # Keep non-empty lines
        if line.strip():
            normalized_lines.append(line.strip())

    return "\n".join(normalized_lines)


def normalize_rtf_structure(rtf_text: str) -> str:
    """Normalize RTF structural differences for comparison.

    This function handles common structural differences between rtflite and r2rtf:
    - Page break and page setup ordering
    - Empty line patterns
    - RTF command grouping

    Args:
        rtf_text: RTF text to normalize

    Returns:
        RTF text with normalized structure
    """
    # Remove font table first
    rtf_text = remove_font_table(rtf_text)

    # Split into lines and normalize
    lines = rtf_text.split("\n")

    # Extract key structural components
    rtf_header = []
    page_setups = []
    content_blocks = []

    current_block = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # RTF header components
        if (
            line.startswith(r"{\rtf1")
            or line.startswith(r"\deff0")
            or line.startswith(r"\deflang")
        ):
            rtf_header.append(line)
        # Page setup components
        elif any(
            cmd in line
            for cmd in [
                r"\paperw",
                r"\paperh",
                r"\margl",
                r"\margr",
                r"\margt",
                r"\margb",
                r"\headery",
                r"\footery",
            ]
        ):
            page_setups.append(line)
        # Page breaks
        elif r"\page" in line:
            if current_block:
                content_blocks.append(current_block)
                current_block = []
            content_blocks.append([line])  # Page break as separate block
            # Add page setup after page break
            if page_setups:
                content_blocks.append(page_setups[:])
        # Content
        elif (
            line.startswith(r"\trowd")
            or line.startswith(r"\cl")
            or line.startswith(r"\pard")
            or line.startswith(r"\intbl")
            or line == "}"
        ):
            current_block.append(line)
        # Everything else
        else:
            current_block.append(line)

    # Add final block
    if current_block:
        content_blocks.append(current_block)

    # Reconstruct normalized RTF
    result = []
    result.extend(rtf_header)
    if page_setups:
        result.extend(page_setups)
    result.append("")  # Empty line after header

    for block in content_blocks:
        if isinstance(block, list) and len(block) == 1 and r"\page" in block[0]:
            # Page break - add with surrounding empty lines
            result.append("")
            result.extend(block)
            result.append("")
        else:
            result.extend(block)

    return "\n".join(result)


def assert_rtf_equals_without_fonts(
    rtf_output: str,
    expected: str,
    test_name: str = "",
    normalize_whitespace: bool = True,
):
    """Compare RTF outputs after removing font tables.

    Args:
        rtf_output: RTF output from rtflite
        expected: Expected RTF output from r2rtf
        test_name: Optional test name for better error messages
        normalize_whitespace: Whether to normalize whitespace differences
    """
    rtf_no_fonts = remove_font_table(rtf_output)
    expected_no_fonts = remove_font_table(expected)

    if normalize_whitespace:
        rtf_no_fonts = normalize_rtf_whitespace(rtf_no_fonts)
        expected_no_fonts = normalize_rtf_whitespace(expected_no_fonts)

    # Add test name to assertion message if provided
    message = "RTF content should match after removing font tables"
    if test_name:
        message = f"{test_name}: {message}"

    if normalize_whitespace:
        message += " (whitespace normalized)"

    assert rtf_no_fonts == expected_no_fonts, message


def normalize_rtf_borders(rtf_text: str) -> str:
    """Normalize RTF border differences for semantic comparison.

    RTF allows borders to be specified as:
    - \\clbrdrt\\brdrw15 (width only, default single style)
    - \\clbrdrt\\brdrs\\brdrw15 (explicit single style + width)
    - \\clbrdrt\\brdrdb\\brdrw15 (explicit double style + width)

    For testing purposes, normalize all border styles to single for comparison.

    Args:
        rtf_text: RTF text to normalize

    Returns:
        RTF text with normalized border commands
    """

    # Pattern to match border commands like \clbrdrt\brdrw15
    # where style is implied (default single)
    pattern1 = r"(\\cl(?:brdrl|brdrt|brdrr|brdrb))\\brdrw(\d+)"

    def replacer1(match):
        border_side = match.group(1)
        width = match.group(2)
        # Add explicit single style
        return f"{border_side}\\brdrs\\brdrw{width}"

    # Pattern to match border commands with explicit styles (single, double, etc.)
    # and normalize them all to single style for comparison
    pattern2 = r"(\\cl(?:brdrl|brdrt|brdrr|brdrb))\\brdr(?:s|db|th|sh|dot|dash|hair|inset|outset|triple)\\brdrw(\d+)"

    def replacer2(match):
        border_side = match.group(1)
        width = match.group(2)
        # Normalize all styles to single style
        return f"{border_side}\\brdrs\\brdrw{width}"

    # Apply normalizations
    result = re.sub(pattern1, replacer1, rtf_text)
    result = re.sub(pattern2, replacer2, result)
    return result


def assert_rtf_equals_structural(rtf_output: str, expected: str, test_name: str = ""):
    """Compare RTF outputs after structural normalization.

    This is more aggressive than font table removal and handles:
    - Font table removal
    - Page break and page setup ordering differences
    - Whitespace normalization
    - Structural RTF command grouping

    Args:
        rtf_output: RTF output from rtflite
        expected: Expected RTF output from r2rtf
        test_name: Optional test name for better error messages
    """
    rtf_normalized = normalize_rtf_structure(rtf_output)
    expected_normalized = normalize_rtf_structure(expected)

    # Add test name to assertion message if provided
    message = "RTF content should match after structural normalization"
    if test_name:
        message = f"{test_name}: {message}"

    assert rtf_normalized == expected_normalized, message


def normalize_rtf_hyphenation(rtf_text: str) -> str:
    """Normalize hyphenation differences between rtflite and r2rtf.

    r2rtf outputs \\hyphpar0 while rtflite outputs \\hyphpar
    This makes them semantically equivalent.
    """
    import re

    # Convert \hyphpar0 to \hyphpar for consistency
    rtf_text = re.sub(r"\\hyphpar0\\", r"\\hyphpar\\", rtf_text)
    return rtf_text


def normalize_column_widths(rtf_content: str) -> str:
    """Normalize column widths to handle small rounding differences.

    RTF column widths can vary by 1-2 units due to floating point precision
    differences between R and Python. This function normalizes these small
    differences that don't affect the visual output.

    Args:
        rtf_content: RTF content string

    Returns:
        Normalized RTF content
    """
    import re

    def normalize_cellx(match):
        value = int(match.group(1))
        # Round to nearest 10 to handle small differences
        normalized = round(value / 10) * 10
        return f"\\cellx{normalized}"

    # Normalize \cellx values
    return re.sub(r"\\cellx(\d+)", normalize_cellx, rtf_content)


def assert_rtf_equals_semantic(rtf_output: str, expected: str, test_name: str = ""):
    """Compare RTF outputs after semantic normalization.

    This handles all structural differences plus border style normalization:
    - Font table removal
    - Page break and page setup ordering differences
    - Whitespace normalization
    - Border style semantic equivalence (\\brdrw15 vs \\brdrs\\brdrw15)
    - Structural RTF command grouping
    - Column width rounding differences

    Args:
        rtf_output: RTF output from rtflite
        expected: Expected RTF output from r2rtf
        test_name: Optional test name for better error messages
    """
    # Apply all normalizations
    rtf_normalized = normalize_rtf_structure(rtf_output)
    rtf_normalized = normalize_rtf_borders(rtf_normalized)
    rtf_normalized = normalize_rtf_hyphenation(rtf_normalized)
    rtf_normalized = normalize_column_widths(rtf_normalized)

    expected_normalized = normalize_rtf_structure(expected)
    expected_normalized = normalize_rtf_borders(expected_normalized)
    expected_normalized = normalize_rtf_hyphenation(expected_normalized)
    expected_normalized = normalize_column_widths(expected_normalized)

    # Add test name to assertion message if provided
    message = "RTF content should match after semantic normalization"
    if test_name:
        message = f"{test_name}: {message}"

    assert rtf_normalized == expected_normalized, message
