import polars as pl
import rtflite as rtf

border_demo = [
    ["Single", "Standard line"],
    ["Double", "Double line"],
    ["Thick", "Thick line"],
    ["None", "No border"],
]

df_borders = pl.DataFrame(border_demo, schema=["type", "description"])

doc_borders = rtf.RTFDocument(
    df=df_borders,
    rtf_body=rtf.RTFBody(
        border_bottom=("single", "double", "thick", ""),
    ),
)

doc_borders.write_rtf("../rtf/row_border_styles.rtf")

width_demo = [
    ["Narrow", "Standard Width", "Wide Column"],
    ["1.0", "2.0", "3.0"],
    ["Small", "Medium text content", "Much wider column for longer text"],
]

df_widths = pl.DataFrame(width_demo, schema=["narrow", "standard", "wide"])

doc_widths = rtf.RTFDocument(
    df=df_widths,
    rtf_body=rtf.RTFBody(
        col_rel_width=(1.0, 2.0, 3.0),  # Relative width ratios
    ),
)

doc_widths.write_rtf("../rtf/row_column_widths.rtf")
