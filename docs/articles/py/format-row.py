import polars as pl

import rtflite as rtf

border_data = [
    [border_type, f"Example of {border_type or 'no'} border"]
    for border_type in rtf.attributes.BORDER_CODES.keys()
]

df_borders = pl.DataFrame(
    border_data, schema=["border_type", "description"], orient="row"
)

doc_borders = rtf.RTFDocument(
    df=df_borders,
    rtf_body=rtf.RTFBody(
        border_bottom=tuple(rtf.attributes.BORDER_CODES.keys()),
    ),
)

doc_borders.write_rtf("../rtf/row-border-styles.rtf")

width_demo = [
    ["Narrow", "Standard Width", "Wide Column"],
    ["1.0", "2.0", "3.0"],
    ["Small", "Medium text content", "Much wider column for longer text"],
]

df_widths = pl.DataFrame(width_demo, schema=["narrow", "standard", "wide"])

doc_widths = rtf.RTFDocument(
    df=df_widths,
    rtf_body=rtf.RTFBody(
        col_rel_width=[1.0, 2.0, 3.0],  # Relative width ratios
    ),
)

doc_widths.write_rtf("../rtf/row-column-widths.rtf")
