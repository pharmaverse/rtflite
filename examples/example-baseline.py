from importlib.resources import files

import polars as pl
import rtflite as rtf

pl.Config.set_tbl_rows(200)

data_path = files("rtflite.data").joinpath("baseline.csv")
df = pl.read_csv(data_path)
print(df)


header1 = pl.DataFrame(
    [["", "Placebo", "Drug Low Dose", "Drug High Dose", "Total"]], orient="row"
)
header2 = pl.DataFrame(
    [["", "n", "(%)", "n", "(%)", "n", "(%)", "n", "(%)"]], orient="row"
)

doc = rtf.RTFDocument(
    df=df,
    rtf_title=rtf.RTFTitle(
        text=["Demographic and Anthropometric Characteristics", "ITT Subjects"]
    ),
    rtf_column_header=[
        rtf.RTFColumnHeader(df=header1, col_rel_width=[3] + [2] * 4),
        rtf.RTFColumnHeader(
            df=header2,
            col_rel_width=[3] + [1.2, 0.8] * 4,
            border_top=[""] + ["single"] * 8,
            border_left=["single"] + ["single", ""] * 4,
        ),
    ],
    rtf_body=rtf.RTFBody(
        page_by=["var_label"],
        col_rel_width=[3] + [1.2, 0.8] * 4 + [3],
        text_justification=["l"] + ["c"] * 8 + ["l"],
        text_format=[""] * 9 + ["b"],
        border_left=["single"] + ["single", ""] * 4 + ["single"],
        border_top=[""] * 9 + ["single"],
        border_bottom=[""] * 9 + ["single"],
    ),
)

doc.write_rtf("output.rtf")

try:
    converter = rtf.LibreOfficeConverter()
    converter.convert(
        input_files="output.rtf", output_dir=".", format="pdf", overwrite=True
    )
except:
    print("No Libreoffice")
